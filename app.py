from flask import Flask, jsonify, request

app = Flask(__name__)   # 👈 TEM que vir ANTES das rotas

memoria = {
    "nivel": "OK",
    "bomba": "OFF",
    "alerta": "NORMAL"
}

@app.route('/')
def pagina_inicial():
    return "SERVIDOR RODANDO"

@app.route('/status', methods=['GET'])
def ver_status():
    return jsonify(memoria)

@app.route('/comando', methods=['POST'])
def receber_comando():
    dados = request.json or {}

    if "nivel" in dados:
        memoria["nivel"] = dados["nivel"]

    if "bomba" in dados:
        memoria["bomba"] = dados["bomba"]

    if "alerta" in dados:
        memoria["alerta"] = dados["alerta"]

    return jsonify(memoria)
