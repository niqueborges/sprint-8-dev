import os

def add_env_var(variables: dict):
    env_file = '.env'
    
    try:
        # Lê o conteúdo existente do .env
        if os.path.exists(env_file):
            with open(env_file, 'r') as file:
                lines = file.readlines()
        else:
            lines = []

        # Para cada variável na lista, verifica se já existe e, se não, adiciona
        for key, value in variables.items():
            if not any(line.startswith(f"{key}=") for line in lines):
                with open(env_file, 'a') as file:
                    file.write(f'\n{key}="{value}"\n')
    except IOError as e:
        print(f"Erro ao acessar o arquivo .env: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Exemplo de uso:
add_env_var({
    "BUCKET_NAME": "vision-project-bucket",  # Nome do bucket S3 para o projeto de visão
    "IMAGE_S3_DIR": "images",  # Diretório no S3 onde as imagens são armazenadas
    "API_KEY": "your_api_key_here",  # Exemplo de chave de API, se necessário
    "ENDPOINT_URL": "https://your-endpoint-url.com"  # URL do endpoint da API
})
