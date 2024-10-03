import json

# Função 'health' que é executada para verificar o status da aplicação
def health(event, context):
    # Monta o corpo da resposta com uma mensagem de sucesso e os dados recebidos no evento
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",  # Mensagem de sucesso
        "input": event,  # Dados recebidos como input no evento
    }

    # Cria a resposta HTTP com o status 200 (sucesso) e o corpo em formato JSON
    response = {
        "statusCode": 200,  # Código de status HTTP para sucesso
        "body": json.dumps(body),  # Converte o corpo da resposta para uma string JSON
    }

    return response  # Retorna a resposta para ser enviada de volta ao solicitante


# Função 'v1_description' que retorna a descrição da API VISION versão 1
def v1_description(event, context):
    # Monta o corpo da resposta com a versão da API
    body = {
        "message": "VISION api version 1."  # Mensagem com a descrição da versão 1 da API
    }

    # Cria a resposta HTTP com o status 200 (sucesso) e o corpo em formato JSON
    response = {
        "statusCode": 200,  # Código de status HTTP para sucesso
        "body": json.dumps(body),  # Converte o corpo da resposta para uma string JSON
    }

    return response  # Retorna a resposta para ser enviada de volta ao solicitante


# Função 'v2_description' que retorna a descrição da API VISION versão 2
def v2_description(event, context):
    # Monta o corpo da resposta com a versão da API
    body = {
        "message": "VISION api version 2."  # Mensagem com a descrição da versão 2 da API
    }

    # Cria a resposta HTTP com o status 200 (sucesso) e o corpo em formato JSON
    response = {
        "statusCode": 200,  # Código de status HTTP para sucesso
        "body": json.dumps(body),  # Converte o corpo da resposta para uma string JSON
    }

    return response  # Retorna a resposta para ser enviada de volta ao solicitante
