import boto3
import json
from datetime import datetime
from dotenv import load_dotenv  
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Extrai os parâmetros do corpo da requisição
        body = json.loads(event['body'])
        bucket = body.get('bucket')
        image_name = body.get('imageName')

        # Verificar se bucket e image_name foram fornecidos
        if not bucket or not image_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Bucket and imageName must be provided."})
            }

        # Monta a URL da imagem no S3
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_name}"
        
        # Chama o Rekognition para detectar faces e emoções
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': image_name}},
            Attributes=['ALL']
        )

        # Verifica se há faces detectadas
        faces_detected = response.get('FaceDetails', [])
        created_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        if not faces_detected:
            # Retorno se não houver nenhuma face detectada
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

        # Processa as faces detectadas
        faces_output = []
        for face in faces_detected:
            emotions = face['Emotions']
            primary_emotion = max(emotions, key=lambda x: x['Confidence'])
            face_data = {
                "position": face['BoundingBox'],
                "classified_emotion": primary_emotion['Type'],
                "classified_emotion_confidence": primary_emotion['Confidence']
            }
            faces_output.append(face_data)

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

    except Exception as e:
        # Registrar erro
        print(f"Erro: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error"})
        }
