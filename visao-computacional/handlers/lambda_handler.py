import json
import os
import boto3
import sys
from datetime import datetime
from dotenv import load_dotenv
import traceback
import logging
from botocore.exceptions import ClientError

current_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório atual (handlers)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))  # Diretório pai (visao-computacional)
sys.path.append(parent_dir)

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente AWS Rekognition
rekognition = boto3.client('rekognition', region_name='us-east-1')  

def check_env_vars():
    """
    Função para verificar se todas as variáveis de ambiente necessárias estão definidas.

    Levanta um erro se alguma variável obrigatória estiver faltando.
    """
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def health(event, context):
    """
    Função de verificação de saúde do serviço.

    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com status de operação.
    """
    body = {
        "message": "Go Serverless v3.0! Sua função foi executada com sucesso!",
        "input": event,
    }
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

def v1_description(event, context):
    """
    Descrição da API versão 1.

    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com descrição da versão da API.
    """
    body = {"message": "VISÃO api versão 1."}
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

def v2_description(event, context):
    """
    Descrição da API versão 2.

    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com descrição da versão da API.
    """
    body = {"message": "VISÃO api versão 2."}
    response = {"statusCode": 200, "body": json.dumps(body)}
    return response

def vision(event, context):
    """
    Função para detectar emoções faciais em uma imagem armazenada no S3.

    Args:
        event (dict): Dados do evento que disparou a função (inclui o corpo da requisição).
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com os detalhes da imagem e emoções detectadas ou mensagem de erro.
    """
    try:
        # Verifica se as variáveis de ambiente necessárias estão definidas
        check_env_vars()

        # Tenta extrair e validar o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        logger.info("Requisição recebida: %s", body)  # Para debug

        bucket = body.get('bucket')
        image_name = body.get('imageName')

        # Valida se os parâmetros essenciais estão presentes
        if not bucket or not image_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Faltando 'bucket' ou 'imageName' no corpo da requisição"})
            }

        # Verifica se o bucket é permitido
        allowed_buckets = [os.getenv('BUCKET_NAME')]  # Adicione outros buckets permitidos aqui, se necessário
        if bucket not in allowed_buckets:
            return {
                "statusCode": 403,
                "body": json.dumps({"message": "Bucket não permitido."})
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
        logger.info("Resposta do Rekognition: %s", response)  # Para debug

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
        logger.info("Corpo da resposta: %s", json.dumps(response_body))

        return {
            "statusCode": 200,
            "body": json.dumps(response_body)
        }

    except json.JSONDecodeError:
        logger.error("JSON inválido no corpo da requisição.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "JSON inválido no corpo da requisição"})
        }
    except ClientError as e:
        logger.error(f"Erro ao chamar Rekognition: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Erro ao chamar o serviço Rekognition."})
        }
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        traceback.print_exc()  # Loga o traceback completo para facilitar o debug
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Erro interno do servidor"})
        }
