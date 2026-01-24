from flask import Flask, request, jsonify

app = Flask(__name__)

# Memória para os dados
dados = {"nivel": "BAIXO", "bomba": "OFF", "alerta": "NORMAL"}
comando = "NENHUM"

@app.route('/')
def home():
    return "Servidor Piscina Sirval Ativo"

@app.route('/status', methods=['GET', 'POST'])
def handle_status():
    global dados
    if request.method == 'POST':
        novo_status = request.json
        if novo_status:
            dados.update(novo_status)
        return "OK", 200
    return jsonify(dados)

@app.route('/comando', methods=['GET', 'POST'])
def handle_comando():
    global comando
    if request.method == 'POST':
        cmd_recebido = request.json
        comando = cmd_recebido.get("acao", "NENHUM")
        return jsonify({"status": "OK"})
    
    # Quando o ESP32 ler o comando, ele volta para NENHUM
    temp = comando
    comando = "NENHUM"
    return jsonify({"comando": temp})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
