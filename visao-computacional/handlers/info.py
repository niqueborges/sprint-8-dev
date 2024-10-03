import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

rekognition_client = boto3.client('rekognition')

def create_response(status_code, message):
    """Cria uma resposta padrão para a API."""
    return {
        "statusCode": status_code,
        "body": json.dumps(message)
    }

def health(event, context):
    """Verifica se a função está funcionando corretamente."""
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }
    return create_response(200, body)

def v1_description(event, context):
    """Retorna a descrição da API VISION versão 1."""
    return create_response(200, {"message": "VISION API version 1."})

def v2_description(event, context):
    """Retorna a descrição da API VISION versão 2."""
    return create_response(200, {"message": "VISION API version 2."})

def vision(event, context):
    """Processa a imagem e retorna as emoções detectadas."""
    body = json.loads(event['body'])
    
    bucket = body.get("bucket")
    image_name = body.get("imageName")

    if not bucket or not image_name:
        return create_response(400, {"message": "bucket and imageName are required."})

    # Chama o Rekognition para detectar emoções
    try:
        response = rekognition_client.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': image_name
                }
            },
            Attributes=['ALL']
        )
    except ClientError as e:
        print(f"Error calling Rekognition: {e}")
        return create_response(500, {"message": "Error calling Rekognition service."})

    # Processa a resposta do Rekognition
    faces_data = []
    if 'FaceDetails' in response:
        for face in response['FaceDetails']:
            emotions = face.get('Emotions', [])
            if emotions:
                classified_emotion = max(emotions, key=lambda x: x['Confidence'])
                faces_data.append({
                    "position": face['BoundingBox'],
                    "classified_emotion": classified_emotion['Type'],
                    "classified_emotion_confidence": classified_emotion['Confidence'],
                })

    # Monta a resposta
    created_image = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    result = {
        "url_to_image": f"https://{bucket}.s3.amazonaws.com/{image_name}",
        "created_image": created_image,
        "faces": faces_data or [{
            "position": {
                "Height": None,
                "Left": None,
                "Top": None,
                "Width": None
            },
            "classified_emotion": None,
            "classified_emotion_confidence": None
        }]
    }

    print(result)  # Para registro no CloudWatch
    return create_response(200, result)
