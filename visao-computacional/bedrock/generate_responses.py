import boto3
import json
from datetime import datetime
import os
from dotenv import load_dotenv  # Importa para carregar variáveis de ambiente
import traceback

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa os clientes AWS Rekognition e Bedrock
rekognition = boto3.client('rekognition', region_name='us-east-1')
bedrock = boto3.client('bedrock', region_name='us-east-1')

# Função para verificar as variáveis de ambiente
def check_env_vars():
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("All necessary environment variables are set.")

# Função principal do Lambda
def vision(event, context):
    try:
        # Verifica se as variáveis de ambiente necessárias estão definidas
        check_env_vars()

        # Tenta extrair e validar o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')

        # Valida se os parâmetros essenciais estão presentes
        if not bucket or not image_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing 'bucket' or 'imageName' in the request body"})
            }

        # Monta a URL da imagem no S3
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_name}"
        
        # Chama o Rekognition para detectar faces e emoções
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': image_name}},
            Attributes=['ALL']
        )

        faces_detected = response.get('FaceDetails', [])
        created_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Se não houver faces detectadas, retorna uma resposta apropriada
        if not faces_detected:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "url_to_image": image_url,
                    "created_image": created_time,
                    "faces": [],
                    "message": "No faces detected."
                })
            }

        # Processa as faces detectadas
        faces_output = []
        for face in faces_detected:
            emotions = face.get('Emotions', [])
            if emotions:
                primary_emotion = max(emotions, key=lambda x: x['Confidence'])
                face_data = {
                    "position": face['BoundingBox'],
                    "classified_emotion": primary_emotion['Type'],
                    "classified_emotion_confidence": primary_emotion['Confidence']
                }
                faces_output.append(face_data)

                # Integração com Bedrock
                detected_emotion = primary_emotion['Type']
                response_bedrock = visao_computacional(detected_emotion)  # Chama a função para gerar uma narrativa
                face_data["bedrock_response"] = response_bedrock  # Adiciona a resposta do Bedrock ao output

        # Monta a resposta com as emoções classificadas e narrativas geradas pelo Bedrock
        response_body = {
            "url_to_image": image_url,
            "created_image": created_time,
            "faces": faces_output
        }

        # Loga o resultado no CloudWatch
        print(json.dumps(response_body))

        return {
            "statusCode": 200,
            "body": json.dumps(response_body)
        }

    except json.JSONDecodeError:
        # Captura erro de decodificação JSON
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON format."})
        }
    except Exception as e:
        # Registrar erro com mais contexto
        print(f"Erro: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)})
        }

# Função que integra com o Bedrock para gerar narrativa baseada na emoção detectada
def visao_computacional(detected_emotion):
    try:
        # Cria um prompt dinâmico com base na emoção detectada
        prompt = f"The detected emotion is {detected_emotion}. Can you provide a brief narrative about what this emotion might represent in the context of a pet's behavior?"

        # Chama o Bedrock para gerar uma resposta com base no prompt
        response = bedrock.invoke_model(
            modelId='gpt-3.5-turbo',  # Escolha o modelo apropriado
            prompt=prompt,
            max_tokens=100  # Define o número de tokens para limitar o tamanho da resposta
        )
        generated_text = response['text']  # Extrai o texto gerado pelo Bedrock

        return generated_text

    except Exception as e:
        print(f"Erro na integração com o Bedrock: {e}")
        return "Erro ao gerar narrativa usando o Bedrock."


