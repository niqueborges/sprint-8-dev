import json
import os  # Para verificar variáveis de ambiente
import boto3
from datetime import datetime
import traceback
from dotenv import load_dotenv  # Importa para carregar variáveis de ambiente

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa os clientes AWS
rekognition = boto3.client('rekognition')
bedrock = boto3.client('bedrock')  # Inicializa o cliente Bedrock

# Função para verificar as variáveis de ambiente
def check_env_vars():
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("All necessary environment variables are set.")

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
                    "faces": [{
                        "position": {
                            "Height": None,
                            "Left": None,
                            "Top": None,
                            "Width": None
                        },
                        "classified_emotion": None,
                        "classified_emotion_confidence": None
                    }]
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
                response_bedrock = visao_computacional(detected_emotion)  # Chama a função com a emoção detectada
                print(response_bedrock)  # Aqui você pode ver a resposta do Bedrock

        # Monta a resposta com as emoções classificadas
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

def visao_computacional(detected_emotion):
    # A lógica do Bedrock para responder com base na emoção detectada
    responses = {
        "HAPPY": "The detected emotion is HAPPY. The pet seems to be very expressive!",
        "SAD": "The detected emotion is SAD. The pet might need some comfort.",
        "ANGRY": "The detected emotion is ANGRY. The pet is feeling agitated.",
        "SURPRISED": "The detected emotion is SURPRISED. The pet is intrigued by something!",
        "NEUTRAL": "The detected emotion is NEUTRAL. The pet is calm."
    }

    return responses.get(detected_emotion, "Emotion not recognized.")

