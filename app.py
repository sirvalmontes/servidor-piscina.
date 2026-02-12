from flask import Flask, request, jsonify
import json
import os
import time

app = Flask(__name__)

ARQ = "estado.json"
TIMEOUT_ESP = 30  # segundos sem atualizar = ESP desconectado


# ================= CARREGAR =================
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


# ================= SALVAR =================
def salvar_estado(estado):
    with open(ARQ, "w") as f:
        json.dump(estado, f)


# ================= VERIFICAR ESP =================
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

    # ===== RECEBE DADOS DO ESP =====
    if request.method == "POST":
        data = request.json or {}

        if "nivel" in data:
            estado["nivel"] = data["nivel"]
            estado["ultimo_update"] = time.time()

            # 🔥 LÓGICA DO ALERTA
            if data["nivel"] in ["ALTO", "CHEIO"]:
                estado["alerta"] = "CHEIO"
                estado["bomba"] = "OFF"
            else:
                estado["alerta"] = "NORMAL"

        salvar_estado(estado)

    # ===== VERIFICA SE ESP DESCONECTOU =====
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


# ================= MAIN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
