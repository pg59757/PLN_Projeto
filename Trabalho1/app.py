from flask import Flask, render_template, redirect, url_for, request
import json
import re

app = Flask(__name__)

# Função para carregar os dados com segurança
def carregar_dados():
    try:
        with open("dicionario_unificado.json", "r", encoding="utf-8") as f:
            conteudo = json.load(f)
            return conteudo.get("Vocabulário médico", [])
    except Exception as e:
        print(f"Erro ao ler o ficheiro: {e}")
        return []

db_conceitos = carregar_dados()

@app.route("/")
def home():
    return render_template("home.html")

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


    return render_template("conceito.html", conceito=item)

@app.route("/pesquisar", methods=["GET", "POST"])
def pesquisar_conceitos():
    if request.method == "GET":
        return render_template("pesquisar.html", resultados=[], query=None)

    palavra = request.form.get('palavra', '').strip()

    if not palavra:
        return render_template("pesquisar.html", resultados=[], query=palavra)

    def match_exato(texto):
        return str(texto).strip().lower() == palavra.lower() if texto else False

    resultados = []
    for item in db_conceitos:
        termo_galego = item.get('termo_galego', {})
        palavra_original = termo_galego.get('palavra', '')
        traducoes = item.get('traducoes', {})
        sinonimos = termo_galego.get('sinonimos_galego', [])

        campos = [palavra_original] + list(traducoes.values()) + (sinonimos if isinstance(sinonimos, list) else [])

        if any(match_exato(c) for c in campos):
            resultados.append({
                'palavra_original': palavra_original,
                'palavra': palavra_original,
                'genero': termo_galego.get('genero_palavra'),
                'tema': item.get('tema', []),
                'traducoes': traducoes,
            })

    return render_template("pesquisar.html", resultados=resultados, query=palavra)

if __name__ == "__main__":
    app.run(host="localhost", port=4003, debug=True)