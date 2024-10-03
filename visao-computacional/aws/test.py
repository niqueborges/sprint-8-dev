import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv 

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

rekognition_client = boto3.client('rekognition')

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': body
    }

def vision(event, context):
    bucket = event['bucket']
    image_name = event['image_name']
    
    print("Chamando Rekognition...")  # Adicione isso para verificar onde o timeout acontece
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
    
    print("Rekognition respondeu.")
    return create_response(200, response)