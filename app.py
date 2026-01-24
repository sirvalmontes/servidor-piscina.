from flask import Flask, request, jsonify

app = Flask(__name__)

# Memória temporária
status_piscina = {"nivel": "BAIXO", "bomba": "OFF", "alerta": "NORMAL"}
comando_pendente = "NENHUM"

@app.route('/')
def home():
    return "Servidor Piscina Sirval Ativo"

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(status_piscina)

@app.route('/status', methods=['POST'])
def post_status():
    global status_piscina
    data = request.json
    if data:
        status_piscina.update(data)
        return "OK", 200
    return "Erro", 400

@app.route('/comando', methods=['GET'])
def get_comando():
    global comando_pendente
    temp = comando_pendente
    comando_pendente = "NENHUM"
    return jsonify({"comando": temp})

@app.route('/comando', methods=['POST'])
def post_comando():
    global comando_pendente
    data = request.json
    if data and "acao" in data:
        comando_pendente = data["acao"]
        return jsonify({"status": "OK"})
    return "Erro", 400

@app.route('/notificar', methods=['POST'])
def notificar():
    # Aqui vai o código do Firebase que configuramos antes
    return "Notificado", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
