import boto3
import json
from datetime import datetime
from dotenv import load_dotenv  
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa os clientes AWS Rekognition e S3
rekognition = boto3.client('rekognition', region_name='us-east-1')  
s3 = boto3.client('s3')

# Função para verificar as variáveis de ambiente
def check_env_vars():
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("All necessary environment variables are set.")

# Função para detectar etiquetas (labels) usando bytes
def detectar_etiquetas(imagem_bytes):
    resposta = rekognition.detect_labels(
        Image={'Bytes': imagem_bytes},
        MaxLabels=10
    )
    return resposta['Labels']

# Função principal do Lambda
def lambda_handler(event, context):
    try:
        # Verifica se as variáveis de ambiente necessárias estão definidas
        check_env_vars()

        # Extrai os parâmetros do corpo da requisição
        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')
        image_bytes = body.get('imageBytes', None)  # Opção para passar imagem em bytes

        # Verificar se bucket e image_name ou imageBytes foram fornecidos
        if not bucket or not image_name and not image_bytes:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Bucket and imageName or imageBytes must be provided."})
            }

        # Se imagem_bytes for fornecido, usa para detectar etiquetas
        etiquetas_detectadas = []
        if image_bytes:
            etiquetas_detectadas = detectar_etiquetas(image_bytes.encode('utf-8'))  # Passa a imagem em bytes para detecção de etiquetas

        # Se bucket e image_name forem fornecidos, monta a URL da imagem no S3
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_name}" if bucket and image_name else None
        
        # Chama o Rekognition para detectar faces e emoções
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': image_name}} if bucket and image_name else {'Bytes': image_bytes},
            Attributes=['ALL']
        )

        # Verifica se há faces detectadas
        faces_detectadas = response.get('FaceDetails', [])
        created_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Se não houver faces detectadas, retorna uma resposta apropriada
        if not faces_detectadas:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "url_to_image": image_url,
                    "created_image": created_time,
                    "faces": [],
                    "etiquetas": etiquetas_detectadas if etiquetas_detectadas else "Nenhuma etiqueta detectada."
                })
            }

        # Processa as faces detectadas
        faces_output = []
        for face in faces_detectadas:
            emotions = face.get('Emotions', [])
            if emotions:
                primary_emotion = max(emotions, key=lambda x: x['Confidence'])
                face_data = {
                    "position": face['BoundingBox'],
                    "classified_emotion": primary_emotion['Type'],
                    "classified_emotion_confidence": primary_emotion['Confidence']
                }
                faces_output.append(face_data)

        # Monta a resposta com as emoções e etiquetas classificadas
        response_body = {
            "url_to_image": image_url,
            "created_image": created_time,
            "faces": faces_output,
            "etiquetas": etiquetas_detectadas if etiquetas_detectadas else "Nenhuma etiqueta detectada."
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
    except EnvironmentError as e:
        # Captura erro relacionado a variáveis de ambiente
        print(f"Environment Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }
    except Exception as e:
        # Registrar erro com mais contexto
        print(f"Erro: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)})
        }

