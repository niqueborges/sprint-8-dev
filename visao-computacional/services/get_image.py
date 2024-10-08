import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Dict, Any, Union

def get_image_details(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Obtém os detalhes de uma imagem armazenada no S3.

    Args:
        bucket_name (str): O nome do bucket S3.
        image_name (str): A chave (nome) do arquivo de imagem no bucket S3.

    Returns:
        dict: Um dicionário contendo a URL da imagem e sua data de criação,
              ou uma mensagem de erro caso a operação falhe.
    """
    # Cria um cliente Boto3 S3 para interagir com o serviço S3
    s3_client = boto3.client("s3")

    # Inclui o caminho "myphotos/" no nome da imagem
    image_key = f"myphotos/{image_name}"

    try:
        # Tenta recuperar os metadados do objeto especificado no bucket S3
        response = s3_client.head_object(Bucket=bucket_name, Key=image_key)
    except (BotoCoreError, ClientError) as e:
        # Trata erros que podem ocorrer ao chamar a API do S3
        return {
            "error": "Erro ao obter detalhes da imagem do S3",  # Mensagem de erro para o chamador
            "message": str(e)  # Mensagem de erro detalhada para depuração
        }

    # Constrói a URL para acessar a imagem diretamente do S3
    url_to_image = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
    
    # Recupera a data da última modificação do objeto da resposta
    creation_date = response["LastModified"]

    # Formata a data de criação para um formato de string mais legível
    formatted_creation_date = creation_date.strftime("%d-%m-%Y %H:%M:%S")
    
    # Prepara a resposta contendo a URL da imagem e a data de criação formatada
    s3_image_details = {
        "url_to_image": url_to_image,
        "created_image": formatted_creation_date
    }
    
    # Retorna os detalhes da imagem como um dicionário
    return s3_image_details


def detect_face_emotions(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Detecta emoções faciais em uma imagem armazenada no S3 usando o Amazon Rekognition.

    Args:
        bucket_name (str): O nome do bucket S3.
        image_name (str): O nome da imagem no S3.

    Returns:
        dict: Dados das emoções detectadas ou mensagem de erro.
    """
    rekognition = boto3.client('rekognition')

    # Inclui o caminho "myphotos/" no nome da imagem
    image_key = f"myphotos/{image_name}"

    try:
        response = rekognition.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            },
            Attributes=['ALL']  # Inclui todas as características (inclusive emoções)
        )

        # Extrai as emoções da primeira face detectada, se houver
        if response['FaceDetails']:
            face_details = response['FaceDetails'][0]
            emotions = face_details['Emotions']
            return {"Emotions": emotions}
        else:
            return {"error": "Nenhuma face detectada na imagem"}

    except ClientError as e:
        return {"error": "Erro ao detectar emoções faciais", "message": str(e)}
