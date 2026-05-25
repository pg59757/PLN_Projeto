from bs4 import BeautifulSoup
import json
import re

# Passo 1: Leitura do ficheiro
with open("data/medicina.xml", 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'xml')

vocabulario = []
entrada_atual = None
lingua_ativa = None

# Mapa da abreviaturas das línguas
mapa_linguas = {"es": "espanhol", "en": "inglês", "pt": "português", "la": "latim"}

# Passo 2: Identificação dos diferentes elemnntos
tags = soup.find_all('text')

for tag in tags:
    texto = tag.get_text().strip()
    if not texto: continue
    
    fonte = tag.get('font')
    
    # Identificação os termos (formato: id_numerico + termo + género)
    #group(1) - id númerico
    #grupo(2) - termo
    #group(3) - letra do género
    match_id = re.match(r'^(\d+)\s+(.+?)\s+([fma])$', texto)

    #se for um termo 
    if fonte == '3' and match_id:
        #guarda o anterior e começa um novo
        if entrada_atual: 
            vocabulario.append(entrada_atual)
        
        #definição do formato das entradas do JSON
        entrada_atual = {
            "termo_galego": {
                "palavra": match_id.group(2).strip(),
                "genero_palavra": match_id.group(3),
                "sinonimos_galego": []
            },
            "tema": [],
            "traducoes": {"espanhol": "", "inglês": "", "português": "", "latim": ""},
            "nota": None
        }
        lingua_ativa = None

    #se for um tema 
    elif entrada_atual:
        if fonte == '6':
            entrada_atual["tema"].append(texto)
        
        #se for um sinónimo
        elif texto.startswith("SIN.-"):
            conteudo = texto.replace("SIN.-", "").strip()
            entrada_atual["termo_galego"]["sinonimos_galego"] = [s.strip() for s in conteudo.split(';')] if conteudo else []

        #se for uma nota
        elif texto.startswith("Nota.-"):
            entrada_atual["nota"] = texto.replace("Nota.-", "").strip()

        #se for uma tradução
        elif texto in mapa_linguas:
            lingua = mapa_linguas[texto]
        
        #se for uma tradução da lingua atual
        elif lingua and (fonte == '7' or fonte == '0'):
            if entrada_atual["traducoes"].get(lingua):
                entrada_atual["traducoes"][lingua] += " " + texto
            else:
                entrada_atual["traducoes"][lingua] = texto

# Passo 3: Guarda o último termo processado
if entrada_atual:
    vocabulario.append(entrada_atual)

resultado = {"Vocabulário médico": vocabulario}

# Passo 4: Criação do ficheiro JSON com a informação
f_out="medicina.json"
with open(f_out, 'w', encoding='utf-8') as f_json:
    json.dump(resultado, f_json, indent=4, ensure_ascii=False)

print(f"Concluído. Termos guardados em {f_out}.")

