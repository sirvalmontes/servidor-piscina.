from flask import Flask, request, jsonify
import json
import os
import time
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# ================= CONFIG FIREBASE =================
firebase_json = os.environ.get("FIREBASE_KEY_JSON")  # variável do Render
if firebase_json:
    cred_dict = json.loads(firebase_json)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    print("✔ Firebase inicializado com sucesso via variável de ambiente!")
else:
    print("✖ Erro: variável FIREBASE_KEY_JSON não encontrada!")

ARQ = "estado.json"

def enviar_notificacao_push(titulo, corpo):
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=corpo),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='piscina_channel',
                    sound='default',
                ),
            ),
            topic="piscina",
        )
        response = messaging.send(message)
        print("✔ Notificação enviada:", response)
    except Exception as e:
        print("✖ Erro ao enviar notificação:", e)

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
            nivel_antigo = estado.get("nivel")
            estado["nivel"] = novo_nivel
            estado["ultimo_update"] = time.time()

            if novo_nivel in ["ALTO", "CHEIO"]:
                estado["alerta"] = "CHEIO"
                estado["bomba"] = "OFF"
                if nivel_antigo != novo_nivel:
                    enviar_notificacao_push("🚨 PISCINA CHEIA!", f"Nível: {novo_nivel}. Bomba desligada.")
            else:
                estado["alerta"] = "NORMAL"
            salvar_estado(estado)
    return jsonify(estado)

@app.route("/comando", methods=["POST"])
def comando():
    estado = carregar_estado()
    acao = (request.json or {}).get("acao")
    if acao == "LIGAR":
        if estado["nivel"] not in ["ALTO", "CHEIO"]:
            estado["bomba"] = "ON"
    elif acao == "DESLIGAR":
        estado["bomba"] = "OFF"
    elif acao == "CIENTE":
        estado["alerta"] = "NORMAL"
    salvar_estado(estado)
    return jsonify(estado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
