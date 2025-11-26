import json

def handler(event, context):
    mensagem = event.get("mensagem", "Olá do Lambda dentro do Step Functions!")
    return {
        "statusCode": 200,
        "body": json.dumps({"msg": mensagem})
    }
