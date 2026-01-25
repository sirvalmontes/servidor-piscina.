from flask import Flask, request, jsonify

app = Flask(__name__)

# Dados salvos na memória (sem Firebase por enquanto)
dados_piscina = {
    "nivel": "BAIXO",
    "bomba": "OFF",
    "alerta": "NORMAL",
    "comando": "NENHUM"
}

@app.route('/')
def home():
    return "Servidor Piscina Sirval - MODO TESTE ATIVO"

@app.route('/status', methods=['GET', 'POST'])
def handle_status():
    global dados_piscina
    if request.method == 'POST':
        recebido = request.get_json()
        if recebido:
            dados_piscina.update(recebido)
        return "OK", 200
    return jsonify(dados_piscina)

@app.route('/comando', methods=['GET', 'POST'])
def handle_comando():
    global dados_piscina
    if request.method == 'POST':
        cmd = request.get_json()
        dados_piscina["comando"] = cmd.get("acao", "NENHUM")
        return jsonify({"status": "OK"})
    
    # ESP32 lê o comando e ele volta para NENHUM
    temp = dados_piscina["comando"]
    dados_piscina["comando"] = "NENHUM"
    return jsonify({"comando": temp})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
