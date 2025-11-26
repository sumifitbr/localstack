import boto3
import argparse
import sys
from botocore.exceptions import ClientError

# --- CONFIGURAÇÃO (Pode ser movida para um arquivo de configuração ou envs) ---
LOCALSTACK_ENDPOINT_URL = "https://localstack.sumifit.business"
LOCALSTACK_AWS_ACCESS_KEY_ID = "test"
LOCALSTACK_AWS_SECRET_ACCESS_KEY = "test"
AWS_REGION = "us-east-1"
# ----------------------------------------------------------------------------


def create_s3_client(use_localstack=True):
    """
    Cria e retorna um cliente S3 do Boto3, configurado para AWS ou LocalStack.
    """
    client_kwargs = {
        "service_name": "s3",
        "region_name": AWS_REGION
    }

    if use_localstack:
        client_kwargs["endpoint_url"] = LOCALSTACK_ENDPOINT_URL
        client_kwargs["aws_access_key_id"] = LOCALSTACK_AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = LOCALSTACK_AWS_SECRET_ACCESS_KEY
    
    return boto3.client(**client_kwargs)


def ensure_bucket_exists(s3_client, bucket_name):
    """
    Cria o bucket se ele não existir.
    Retorna True se o bucket existir ou foi criado, False em caso de erro.
    """
    try:
        # Tenta verificar se o bucket existe (head_bucket)
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' já existe. Ignorando a criação.")
        return True
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        # 404 significa que o bucket não existe e pode ser criado
        if error_code == '404':
            print(f"Bucket '{bucket_name}' não encontrado. Criando...")
            try:
                # LocalStack ignora a LocationConstraint, mas a AWS a exige fora de us-east-1
                if AWS_REGION == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                print(f"Bucket '{bucket_name}' criado com sucesso.")
                return True
            except ClientError as ce:
                print(f"Erro ao criar bucket '{bucket_name}': {ce}")
                return False
        
        # 403 significa acesso negado (sem permissão)
        elif error_code == '403':
            print(f"Erro de permissão: Sem acesso ao bucket '{bucket_name}'.")
            return False
        
        else:
            print(f"Erro inesperado ao verificar o bucket: {e}")
            return False


def ensure_key_prefix_exists(s3_client, bucket_name, key_prefix):
    """
    Cria a estrutura de pastas (key prefix) se ela não existir.
    """
    # Garante que a chave termine com '/'
    if not key_prefix.endswith('/'):
        key_prefix += '/'

    # 1. Verifica se a "pasta" já existe
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=key_prefix,
        MaxKeys=1
    )
    
    # Se 'Contents' existir e não for vazio, o prefixo já tem arquivos ou a própria pasta
    if 'Contents' in response:
        print(f"Estrutura de pastas '{key_prefix}' já existe. Ignorando a criação.")
        return True

    # 2. Se não existir, cria a pasta (adicionando um objeto vazio com a chave)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key_prefix)
        print(f"Estrutura de pastas '{key_prefix}' criada com sucesso.")
        return True
    except ClientError as e:
        print(f"Erro ao criar a pasta '{key_prefix}': {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Gerencia a estrutura S3 (Bucket e Pastas) no LocalStack.")
    parser.add_argument("--bucket-name", required=True, help="Nome do bucket a ser criado/verificado (ex: datalake-dev).")
    parser.add_argument("--key", required=True, help="Estrutura de pastas (prefixo) a ser criada dentro do bucket (ex: landing-zone/oca-digital/alta-celulares/).")
    
    # Opcional: Adicionar a opção para usar o AWS real, se necessário
    parser.add_argument("--aws", action="store_true", help="Use esta flag para apontar para o AWS real (em vez do LocalStack).")
    
    args = parser.parse_args()

    # Cria o cliente, decidindo se usa LocalStack ou AWS
    s3 = create_s3_client(use_localstack=not args.aws)

    # --- 1. Garantir que o Bucket exista ---
    if not ensure_bucket_exists(s3, args.bucket_name):
        sys.exit(1) # Sai se o bucket não puder ser criado/verificado
        
    # --- 2. Garantir que a estrutura de pastas exista ---
    ensure_key_prefix_exists(s3, args.bucket_name, args.key)
    
    # --- 3. Confirmação (Opcional, mas útil) ---
    print("-" * 40)
    print(f"Estrutura final S3 Path: s3://{args.bucket_name}/{args.key.strip('/')}/")
    
    # Lista o conteúdo para confirmação visual
    response = s3.list_objects_v2(Bucket=args.bucket_name, Prefix=args.key)

    print(f"\nConteúdo (Prefixado) do bucket: {args.bucket_name}")
    if response.get("Contents"):
        for item in response["Contents"]:
            print(" -", item["Key"])
    else:
        print(" - Estrutura criada com sucesso, mas o prefixo está vazio.")


if __name__ == "__main__":
    main()