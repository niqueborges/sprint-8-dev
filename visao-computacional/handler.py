import json


def health(event, context):
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

def v1_description(event, context):
    body = {
        "message": "VISION api version 1."
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

def v2_description(event, context):
    body = {
        "message": "VISION api version 2."
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

def v1_vision(event, context):
    try:
        # Tenta extrair e validar o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        
        # Verifica se os parâmetros estão presentes
        bucket = body.get('bucket')
        image_name = body.get('imageName')
        
        if not bucket or not image_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing 'bucket' or 'imageName' in the request body"})
            }

        # Monta a resposta com os dados recebidos
        response_body = {
            "message": {
                "bucket": bucket,
                "imageName": image_name
            }
        }

        return {
            "statusCode": 200,
            "body": json.dumps(response_body)
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON in the request body"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal Server Error: {str(e)}"})
        }
