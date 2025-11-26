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

### 6. Criando Tabela no DYNAMODB - Defina suas variáveis (opcional, mas recomendado)
```
aws dynamodb create-table \
    --cli-input-json file://create-table-tb_process.json \
    --endpoint-url "https://localstack.sumifit.business" \
    --profile localstack \
    --region us-east-1
```

### 7. PUT Tabela no DYNAMODB - Defina suas variáveis (opcional, mas recomendado)
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

2. Criar a state Machine
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
    "creationDate": "2025-11-25T19:46:24.190477-03:00"
}
```
e você verá em (https://app.localstack.cloud)[APP LOCALSTACK CLOUD] o item criado.

3. Exectuar a State Machine
```
aws stepfunctions start-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:HelloStateMachine \
  --input '{"teste":"ok"}'

```
Retorno do comando
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:HelloStateMachine:08555d5d-dee7-4fe9-a902-dedb4d8b77f7",
    "startDate": "2025-11-26T07:39:45.207744-03:00"
}
```

4. Para ver o resultado do que foi criado
```
aws stepfunctions describe-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --execution-arn arn:aws:states:us-east-1:000000000000:execution:HelloStateMachine:08555d5d-dee7-4fe9-a902-dedb4d8b77f7

```
Retorno foi
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:HelloStateMachine:08555d5d-dee7-4fe9-a902-dedb4d8b77f7",
    "stateMachineArn": "arn:aws:states:us-east-1:000000000000:stateMachine:HelloStateMachine",
    "name": "08555d5d-dee7-4fe9-a902-dedb4d8b77f7",
    "status": "SUCCEEDED",
    "startDate": "2025-11-26T07:39:45.207744-03:00",
    "stopDate": "2025-11-26T07:39:45.230829-03:00",
    "input": "{\"teste\":\"ok\"}",
    "inputDetails": {
        "included": true
    },
    "output": "\"Ol\\u00e1 do Step Functions!\"",
    "outputDetails": {
        "included": true
    }
}
```

## Trabalhando com AWS LAMBDA

1. Criamos o arquivo lambda_hello.py

2. O localstack exige que a lambda criada no passo 1 seja **zipada**. Para Isso utilize o comando abaixo:

```zip lambda_hello.zip lambda_hello.py```

Isso gera um arquivo zip chamado *lambda_hello.zip*

3. Subir a lambda para o LocalStack

```
aws lambda create-function \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --function-name LambdaHello \
  --runtime python3.9 \
  --handler lambda_hello.handler \
  --role arn:aws:iam::000000000000:role/DummyRole \
  --zip-file fileb://lambda_hello.zip
```

Retorno foi:
```
{
    "FunctionName": "LambdaHello",
    "FunctionArn": "arn:aws:lambda:us-east-1:000000000000:function:LambdaHello",
    "Runtime": "python3.9",
    "Role": "arn:aws:iam::000000000000:role/DummyRole",
    "Handler": "lambda_hello.handler",
    "CodeSize": 341,
    "Description": "",
    "Timeout": 3,
    "MemorySize": 128,
    "LastModified": "2025-11-26T10:51:08.770209+0000",
    "CodeSha256": "iZaSMhgJb5e/s77gZILOxlCdGhNJJr4QNJzsFIoqJF4=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "c59d4f21-cf6a-4a1b-a555-83d8056d4af6",
    "State": "Pending",
    "StateReason": "The function is being created.",
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:8eeff65f6809a3ce81507fe733fe09b835899b99481ba22fd75b5a7338290ec1"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/LambdaHello"
    }
}
```
4. Testando a lambda antes do Step Functions
```
aws lambda invoke \
  --endpoint-url=http://localhost:4566 \
  --function-name LambdaHello \
  --payload '{"mensagem":"Oi Lambda!"}' \
  output.json
```

Retorno foi:
```
```

5. Criar a Step Function que chama a Lambda

a) Crie o arquivo stepfn_lambda.json
```
{
  "Comment": "Step Function chamando uma Lambda",
  "StartAt": "ChamarLambda",
  "States": {
    "ChamarLambda": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:LambdaHello",
      "End": true
    }
  }
}
```
6. Criar a State Machine
```
aws stepfunctions create-state-machine \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --name LambdaStateMachine \
  --definition file://stepfn_lambda.json \
  --role-arn arn:aws:iam::000000000000:role/DummyRole
```

Retorno foi:
```
{
    "stateMachineArn": "arn:aws:states:us-east-1:000000000000:stateMachine:LambdaStateMachine",
    "creationDate": "2025-11-26T07:58:13.158948-03:00"
}
```
7. Executar a state machine
```
aws stepfunctions start-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:LambdaStateMachine \
  --input '{"mensagem":"Chamando Lambda via Step Functions!"}'
```

Retorno foi:
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:LambdaStateMachine:a6ffa00e-d6ad-405d-b9ee-898e4fa658e9",
    "startDate": "2025-11-26T07:59:24.701052-03:00"
}
```

8. Ver o resultado
```
aws stepfunctions describe-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --execution-arn arn:aws:states:us-east-1:000000000000:execution:LambdaStateMachine:a6ffa00e-d6ad-405d-b9ee-898e4fa658e9
```
Retorno foi:
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:LambdaStateMachine:a6ffa00e-d6ad-405d-b9ee-898e4fa658e9",
    "stateMachineArn": "arn:aws:states:us-east-1:000000000000:stateMachine:LambdaStateMachine",
    "name": "a6ffa00e-d6ad-405d-b9ee-898e4fa658e9",
    "status": "SUCCEEDED",
    "startDate": "2025-11-26T07:59:24.701052-03:00",
    "stopDate": "2025-11-26T07:59:24.791813-03:00",
    "input": "{\"mensagem\":\"Chamando Lambda via Step Functions!\"}",
    "inputDetails": {
        "included": true
    },
    "output": "{\"statusCode\":200,\"body\":\"{\\\"msg\\\": \\\"Chamando Lambda via Step Functions!\\\"}\"}",
    "outputDetails": {
        "included": true
    }
}
```