🎓 Simulando um Glue Job usando Lambda + Step Functions

🧠 Objetivo

Criar um fluxo idêntico ao real:

```
S3 → LambdaDisparadora → Step Functions → “Glue Job” (simulado com Lambda) → Final
```

> Observação: *basta alterar 1 linha do Step Functions para usar Glue real.*

📌 VISÃO GERAL DO QUE VAMOS CONSTRUIR

Chamadas equivalentes:

| Ambiente Dev / LocalStack | Produção AWS                        |
| ------------------------- | ----------------------------------- |
| LambdaSimulaGlue          | Glue Job real                       |
| `arn:aws:lambda:...`      | `arn:aws:states:::glue:startJobRun` |
| Polling feito em Lambda   | Glue Job Status API                 |
| Delay artificial          | Execução real do Glue               |

🟦 PASSO 1 — Criar a Lambda que simula o Glue Job

Essa Lambda vai:

* receber parâmetros

* simular uma execução demorada

* devolver STATUS

* às vezes falhar (para testarmos o CATCH)

Vamos criar **2 Lambdas**:

1. IniciarJobSimulado → inicia a execução e devolve um jobRunId

2. VerificarStatusJobSimulado → retorna SUCCEEDED, RUNNING ou FAILED

📁 Estrutura de pastas

```bash
/projeto_final
  |- iniciar_job/
  |    |- app.py
  |
  |- verificar_job/
       |- app.py
```
🟩 PASSO 2 — Código da Lambda “IniciarJobSimulado”

Crie iniciar_job/app.py

```python
import json
import uuid
import random

def handler(event, context):
    # Simula parametros da chamada de um glue job
    job_name = event.get("jobName", "JobSimulado")
    args = event.get("arguments", {})

    # Geramos um ID único para a simulação do Glue Job
    job_run_id = str(uuid.uuid4())

    # Vamos registrar (em memória local) o status inicial "RUNNING"
    # Simples dicionário para testes locais
    status = {
        "jobRunId": job_run_id,
        "jobName": job_name,
        "status": "RUNNING",
        "progress": 0,
        "arguments": args
    }

    # Salvamos o status em um arquivo local (funciona no LocalStack)
    with open(f"/tmp/{job_run_id}.json", "w") as f:
        json.dump(status, f)

    return {
        "jobRunId": job_run_id,
        "message": "Job simulado iniciado com sucesso"
    }
```

🟧 PASSO 3 — Código da Lambda “VerificarStatusJobSimulado”

Crie verificar_job/app.py

```python
import json
import os
import random
import time

def handler(event, context):
    job_run_id = event.get("jobRunId")

    if not job_run_id:
        raise Exception("jobRunId não informado!")

    file_path = f"/tmp/{job_run_id}.json"

    if not os.path.exists(file_path):
        raise Exception("Job não encontrado (simulação).")

    with open(file_path, "r") as f:
        status = json.load(f)

    # Simula progresso
    status["progress"] += random.randint(20, 50)

    # 20% de chance de falha para testar Catch
    if random.random() < 0.2:
        status["status"] = "FAILED"
    elif status["progress"] >= 100:
        status["status"] = "SUCCEEDED"
    else:
        status["status"] = "RUNNING"

    # Grava atualização
    with open(file_path, "w") as f:
        json.dump(status, f)

    return status
```

🟨 PASSO 4 — Zipar e subir as Lambdas

Iniciar Job

```bash
cd iniciar_job
zip iniciar_job.zip app.py

aws lambda create-function \
  --endpoint-url http://localhost:4566 \
  --region us-east-1 \
  --function-name IniciarJobSimulado \
  --runtime python3.10 \
  --handler app.handler \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --zip-file fileb://iniciar_job.zip
```

Verificar Job

```bash
cd ../verificar_job
zip verificar_job.zip app.py

aws lambda create-function \
  --endpoint-url http://localhost:4566 \
  --region us-east-1 \
  --function-name VerificarJobSimulado \
  --runtime python3.10 \
  --handler app.handler \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --zip-file fileb://verificar_job.zip
```

🟦 PASSO 5 — Criar Step Functions para orquestrar o “Glue”

Aqui vai o State Machine REAL, simulando Glue:

