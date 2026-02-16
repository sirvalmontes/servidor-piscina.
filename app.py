meu app esta assim o py from flask import Flask, request, jsonify
import json
import os
import time
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# ================= CONFIG FIREBASE =================
# Verifica se o arquivo de chave existe antes de iniciar
if os.path.exists("firebase-key.json"):
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
    print("✔ Firebase inicializado com sucesso!")
else:
    print("✖ Erro: Arquivo firebase-key.json não encontrado!")

ARQ = "estado.json"
TIMEOUT_ESP = 30 

# ================= FUNÇÃO DE NOTIFICAÇÃO =================
def enviar_notificacao_push(titulo, corpo):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=corpo,
            ),
            topic="piscina", # Deve ser o mesmo tópico do Flutter
        )
        response = messaging.send(message)
        print("✔ Notificação enviada:", response)
    except Exception as e:
        print("✖ Erro ao enviar notificação:", e)

# ================= CARREGAR / SALVAR =================
def carregar_estado():
    if not os.path.exists(ARQ):
        return {
            "nivel": "BAIXO",
            "bomba": "OFF",
            "alerta": "NORMAL",
            "ultimo_update": time.time()
        }
    with open(ARQ, "r") as f:
        return json.load(f)

def salvar_estado(estado):
    with open(ARQ, "w") as f:
        json.dump(estado, f)

def verificar_esp(estado):
    agora = time.time()
    ultimo = estado.get("ultimo_update", 0)
    if agora - ultimo > TIMEOUT_ESP:
        estado["nivel"] = "DESCONECTADO"
        estado["alerta"] = "DESCONECTADO"
        estado["bomba"] = "OFF"
    return estado

# ================= STATUS =================
@app.route("/status", methods=["GET", "POST"])
def status():
    estado = carregar_estado()

    if request.method == "POST":
        data = request.json or {}

        if "nivel" in data:
            novo_nivel = data["nivel"]
            nivel_antigo = estado.get("nivel")
            
            estado["nivel"] = novo_nivel
            estado["ultimo_update"] = time.time()

            # 🔥 LÓGICA DO ALERTA E NOTIFICAÇÃO
            if novo_nivel in ["ALTO", "CHEIO"]:
                estado["alerta"] = "CHEIO"
                estado["bomba"] = "OFF"
                
                # SÓ ENVIA NOTIFICAÇÃO SE O NÍVEL MUDOU AGORA (para não spammar)
                if nivel_antigo != novo_nivel:
                    enviar_notificacao_push(
                        "🚨 Alerta de Piscina!", 
                        f"O nível está {novo_nivel}. A bomba foi desligada!"
                    )
            else:
                estado["alerta"] = "NORMAL"

            salvar_estado(estado)

    estado = verificar_esp(estado)
    return jsonify(estado)

# ================= COMANDO =================
@app.route("/comando", methods=["POST"])
def comando():
    estado = carregar_estado()
    estado = verificar_esp(estado)
    data = request.json or {}
    acao = data.get("acao")

    if acao == "LIGAR" and estado["nivel"] == "BAIXO":
        estado["bomba"] = "ON"
    elif acao == "DESLIGAR":
        estado["bomba"] = "OFF"
    elif acao == "CIENTE":
        estado["alerta"] = "NORMAL"

    salvar_estado(estado)
    return jsonify(estado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
