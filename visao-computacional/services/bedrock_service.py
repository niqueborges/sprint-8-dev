import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def invoke_bedrock_model(model_id: str, text: str, cfg_scale=8, seed=0, quality="standard", width=1024, height=1024, number_of_images=3):
    if not model_id or not text:
        return {
            "error": "model_id e text são obrigatórios."
        }
    
    bedrock_client = boto3.client('bedrock')

    request_body = {
        "textToImageParams": {
            "text": text
        },
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": cfg_scale,
            "seed": seed,
            "quality": quality,
            "width": width,
            "height": height,
            "numberOfImages": number_of_images
        }
    }

    try:
        logger.info(f"Iniciando a invocação do modelo: {model_id} com texto: {text}")
        response = bedrock_client.invoke_model(
            ModelId=model_id,
            ContentType="application/json",
            Body=json.dumps(request_body)
        )

        result = json.loads(response['Body'].read())
        return result
    
    except ClientError as e:
        logger.error(f"Erro ao invocar o modelo: {e}")
        return {
            "error": "Erro ao invocar o modelo no Bedrock",
            "message": str(e)
        }
