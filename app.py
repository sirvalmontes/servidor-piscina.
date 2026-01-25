@app.route('/comando', methods=['POST'])
def receber_comando():
    dados = request.json

    if "nivel" in dados:
        memoria["nivel"] = dados["nivel"]

    if "bomba" in dados:
        memoria["bomba"] = dados["bomba"]

    if "alerta" in dados:
        memoria["alerta"] = dados["alerta"]

    return jsonify(memoria)
