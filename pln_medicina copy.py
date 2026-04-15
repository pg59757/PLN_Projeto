from bs4 import BeautifulSoup
import json
import re

def medicina_xml(f_in, f_out):
    with open(f_in, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'xml')

    vocabulario = []
    entrada_atual = None
    lingua_ativa = None

    mapa_linguas = {"es": "espanhol", "en": "inglês", "pt": "português", "la": "latim"}

    tags = soup.find_all('text')

    for tag in tags:
        texto = tag.get_text().strip()
        if not texto: continue
        
        fonte = tag.get('font')
        
        # 1. DETETAR ENTRADA NUMÉRICA (Ex: 4 abdome agudo m)
        match_id = re.match(r'^(\d+)\s+(.+?)\s+([fma])$', texto)

        if fonte == '3' and match_id:
            # Guarda a anterior antes de começar
            if entrada_atual: 
                vocabulario.append(entrada_atual)
            
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

        elif entrada_atual:
            # 3. TRATAR TEMAS (Font 6)
            if fonte == '6':
                entrada_atual["tema"].append(texto)
            
            # 4. TRATAR SINÓNIMOS
            elif texto.startswith("SIN.-"):
                conteudo = texto.replace("SIN.-", "").strip()
                entrada_atual["termo_galego"]["sinonimos_galego"] = [s.strip() for s in conteudo.split(';')] if conteudo else []

            # 5. TRATAR NOTAS
            elif texto.startswith("Nota.-"):
                entrada_atual["nota"] = texto.replace("Nota.-", "").strip()

            # 6. TRATAR TRADUÇÕES
            elif texto in mapa_linguas:
                lingua_ativa = mapa_linguas[texto]
            
            elif lingua_ativa and (fonte == '7' or fonte == '0'):
                if entrada_atual["traducoes"].get(lingua_ativa):
                    entrada_atual["traducoes"][lingua_ativa] += " " + texto
                else:
                    entrada_atual["traducoes"][lingua_ativa] = texto

    # Adicionar a última se ainda existir
    if entrada_atual:
        vocabulario.append(entrada_atual)

    resultado = {"Vocabulário médico": vocabulario}

    with open(f_out, 'w', encoding='utf-8') as f_json:
        json.dump(resultado, f_json, indent=4, ensure_ascii=False)

    print(f"Json {f_out} gerado com sucesso")

medicina_xml('data/medicina.xml', 'medicina2.json')