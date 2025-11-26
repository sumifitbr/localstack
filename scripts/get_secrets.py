# Função que coleta secret manager
def get_secret(use_localstack=True):
    """
    Recupera as configurações do AWS Secrets Manager.

    Secret utilizado: 'oca-pipeline-glue'
    Região padrão: 'us-east-1'
    """
    secret_name = "oca-pipeline-glue"
    region_name = "us-east-1"

    try:
        # Cria sessão (pode ser mantida, mas a configuração do cliente é o que importa)
        session = boto3.session.Session()
        
        client_kwargs = {
            "service_name": "secretsmanager",
            "region_name": region_name
        }

        # ** A MUDANÇA PRINCIPAL: Adiciona as configurações do LocalStack se estiver em uso **
        if use_localstack:
            client_kwargs["endpoint_url"] = LOCALSTACK_ENDPOINT_URL
            client_kwargs["aws_access_key_id"] = LOCALSTACK_AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = LOCALSTACK_AWS_SECRET_ACCESS_KEY
        
        # Cria o cliente do Secrets Manager com ou sem as configurações do LocalStack
        client = session.client(**client_kwargs)

        # Busca o valor do secret
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        # Retorna o conteúdo do secret
        if "SecretString" in get_secret_value_response:
            return json.loads(get_secret_value_response["SecretString"])
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response["SecretBinary"])
            return json.loads(decoded_binary_secret)

    except Exception as e:
        error_message = f"Erro ao recuperar secret do AWS Secrets Manager: {e}\n" \
                        f"Verifique as variáveis do AWS Secret Manager '{secret_name}'"
        print(error_message)
        raise