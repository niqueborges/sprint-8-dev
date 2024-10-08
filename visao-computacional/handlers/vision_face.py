import sys
import os
import json
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o caminho do diretório visao-computacional ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório atual (handlers)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))  # Diretório pai (visao-computacional)
sys.path.append(parent_dir)

from services.bedrock_service import invoke_bedrock_model
from services.get_image import get_image_details, detect_face_emotions

def validate_input(body):
    """
    Valida os campos obrigatórios no corpo da requisição.

    Args:
        body (dict): O corpo da requisição.

    Returns:
        tuple: Um booleano que indica se a validação passou e um dicionário de erros, se houver.
    """
    errors = {}
    if not body.get("bucket"):
        errors["bucket"] = "O campo 'bucket' é obrigatório."
    if not body.get("imageName"):
        errors["imageName"] = "O campo 'imageName' é obrigatório."
    
    return len(errors) == 0, errors

def v1_vision(event, context):
    """
    Função para detectar emoções faciais em uma imagem armazenada no S3.
    Além disso, utiliza o Bedrock para processar a imagem.

    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com os detalhes da imagem, emoções detectadas ou mensagem de erro.
    """
    try:
        body = event.get("body")
        if body:
            try:
                body = json.loads(body)  # Tenta converter o corpo para um dicionário
            except json.JSONDecodeError:
                logger.error("JSON inválido no corpo da requisição.")
                return {"statusCode": 400, "body": json.dumps({"error": "JSON inválido no corpo da requisição"})}

        # Valida os campos obrigatórios
        is_valid, errors = validate_input(body)
        if not is_valid:
            logger.error("Erro de validação: %s", errors)
            return {"statusCode": 400, "body": json.dumps({"error": "Erro de validação", "details": errors})}

        # Obtém detalhes da imagem
        bucket_name = body["bucket"]
        image_name = body["imageName"]

        # Atualiza o caminho da imagem com a pasta 'myphotos'
        image_path = f"myphotos/{image_name}"  # Inclui a pasta 'myphotos' no caminho

        # Obtém detalhes da imagem a partir do bucket S3
        s3_image_details = get_image_details(bucket_name, image_path)  # Use o caminho atualizado
        if "error" in s3_image_details:
            logger.error("Erro ao obter detalhes da imagem: %s", s3_image_details["error"])
            return {"statusCode": 500, "body": json.dumps(s3_image_details)}

        # Detecta emoções na imagem usando Rekognition
        face_data = detect_face_emotions(bucket_name, image_path)  # Use o caminho atualizado
        if "error" in face_data:
            logger.error("Erro ao detectar emoções: %s", face_data["error"])
            return {"statusCode": 500, "body": json.dumps(face_data)}

        # Combina os dados do S3 e do Rekognition
        response_body = {**s3_image_details, **face_data}

        # --- Integração com AWS Bedrock ---
        text_input = "Análise da imagem: " + image_name  # Texto descritivo da imagem
        bedrock_response = invoke_bedrock_model(model_id="amazon.titan-image-generator-v2:0", text=text_input)

        # Verifica se houve algum erro ao invocar o modelo do Bedrock
        if "error" in bedrock_response:
            logger.error("Erro ao processar a imagem com Bedrock: %s", bedrock_response["error"])
            return {"statusCode": 500, "body": json.dumps(bedrock_response)}

        # Adiciona a resposta do Bedrock ao response_body
        response_body["bedrock_analysis"] = bedrock_response

        logger.info("Processamento concluído com sucesso.")
        response = {
            "statusCode": 200,
            "body": json.dumps(response_body, indent=4, ensure_ascii=True)
        }

    except Exception as e:
        logger.exception("Erro inesperado: %s", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": "Erro interno do servidor", "message": str(e)})}

    return response
