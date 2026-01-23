from flask import Flask, request, jsonify

app = Flask(__name__)

# Memória temporária para guardar os dados da piscina
status_piscina = {"nivel": "Buscando...", "bomba": "OFF", "alerta": "NORMAL"}
comando_pendente = "NENHUM"

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(status_piscina)

@app.route('/status', methods=['POST'])
def post_status():
    global status_piscina
    status_piscina = request.json
    return "OK", 200

@app.route('/comando', methods=['POST'])
def post_comando():
    global comando_pendente
    data = request.json
    comando_pendente = data.get("acao", "NENHUM")
    return jsonify({"status": "OK"})

@app.route('/comando', methods=['GET'])
def get_comando():
    global comando_pendente
    temp = comando_pendente
    comando_pendente = "NENHUM"
    return temp

@app.route('/')
def home():
    return "Servidor da Piscina Sirval Online"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
