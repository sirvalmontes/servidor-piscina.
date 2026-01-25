from flask import Flask, jsonify, request

app = Flask(__name__)

memoria = {"nivel": "OK", "bomba": "OFF", "alerta": "NORMAL"}

@app.route('/')
def pagina_inicial():
    return "SERVIDOR RODANDO"

@app.route('/status')
def ver_status():
    return jsonify(memoria)

@app.route('/comando', methods=['POST'])
def receber_comando():
    return jsonify({"status": "recebido"})
