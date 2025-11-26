import json

def handler(event, context):
    # Se o event for STRING, transformar em JSON
    if isinstance(event, str):
        try:
            event = json.loads(event)
        except:
            pass

    tipo = event.get("tipo")

    if tipo == "erro":
        raise Exception("Erro forçado pela entrada!")

    return {
        "mensagem": "Processamento OK",
        "tipo": tipo
    }
