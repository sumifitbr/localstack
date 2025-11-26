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
