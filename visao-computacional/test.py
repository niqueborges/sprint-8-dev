import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

bucket_name = 'gato-sapeca'
object_key = 'myphotos/test-happy.jpg'

try:
    s3.head_object(Bucket=bucket_name, Key=object_key)
    print("O objeto existe e você tem acesso.")
except ClientError as e:
    print("Erro ao acessar o objeto:", e)

