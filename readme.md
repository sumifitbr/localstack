# Gerando diversos comandos para localstack

Meu config associado ao user do localstack está em */home/laralves/.aws/config*

## Dados Localstack

### 1. Defina o endpoint do LocalStack (se ainda não o fez)
LOCALSTACK_URL="https://localstack.sumifit.business"

REGION="us-east-1"

TOPIC_NAME="pipeline-failure-notifications"

### 2. Crie o tópico SNS

```
aws sns create-topic --name pipeline-failure-notifications --profile localstack --region us-east-1 
```

Tipo|Valores
--|--
SNS_ARN|arn:aws:sns:us-east-1:000000000000:pipeline-failure-notifications
SECRET_NAME|oca-pipeline-glue

### 3. Criando o secret manager
```
aws secretsmanager create-secret \
    --name oca-pipeline-glue \
    --secret-string file://secret.json \
    --profile localstack
```    

### 4. Deleta o secret manager
```
aws secretsmanager delete-secret \
    --secret-id oca-pipeline-glue \
    --force-delete-without-recovery \
    --profile localstack
```      

### 5. Criando bucket s3
# Execução apontando para o LocalStack (com a flag --key)
```
python scripts/create_bucket.py \
    --bucket-name datalake-dev \
    --key parameters/
```    

### 6. Criando Tabela no DYNAMODB
# Defina suas variáveis (opcional, mas recomendado)
```
aws dynamodb create-table \
    --cli-input-json file://create-table-tb_process.json \
    --endpoint-url "https://localstack.sumifit.business" \
    --profile localstack \
    --region us-east-1
```

### 7. Criando Tabela no DYNAMODB
# Defina suas variáveis (opcional, mas recomendado)
```
aws dynamodb put-item \
    --table-name tb_process \
    --item file://put-item-tb_process.json \
    --endpoint-url "https://localstack.sumifit.business" \
    --profile localstack \
    --region us-east-1
```

### 8. Criando um policy
```
aws iam create-policy \
    --policy-name FullAccessPolicy \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }
        ]
    }' \
    --endpoint-url "https://localstack.sumifit.business" \
    --region us-east-1
```    

##### Politica para o bucket

```
aws s3api put-bucket-policy \
    --bucket datalake-dev \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowAllS3ActionsForIntegrationUser",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "s3:*",
                "Resource": [
                    "arn:aws:s3:::datalake-dev",
                    "arn:aws:s3:::datalake-dev/*"
                ]
            }
        ]
    }' \
    --endpoint-url "https://localstack.sumifit.business" \
    --region us-east-1
```

###### Retono do comando acima
```
{
    "Policy": {
        "PolicyName": "FullAccessPolicy",
        "PolicyId": "AEOVMAVIV6XP535BOHWAD",
        "Arn": "arn:aws:iam::000000000000:policy/FullAccessPolicy",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 0,
        "IsAttachable": true,
        "Description": "",
        "CreateDate": "2025-10-14T11:47:04.615675+00:00",
        "UpdateDate": "2025-10-14T11:47:04.615682+00:00",
        "Tags": []
    }
}
```

### 9. Anexando usuario a policy acima
```
aws iam attach-user-policy \
    --user-name integration \
    --policy-arn arn:aws:iam::000000000000:policy/FullAccessPolicy \
    --endpoint-url "https://localstack.sumifit.business" \
    --region us-east-1
```

#### Verificando se a policy foi anexado com sucesso
```
aws iam list-attached-user-policies \
    --user-name integration \
    --endpoint-url "https://localstack.sumifit.business" \
    --region us-east-1
```

### 10. Criando Accesskey e SecretKey para o usuario
```
aws iam create-access-key \
    --user-name integration \
    --endpoint-url "https://localstack.sumifit.business" \
    --region us-east-1
```

#### Retorno do comando acima
```
{
    "AccessKey": {
        "UserName": "integration",
        "AccessKeyId": "LKIAQAAAAAAAGLJXDEB7",
        "Status": "Active",
        "SecretAccessKey": "lKvhDHFjlnttTjgV5jS4aLvH3/Y/i+JJq7GdtFcY",
        "CreateDate": "2025-10-14T11:54:35.004760+00:00"
    }
}
```

## Trabalhando com STEP FUNCTIONS

### Testando se tudo está de acordo

1. Crie um arquivo na raiz chamado *hello-world-stepfn.json* com o conteúdo abaixo:

```
{
  "Comment": "Exemplo simples Step Functions no LocalStack",
  "StartAt": "Hello",
  "States": {
    "Hello": {
      "Type": "Pass",
      "Result": "Olá do Step Functions!",
      "End": true
    }
  }
}
```

2. Execute o comando 
```
aws stepfunctions create-state-machine \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --name HelloStateMachine \
  --definition file://hello-world-stepfn.json \
  --role-arn arn:aws:iam::000000000000:role/DummyRole
```

Se tudo correu bem a saída no terminal será:

```
{
    "stateMachineArn": "arn:aws:states:us-east-1:000000000000:stateMachine:HelloStateMachine",
    "creationDate": "2025-11-25T19:35:53.584626-03:00"
}
```
e você verá em (https://app.localstack.cloud)[APP LOCALSTACK CLOUD] o item criado.