```json
{
  "Comment": "Simulação de Glue usando Lambda",
  "StartAt": "IniciarJob",
  "States": {
    "IniciarJob": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:IniciarJobSimulado",
      "Next": "Aguardar5s"
    },

    "Aguardar5s": {
      "Type": "Wait",
      "Seconds": 5,
      "Next": "VerificarProgresso"
    },

    "VerificarProgresso": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:000000000000:function:VerificarJobSimulado",
      "Next": "DecisaoStatus"
    },

    "DecisaoStatus": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.status",
          "StringEquals": "RUNNING",
          "Next": "Aguardar5s"
        },
        {
          "Variable": "$.status",
          "StringEquals": "FAILED",
          "Next": "JobFalhou"
        }
      ],
      "Default": "JobConcluido"
    },

    "JobConcluido": {
      "Type": "Succeed"
    },

    "JobFalhou": {
      "Type": "Fail",
      "Cause": "JobSimuladoFalhou"
    }
  }
}
```

🟩 PASSO 6 — Criar state machine

```bash
aws stepfunctions create-state-machine \
  --endpoint-url http://localhost:4566 \
  --region us-east-1 \
  --name GlueSimuladoStateMachine \
  --role-arn arn:aws:iam::000000000000:role/step-functions \
  --definition file://statemachine.json
```

🟦 PASSO 7 — Testar execução 🎉

```bash
aws stepfunctions start-execution \
  --endpoint-url http://localhost:4566 \
  --region us-east-1 \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:GlueSimuladoStateMachine \
  --input '{"jobName":"ProcessaCSV","arguments":{"arquivo":"dados.csv"}}'
```

Acompanhe:
```bash
aws stepfunctions describe-execution ...
aws stepfunctions get-execution-history ...
```

🎉 PRONTO!

Você acabou de construir:

✔️ Uma simulação COMPLETA de Glue
✔️ Com duas Lambdas
✔️ Orquestração realista
✔️ Polling
✔️ Retry
✔️ Status RUNNING / FAILED / SUCCEEDED
✔️ Comportamento idêntico ao Glue de verdade
✔️ 100% funcional no LocalStack Free
✔️ Migrável para AWS com uma alteração de uma linha:

Trocar:
```json
"Resource": "arn:aws:lambda:...IniciarJobSimulado"
```
por:
```json
"Resource": "arn:aws:states:::glue:startJobRun"
```

e no polling:
```json
"Resource": "arn:aws:lambda:...VerificarJobSimulado"
```
por:
```json
"Resource": "arn:aws:states:::glue:getJobRun"

🔥 DIAGRAMA COMPLETO

```bash
                                      ┌───────────────────────┐
                                      │        INÍCIO         │
                                      └─────────────┬─────────┘
                                                    │
                                                    ▼
                                 ┌──────────────────────────────────┐
                                 │         IniciarJob (Lambda)      │
                                 │  - Gera jobRunId                  │
                                 │  - Salva status RUNNING no /tmp   │
                                 │  - Retorna jobRunId ao SFN        │
                                 └──────────────────────┬───────────┘
                                                        │
                                                        ▼
                                          ┌──────────────────────────┐
                                          │        Wait 5 segundos   │
                                          └──────────────┬───────────┘
                                                         │
                                                         ▼
                                 ┌──────────────────────────────────────┐
                                 │   VerificarProgresso (Lambda)       │
                                 │  - Lê arquivo /tmp/<jobRunId>.json  │
                                 │  - Incrementa progresso             │
                                 │  - Decide RUNNING / FAILED / SUCC.  │
                                 │  - Atualiza arquivo /tmp            │
                                 └───────────────────────┬────────────┘
                                                         │
                                                         ▼
                                      ┌────────────────────────────────┐
                                      │             Choice             │
                                      │     status == "RUNNING"?       │
                                      ├────────────────┬───────────────┤
                                      │                │               │
                                      │ SIM            │ status=FAILED │
                                      │                │               │
                                      ▼                ▼               ▼
                ┌─────────────────────────────┐   ┌────────────────┐   ┌───────────────────────────┐
                │   Volta p/ Wait 5 segundos   │   │    JobFalhou   │   │        JobConcluido       │
                │  (loop até SUCCEEDED/FAILED) │   │   (Fail State) │   │        (Succeed State)    │
                └─────────────────────────────┘   └────────────────┘   └───────────────────────────┘
