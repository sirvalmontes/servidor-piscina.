from flask import Flask, request, jsonify
import json
import os
import time
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# CONFIG FIREBASE
firebase_json = os.environ.get("FIREBASE_CHAVE_JSON")
if firebase_json:
    try:
        if not firebase_admin._apps:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✔ Firebase OK!")
    except Exception as e:
        print(f"✖ Erro Firebase: {e}")

ARQ = "estado.json"

def enviar_notificacao_push(titulo, corpo):
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=corpo),
            topic="piscina",
        )
        messaging.send(message)
        print("✔ Enviada!")
    except Exception as e:
        print(f"✖ Erro Push: {e}")

def carregar_estado():
    if not os.path.exists(ARQ):
        return {"nivel": "BAIXO", "bomba": "OFF", "alerta": "NORMAL", "ultimo_update": time.time()}
    with open(ARQ, "r") as f:
        return json.load(f)

def salvar_estado(estado):
    with open(ARQ, "w") as f:
        json.dump(estado, f)

@app.route("/status", methods=["GET", "POST"])
def status():
    estado = carregar_estado()
    if request.method == "POST":
        data = request.json or {}
        if "nivel" in data:
            novo_nivel = data["nivel"].upper()
            estado["nivel"] = novo_nivel
            estado["ultimo_update"] = time.time()
            
            if novo_nivel in ["ALTO", "CHEIO"]:
                if estado.get("alerta") != "NORMAL":
                    estado["alerta"] = "CHEIO"
                    estado["bomba"] = "OFF"
                    enviar_notificacao_push("🚨 PISCINA CHEIA!", f"Nível: {novo_nivel}")
            else:
                estado["alerta"] = "NORMAL"
            salvar_estado(estado)
    return jsonify(estado)

@app.route("/comando", methods=["POST"])
def comando():
    estado = carregar_estado()
    acao = (request.json or {}).get("acao")
    if acao == "LIGAR" and estado["nivel"] not in ["ALTO", "CHEIO"]:
        estado["bomba"] = "ON"
    elif acao == "DESLIGAR":
        estado["bomba"] = "OFF"
    elif acao == "CIENTE":
        estado["alerta"] = "NORMAL"
    salvar_estado(estado)
    return jsonify(estado)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
