import json
import uuid
import os

def handler(event, context):
    # Pega o jobName recebido (aceita qualquer nome)
    job_name = event.get("jobName", "JOB_DESCONHECIDO")

    # Gera ID único simulando Glue JobRunId
    job_run_id = str(uuid.uuid4())

    # Caminho do arquivo que simula o status do Glue
    status_path = f"/tmp/{job_run_id}.json"

    # Estado inicial
    data = {
        "jobName": job_name,
        "status": "RUNNING",
        "progress": 0
    }

    # Salva o estado em /tmp (persistente durante a execução do container localstack)
    with open(status_path, "w") as f:
        json.dump(data, f)

    # Retorno que o Step Functions espera
    return {
        "jobRunId": job_run_id,
        "status": "RUNNING"
    }
