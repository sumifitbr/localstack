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

2. Criando lambda "Validadora"

```
lambda_validacao.py
```

3. Zip a Lambda
```
zip lambda_validacao.zip lambda_validacao.py
```
4. Crie a lambda
```
aws lambda create-function \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --function-name LambdaValidacao \
  --runtime python3.9 \
  --handler lambda_validacao.handler \
  --role arn:aws:iam::000000000000:role/DummyRole \
  --zip-file fileb://lambda_validacao.zip
```
Resultado foi:
```
{
    "FunctionName": "LambdaValidacao",
    "FunctionArn": "arn:aws:lambda:us-east-1:000000000000:function:LambdaValidacao",
    "Runtime": "python3.9",
    "Role": "arn:aws:iam::000000000000:role/DummyRole",
    "Handler": "lambda_validacao.handler",
    "CodeSize": 379,
    "Description": "",
    "Timeout": 3,
    "MemorySize": 128,
    "LastModified": "2025-11-26T12:38:04.199192+0000",
    "CodeSha256": "9mpXAF20qCqhQQcoG0+L8x+qJAAq0zLIuoBLNfZZdH4=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "64bc4da3-ae98-4076-86b5-67f5e2819383",
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
        "LogGroup": "/aws/lambda/LambdaValidacao"
    }
}
```
5. Criando Step Function com Choice, Retry e Catch

```
stepfn_choice_retry_catch.json
```

6. Criar a State Machine
```
aws stepfunctions create-state-machine \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --name StepChoiceRetryCatch \
  --definition file://stepfn_choice_retry_catch.json \
  --role-arn arn:aws:iam::000000000000:role/DummyRole
```
Resultado foi
```{
    "stateMachineArn": "arn:aws:states:us-east-1:000000000000:stateMachine:StepChoiceRetryCatch",
    "creationDate": "2025-11-26T09:43:36.598239-03:00"
}
```
7. Testar diferentes cenários 

🟢 Cenário A: fluxo especial
```
aws stepfunctions start-execution \
  --cli-binary-format raw-in-base64-out \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:StepChoiceRetryCatch \
  --input '{"tipo":"A"}'
```
Resultado foi
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:StepChoiceRetryCatch:b691bb97-af52-48d7-953c-4b97c51e9625",
    "startDate": "2025-11-26T09:45:45.968130-03:00"
}
```

🟡 Cenário B: fluxo genérico
```
aws stepfunctions start-execution \
 --cli-binary-format raw-in-base64-out \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:StepChoiceRetryCatch \
  --input '{"tipo":"B"}'
```
Resultado foi
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:StepChoiceRetryCatch:96607c59-d657-428c-84c6-9cde7fde6fb1",
    "startDate": "2025-11-26T10:05:37.655615-03:00"
}
```

🔴 Cenário C: erro forçado + Catch
```
aws stepfunctions start-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:StepChoiceRetryCatch \
  --input '{"tipo":"erro"}'
```

Resultado foi
```
{
    "executionArn": "arn:aws:states:us-east-1:000000000000:execution:StepChoiceRetryCatch:1945867a-c822-4ccc-9408-55e22f5bfd3c",
    "startDate": "2025-11-26T10:06:39.857675-03:00"
}
```

Como toda a execução por padrão roda e retorna ARN, para verificar o resultado utilizamos:

👉 describe-execution

```
aws stepfunctions describe-execution \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --execution-arn arn:aws:states:us-east-1:000000000000:execution:StepChoiceRetryCatch:b101cef6-f7fa-4fbc-945b-dc47c13a93f2
```

🎁 BÔNUS (super útil)

Se quiser ver o passo a passo dos estados, use:
```
aws stepfunctions get-execution-history \
  --endpoint-url=http://localhost:4566 \
  --region us-east-1 \
  --execution-arn SEU_ARN
```

Isso mostra:

> qual step rodou

> quais inputs

> quais outputs

> onde deu erro

> retries executados

É uma ferramenta poderosa 🔥

### Desenho do fluxo

                 ┌────────────────────┐
                 │      INÍCIO        │
                 └─────────┬──────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │    ValidarEntrada    │
                │ (LambdaValidacao)    │
                └─────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────────┐
              │           Choice            │
              │    "tipo" == "A"?           │
              └──────────┬───────┬─────────┘
                         │       │
          SIM (tipo=A)   │       │   NÃO (default)
                         │       │
                         ▼       ▼
        ┌──────────────────┐     ┌──────────────────┐
        │ ProcessarTipoA   │     │ ProcessarGenerico│
        │  (Pass State)    │     │   (Pass State)    │
        └─────────┬────────┘     └────────┬─────────┘
                  │                        │
                  ▼                        ▼
        ┌──────────────────┐     ┌──────────────────┐
        │    SUCCEEDED     │     │    SUCCEEDED     │
        │ "Processamento   │     │ "Processamento   │
        │  especial..."    │     │  genérico"        │
        └──────────────────┘     └──────────────────┘


                       EXCEÇÃO
                      (tipo="erro")
                           │
                           ▼
               ┌────────────────────────┐
               │         Catch           │
               │   (ErroTratado state)   │
               └──────────────┬─────────┘
                              ▼
                    ┌──────────────────┐
                    │    SUCCEEDED     │
                    │"Ocorreu um erro  │
                    │ e foi tratado"   │
                    └──────────────────┘
