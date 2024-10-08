import boto3
import json
from pytz import timezone
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
from vision_face import detect_emotions  # Importa a função que detecta emoções

# Carrega as credenciais do ambiente
load_dotenv()

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis para acesso
S3_BUCKET = "photogrupo3"  # Altere para o nome do seu bucket S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")  # Sua Access Key ID da AWS
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # Sua Secret Key da AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Região AWS, ou retorna a padrão

# Inicializa a sessão boto3 com credenciais
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

rekognition = boto3.client("rekognition")
bedrock = boto3.client("bedrock-runtime")  # Cliente para Bedrock

def detect_labels(bucket: str, image_name: str) -> dict:
    """Função para detectar rótulos em uma imagem armazenada no S3 usando Rekognition."""
    try:
        image_path = f"myphotos/{image_name}"  # Atualiza o caminho da imagem
        response = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": image_path}},  # Usa o caminho atualizado
            MaxLabels=10,
            MinConfidence=75,
        )
        return response
    except Exception as e:
        logger.error(f"Erro ao detectar rótulos: {str(e)}")
        return {"error": str(e)}


def generate_pastor_tips(labels: list) -> dict:
    """Gera dicas sobre cães pastores baseadas em rótulos detectados."""
    exclude_keywords = {"Animal", "Canine", "Mammal", "Pet", "Dog"}
    pastor_labels = [
        {"Confidence": label["Confidence"], "Name": label["Name"]}
        for label in labels
        for category in label.get("Categories", [])
        if category["Name"] == "Animals and Pets"
    ]

    other_pastor_labels = [
        label["Name"] for label in pastor_labels if label["Name"] not in exclude_keywords
    ]

    logger.info(f"Rótulos filtrados: {other_pastor_labels}")

    if other_pastor_labels:
        raca_nome = other_pastor_labels[0]
        logger.info(f"Raça identificada: {raca_nome}")

        prompt = (
            f"Eu gostaria de Dicas sobre cães pastores como {raca_nome}. Por favor, forneça informações detalhadas seguindo a estrutura abaixo:\n"
            "Nível de Energia e Necessidades de Exercícios:\n"
            "Temperamento e Comportamento:\n"
            "Cuidados e Necessidades:\n"
            "Problemas de Saúde Comuns:\n"
        )

        native_request = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 500,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }

        logger.info(f"Enviando prompt ao Bedrock: {prompt}")

        try:
            response = bedrock.invoke_model(
                modelId="amazon.titan-text-express-v1",
                body=json.dumps(native_request),
            )

            model_response = json.loads(response["body"].read())
            bedrock_response = model_response["results"][0]["outputText"]

            logger.info(f"Resposta do Bedrock: {bedrock_response}")

            return {
                "labels": pastor_labels,
                "Dicas": bedrock_response,
            }

        except Exception as e:
            logger.error(f"ERROR: Can't invoke the Bedrock model. Reason: {e}")
            return {"error": str(e)}

    logger.warning("Nenhuma raça identificada.")
    return pastor_labels

def validate_input(body):
    """Valida os campos obrigatórios no corpo da requisição."""
    if not body.get("bucket"):
        raise ValueError("O campo 'bucket' é obrigatório.")
    if not body.get("imageName"):
        raise ValueError("O campo 'imageName' é obrigatório.")
    return body["bucket"], body["imageName"]

def handler_pastor(event, context):
    """Função principal do Lambda para processar a imagem e gerar dicas sobre cães pastores."""
    try:
        body = json.loads(event["body"])
        logger.info("Event received: %s", json.dumps(event))

        # Valida e obtém bucket e nome da imagem
        bucket, image_name = validate_input(body)

        # Adiciona a pasta 'myphotos' ao nome da imagem
        image_path = f"myphotos/{image_name}"  # Caminho da imagem atualizado

        # Detecta emoções na imagem
        response = detect_emotions(bucket, image_path)  # Use o caminho atualizado
        logger.info("Rekognition response: %s", json.dumps(response))

        faces = []
        for face in response.get("FaceDetails", []):
            position = face["BoundingBox"]
            emotion = max(face["Emotions"], key=lambda e: e["Confidence"], default={"Type": "Unknown", "Confidence": 0})
            faces.append(
                {
                    "position": {
                        "Height": position["Height"],
                        "Left": position["Left"],
                        "Top": position["Top"],
                        "Width": position["Width"],
                    },
                    "classified_emotion": emotion["Type"],
                    "classified_emotion_confidence": emotion["Confidence"],
                }
            )

        # Detectando pets usando Rekognition (labels)
        rekognition_label_response = detect_labels(bucket, image_path)  # Use o caminho atualizado
        labels = rekognition_label_response.get("Labels", [])

        # Verifica se há cães pastores e gera dicas
        pastor_analysis = generate_pastor_tips(labels)
        if pastor_analysis.get("labels"):
            fuso = timezone("America/Sao_Paulo")
            result = {
                "url_to_image": f"https://{bucket}.s3.amazonaws.com/{image_path}",  # Atualize a URL da imagem
                "created_image": datetime.now(fuso).strftime("%d-%m-%Y %H:%M:%S"),
                "faces": faces if faces else None,
                "pets": (pastor_analysis,)  # Envolve em tupla para manter consistência
            }

            logger.info("Response: %s", json.dumps(result))
            return {"statusCode": 200, "body": json.dumps(result)}

        logger.info("Nenhum cão pastor detectado.")
        return {"statusCode": 200, "body": json.dumps({"message": "No pastor dogs detected"})}

    except ValueError as ve:
        logger.error(f"Valor inválido: {str(ve)}")
        return {"statusCode": 400, "body": json.dumps({"error": str(ve)})}
    except Exception as e:
        logger.error(f"Erro ao processar a imagem: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Failed to process the image"})}
