from flask import Flask, request, jsonify
import json
import os
import time
import threading
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# ================= FIREBASE =================
firebase_json = os.environ.get("FIREBASE_KEY_JSON")
if firebase_json:
    cred_dict = json.loads(firebase_json)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    print("✔ Firebase OK")
else:
    print("✖ FIREBASE_KEY_JSON não encontrada")

ARQ = "estado.json"
TOKENS_ARQ = "tokens.json"  # onde vamos salvar os tokens dos dispositivos

# ================= FUNÇÕES PARA TOKENS =================
def carregar_tokens():
    if not os.path.exists(TOKENS_ARQ):
        return []
    with open(TOKENS_ARQ, "r") as f:
        return json.load(f)

def salvar_tokens(tokens):
    with open(TOKENS_ARQ, "w") as f:
        json.dump(tokens, f)

# ================= NOTIFICAÇÃO =================
def enviar_notificacao_push(titulo, corpo):
    try:
        tokens = carregar_tokens()
        if not tokens:
            print("✖ Nenhum token registrado")
            return

        for token in tokens:
            message = messaging.Message(
                notification=messaging.Notification(title=titulo, body=corpo),
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="piscina_channel",
                        sound="default",
                    ),
                ),
                token=token,
            )
            messaging.send(message)
        print("✔ Notificação enviada para todos os dispositivos")
    except Exception as e:
        print("✖ Erro ao enviar:", e)

# ================= ESTADO =================
def carregar_estado():
    if not os.path.exists(ARQ):
        return {
            "nivel": "BAIXO",
            "bomba": "OFF",
            "alerta": "NORMAL",
            "ciente": False,
            "ultimo_envio": 0,
            "ultimo_heartbeat": 0,
        }
    with open(ARQ, "r") as f:
        return json.load(f)

def salvar_estado(estado):
    with open(ARQ, "w") as f:
        json.dump(estado, f)

# ================= LOOP DE ALERTA =================
def loop_notificacao():
    while True:
        estado = carregar_estado()

        if estado["alerta"] == "CHEIO" and not estado["ciente"]:
            agora = time.time()

            if agora - estado["ultimo_envio"] > 10:
                enviar_notificacao_push(
                    "🚨 PISCINA CHEIA!",
                    "Clique em CIENTE no app para parar."
                )
                estado["ultimo_envio"] = agora
                salvar_estado(estado)

        time.sleep(5)

threading.Thread(target=loop_notificacao, daemon=True).start()

# ================= ROTAS =================
@app.route("/status", methods=["GET", "POST"])
def status():
    estado = carregar_estado()

    if request.method == "POST":
        data = request.json or {}
        estado["ultimo_heartbeat"] = time.time()

        if "nivel" in data:
            novo_nivel = data["nivel"].upper()
            nivel_antigo = estado["nivel"]

            estado["nivel"] = novo_nivel

            if novo_nivel in ["ALTO", "CHEIO"]:
                if nivel_antigo not in ["ALTO", "CHEIO"]:
                    estado["alerta"] = "CHEIO"
                    estado["ciente"] = False
                    estado["ultimo_envio"] = 0
                estado["bomba"] = "OFF"
            else:
                estado["alerta"] = "NORMAL"
                estado["ciente"] = False

            salvar_estado(estado)

        return jsonify(estado)

    agora = time.time()
    if agora - estado.get("ultimo_heartbeat", 0) > 30:
        return jsonify({
            "nivel": "DESCONECTADO",
            "bomba": "-",
            "alerta": "DISPOSITIVO OFFLINE"
        })

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
        estado["ciente"] = True
        print("✔ Usuário clicou CIENTE")

    salvar_estado(estado)
    return jsonify(estado)

# ================= ROTA PARA REGISTRAR TOKEN =================
@app.route("/registrar_token", methods=["POST"])
def registrar_token():
    data = request.json or {}
    token = data.get("token")
    if token:
        tokens = carregar_tokens()
        if token not in tokens:
            tokens.append(token)
            salvar_tokens(tokens)
            print("✔ Token registrado:", token)
        return jsonify({"status": "ok"})
    return jsonify({"status": "erro"}), 400

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
