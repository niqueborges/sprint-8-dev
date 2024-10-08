import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
import os

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_face_emotions(bucket_name: str, image_name: str) -> dict:
    """
    Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition.

    Args:
        bucket_name (str): O nome do bucket S3 onde a imagem está armazenada.
        image_name (str): O nome da imagem no bucket S3 (incluindo o caminho da pasta).

    Returns:
        dict: Um dicionário contendo informações sobre as emoções detectadas nas faces.
              Se ocorrer um erro, o dicionário contém uma mensagem de erro.
    """
    # Verifica se os parâmetros estão vazios
    if not bucket_name or not image_name:
        logger.error("Nome do bucket ou da imagem não pode ser vazio.")
        return {
            "error": "Nome do bucket ou da imagem não pode ser vazio."
        }

    rekognition = boto3.client("rekognition")

    try:
        # Chama a API do Rekognition para detectar faces e emoções
        response = rekognition.detect_faces(
            Image={
                "S3Object": {
                    "Bucket": bucket_name,
                    "Name": image_name  # O image_name deve incluir 'myphotos/'
                }
            },
            Attributes=["ALL"]  # Solicita todas as emoções
        )
        logger.info("Resposta do Rekognition recebida com sucesso.")
    except (BotoCoreError, ClientError) as e:
        # Captura erros ao chamar a API do Rekognition
        logger.error("Erro ao chamar a API Rekognition: %s", e)
        return {
            "error": "Erro ao chamar a API Rekognition",
            "message": str(e)
        }

    # Se não houver detalhes de face na resposta
    if not response.get("FaceDetails"):
        logger.warning("Nenhuma face detectada na imagem.")
        return {
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
        }

    face_data = {"faces": []}

    # Processa cada face detectada
    for face in response.get("FaceDetails", []):
        # Encontra a emoção com a maior confiança
        if face.get("Emotions"):
            max_emotion = max(face["Emotions"], key=lambda e: e["Confidence"])
            emotion = max_emotion["Type"]
            confidence_emotion = max_emotion["Confidence"]
        else:
            emotion = None
            confidence_emotion = 0

        # Monta as informações da face detectada
        face_info = {
            "position": {
                "Height": face["BoundingBox"]["Height"],
                "Left": face["BoundingBox"]["Left"],
                "Top": face["BoundingBox"]["Top"],
                "Width": face["BoundingBox"]["Width"]
            },
            "classified_emotion": emotion,
            "classified_emotion_confidence": confidence_emotion
        }

        face_data["faces"].append(face_info)

    logger.info("Processamento concluído. Total de faces detectadas: %d", len(face_data["faces"]))
    return face_data

