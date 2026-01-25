from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

ARQ = "estado.json"

def carregar_estado():
    if not os.path.exists(ARQ):
        return {
            "nivel": "BAIXO",
            "bomba": "OFF",
            "alerta": "NORMAL"
        }
    with open(ARQ, "r") as f:
        return json.load(f)

def salvar_estado(estado):
    with open(ARQ, "w") as f:
        json.dump(estado, f)

# ===== STATUS =====
@app.route("/status", methods=["GET", "POST"])
def status():
    estado = carregar_estado()

    if request.method == "POST":
        data = request.json or {}
        if "nivel" in data:
            estado["nivel"] = data["nivel"]
            salvar_estado(estado)

    return jsonify(estado)

# ===== COMANDO =====
@app.route("/comando", methods=["POST"])
def comando():
    estado = carregar_estado()
    data = request.json or {}

    acao = data.get("acao")

    if acao == "LIGAR":
        estado["bomba"] = "ON"
    elif acao == "DESLIGAR":
        estado["bomba"] = "OFF"
    elif acao == "CIENTE":
        estado["alerta"] = "NORMAL"

    salvar_estado(estado)
    return jsonify(estado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
