import boto3
import json
from botocore.exceptions import ClientError

def invoke_bedrock_model(model_id: str, text: str):
    """
    Invoca o modelo Titan Image Generator v2 hospedado no AWS Bedrock com os dados fornecidos.
    
    Args:
        model_id (str): ID do modelo no Bedrock.
        text (str): O texto que será transformado em imagem.

    Returns:
        dict: Resposta do Bedrock ou mensagem de erro.
    """
    bedrock_client = boto3.client('bedrock')  # Cria o cliente do Bedrock

    # Configura o corpo da solicitação de acordo com a documentação do modelo
    request_body = {
        "textToImageParams": {
            "text": text
        },
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": 8,
            "seed": 0,
            "quality": "standard",
            "width": 1024,
            "height": 1024,
            "numberOfImages": 3
        }
    }

    try:
        # Invoca o modelo no AWS Bedrock
        response = bedrock_client.invoke_model(
            ModelId=model_id,
            ContentType="application/json",
            Body=json.dumps(request_body)  # Converte os dados de entrada para JSON
        )

        # Lê a resposta do modelo
        result = json.loads(response['Body'].read())
        return result
    
    except ClientError as e:
        return {
            "error": "Erro ao invocar o modelo no Bedrock",
            "message": str(e)
        }
