import sys
import os
import boto3
import json
from botocore.exceptions import ClientError
import importlib

# Adiciona o caminho do diretório pai ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório atual (utils)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))  # Diretório pai (visao-computacional)
sys.path.append(parent_dir)

# Importa o módulo correto para o projeto
try:
    add_env_var_module = importlib.import_module("utils.check_env")  # Ajuste o caminho conforme necessário
    add_env_var = add_env_var_module.add_env_var
except ModuleNotFoundError as e:
    print(f"Erro ao importar o módulo: {e}")
    sys.exit(1)

def create_bucket(bucket_name):
    s3 = boto3.client('s3')

    try:
        # Verifica se o bucket já existe (exceção será lançada se o bucket não existir)
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} já existe.")
        return True  # Retorna True se o bucket já existir
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                # Obtém a região da sessão atual
                region = boto3.session.Session().region_name

                # Cria o bucket, sem LocationConstraint para 'us-east-1'
                if region == 'us-east-1':
                    s3.create_bucket(Bucket=bucket_name)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': region  # Define a região
                        }
                    )
                print(f"Bucket {bucket_name} criado com sucesso.")

                # Desabilita o bloqueio de ACLs públicas
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )

                # Define uma política de bucket para permitir acesso público
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        },
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:PutObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
                s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
                print(f"Política do bucket {bucket_name} aplicada com sucesso.")
                return True

            except ClientError as e:
                print(f"Erro ao criar o bucket: {e}")
                return False
        else:
            # Caso o erro seja diferente de '404', imprima o erro
            print(f"Erro ao verificar o bucket: {e}")
            return False

    # Adicionar as informações ao .env se o bucket foi criado com sucesso
    add_env_var({
        "BUCKET_NAME": bucket_name,
        "VISION_S3_DIR": "myphotos"  # Atualiza o diretório para o contexto do projeto
    })
    print(f"Variáveis de ambiente adicionadas com sucesso.")

if __name__ == "__main__":
    bucket_name = "gato-sapeca"  # Nome do bucket ajustado para o projeto
    create_bucket(bucket_name)

