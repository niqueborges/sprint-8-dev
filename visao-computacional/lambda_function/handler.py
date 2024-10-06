import json
import os
import boto3
from datetime import datetime
from dotenv import load_dotenv  # Importa para carregar variáveis de ambiente
import traceback

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente AWS Rekognition
rekognition = boto3.client('rekognition', region_name='us-east-1')  

# Função para verificar as variáveis de ambiente
def check_env_vars():
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Função de verificação de saúde do serviço
def health(event, context):
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

# Descrição da API versão 1
def v1_description(event, context):
    body = {"message": "VISION api version 1."}
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

# Descrição da API versão 2
def v2_description(event, context):
    body = {"message": "VISION api version 2."}
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

# Função para detectar emoções nas faces usando AWS Rekognition
def vision(event, context):
    try:
        # Verifica se as variáveis de ambiente necessárias estão definidas
        check_env_vars()

        # Tenta extrair e validar o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        print("Requisição recebida:", body)  # Para debug

        bucket = body.get('bucket')
        image_name = body.get('imageName')

        # Valida se os parâmetros essenciais estão presentes
        if not bucket or not image_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing 'bucket' or 'imageName' in the request body"})
            }

        # Atualiza o image_name para incluir a pasta myphotos
        image_key = f"myphotos/{image_name}"  # Adicionando a pasta "myphotos"

        # Monta a URL da imagem no S3
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

        # Chama o AWS Rekognition para detectar emoções nas faces
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': image_key}},  # Usa o caminho atualizado
            Attributes=['ALL']
        )
        print("Resposta do Rekognition:", response)  # Para debug

        faces_detected = response.get('FaceDetails', [])
        created_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Se nenhuma face for detectada
        if not faces_detected:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "url_to_image": image_url,
                    "created_image": created_time,
                    "faces": [
                        {
                            "position": {
                                "Height": None,
                                "Left": None,
                                "Top": None,
                                "Width": None
                            },
                            "classified_emotion": None,
                            "classified_emotion_confidence": None
                        }
                    ]
                })
            }

        # Processar as faces detectadas
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

        # Monta a resposta final
        response_body = {
            "url_to_image": image_url,
            "created_image": created_time,
            "faces": faces_output
        }

        # Loga o corpo da resposta no CloudWatch
        print(json.dumps(response_body))

        return {
            "statusCode": 200,
            "body": json.dumps(response_body)
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON in the request body"})
        }
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        traceback.print_exc()  # Loga o traceback completo para facilitar o debug
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error"})
        }
