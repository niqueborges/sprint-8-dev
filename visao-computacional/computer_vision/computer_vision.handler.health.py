import json

def create_response(status_code, message):
    """Cria uma resposta padrão para a API."""
    return {
        "statusCode": status_code,
        "body": json.dumps({"message": message})
    }

def health(event, context):
    """Verifica se a função está funcionando corretamente."""
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }
    return create_response(200, body)

def v1_description(event, context):
    """Retorna a versão 1 da API VISION."""
    return create_response(200, "VISION API version 1.")

def v2_description(event, context):
    """Retorna a versão 2 da API VISION."""
    return create_response(200, "VISION API version 2.")
