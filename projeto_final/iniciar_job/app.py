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
