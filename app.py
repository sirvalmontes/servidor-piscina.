from flask import Flask, request, jsonify
import json
import os
import time
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# ================= CONFIG FIREBASE (VIA RENDER) =================
# Lógica corrigida para usar a variável de ambiente que você preencheu
firebase_json = os.environ.get("FIREBASE_CHAVE_JSON")

if firebase_json:
    try:
        # Se o Firebase ainda não foi iniciado, inicia agora
        if not firebase_admin._apps:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✔ Firebase inicializado com sucesso via Render!")
    except Exception as e:
        print(f"✖ Erro ao processar chave do Firebase: {e}")
else:
    print("✖ Erro: Variável FIREBASE_CHAVE_JSON não encontrada no Render!")

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
            topic="piscina", # Deve ser o mesmo tópico que você colocou no Flutter
        )
        response = messaging.send(message)
        print("✔ Notificação enviada com sucesso:", response)
    except Exception as e:
        print("✖ Erro fatal ao enviar notificação:", e)

# ================= CARREGAR / SALVAR ESTADO =================
def carregar_estado():
    if not os.path.exists(ARQ):
        return {
            "nivel": "BAIXO",
            "bomba": "OFF",
            "alerta": "NORMAL",
            "ultimo_update": time.time()
        }
    try:
        with open(ARQ, "r") as f:
            return json.load(f)
    except:
        return {"nivel": "BAIXO", "bomba": "OFF", "alerta": "NORMAL", "ultimo_update": time.time()}

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

# ================= ROTA DE STATUS (USADA PELO ESP32 E CELULAR) =================
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

            # LÓGICA DE ALERTA
            if novo_nivel in ["ALTO", "CHEIO"]:
                estado["alerta"] = "CHEIO"
                estado["bomba"] = "OFF" # Segurança: desliga se encher
                
                # SÓ ENVIA NOTIFICAÇÃO SE O NÍVEL MUDOU PARA EVITAR SPAM
                if nivel_antigo != novo_nivel:
                    enviar_notificacao_push(
                        "🚨 Alerta de Piscina!", 
                        f"O nível está {novo_nivel}. A bomba foi bloqueada por segurança."
                    )
            else:
                estado["alerta"] = "NORMAL"

            salvar_estado(estado)

    estado = verificar_esp(estado)
    return jsonify(estado)

# ================= ROTA DE COMANDO (BOTAO DO APP) =================
@app.route("/comando", methods=["POST"])
def comando():
    estado = carregar_estado()
    estado = verificar_esp(estado)
    data = request.json or {}
    acao = data.get("acao")

    if acao == "LIGAR":
        # Só deixa ligar se não estiver cheio
        if estado["nivel"] not in ["ALTO", "CHEIO"]:
            estado["bomba"] = "ON"
        else:
            return jsonify({"erro": "Piscina cheia!"}), 400
            
    elif acao == "DESLIGAR":
        estado["bomba"] = "OFF"
        
    elif acao == "CIENTE":
        estado["alerta"] = "NORMAL"

    salvar_estado(estado)
    return jsonify(estado)

# ================= INICIALIZAÇÃO =================
if __name__ == "__main__":
    # O Render usa a porta 3000 por padrão em muitos casos ou via env
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
