from flask import Flask, render_template, redirect, url_for
import json

app = Flask(__name__)

# Função para carregar os dados com segurança
def carregar_dados():
    try:
        with open("pln_final_com_todas_linguas.json", "r", encoding="utf-8") as f:
            conteudo = json.load(f)
            return conteudo.get("Vocabulário médico", [])
    except Exception as e:
        print(f"Erro ao ler o ficheiro: {e}")
        return []

db_conceitos = carregar_dados()

@app.route("/")
def home():
    return render_template("layout.html")

@app.route("/conceitos")
def listar_conceitos():
    # 1. Extraímos apenas a string da palavra de cada entrada
    termos = []
    for item in db_conceitos:
        palavra = item.get('termo_galego', {}).get('palavra')
        if palavra:
            termos.append(palavra)
    
    # 2. Ordenamos alfabeticamente (o key=str.lower garante que 'á' ou 'A' fiquem no início)
    termos.sort(key=str.lower)
    
    return render_template("conceitos.html", lista_termos=termos)

@app.route("/conceitos/<designacao>")
def detalhe(designacao):
    # Procurar o objeto completo que corresponde à palavra clicada
    item = next((c for c in db_conceitos if c['termo_galego']['palavra'] == designacao), None)
    
    if not item:
        return "Termo não encontrado", 404

    # Lógica de redirecionamento se for um termo "alternativa"
    if item.get("tipo_entrada") == "alternativa":
        alvo = item.get("termo_equivalente")
        return redirect(url_for('detalhe', designacao=alvo))

    return render_template("conceito.html", conceito=item)

if __name__ == "__main__":
    app.run(host="localhost", port=4003, debug=True)