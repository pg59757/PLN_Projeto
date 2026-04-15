from bs4 import BeautifulSoup
import json
import re

def parser_medicina_v3(xml_path, json_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
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
        
        # 2. DETETAR REFERÊNCIA ISOLADA (Ex: "aberración cromosómica Vid.- ...")
        # Se o texto contém Vid.- mas NÃO começa por números
        is_vid = "Vid.-" in texto

        if fonte == '3' and match_id:
            # Guarda a anterior antes de começar
            if entrada_atual: vocabulario.append(entrada_atual)
            
            entrada_atual = {
                "tipo_entrada": "definicao_completa",
                "id_entrada": int(match_id.group(1)),
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

        elif is_vid:
            # Se encontrarmos um Vid.-, ele deve ser uma nova entrada de referência
            # Primeiro guardamos a que estava aberta
            if entrada_atual:
                vocabulario.append(entrada_atual)
            
            # Criamos a entrada de reencaminhamento
            # Tentamos separar o termo do "Vid.-"
            partes = texto.split("Vid.-")
            termo_referencia = partes[0].strip()
            destino = "Vid.-" + partes[1]

            entrada_atual = {
                "tipo_entrada": "referencia",
                "id_entrada": None,
                "termo_galego": {
                    "palavra": termo_referencia,
                    "genero_palavra": None,
                    "sinonimos_galego": []
                },
                "tema": [destino],
                "traducoes": {},
                "nota": None
            }
            # Após criar a referência, "fechamos" logo para não misturar com as traduções seguintes
            vocabulario.append(entrada_atual)
            entrada_atual = None 
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

    # Limpeza final: remover entradas de referência que ficaram vazias ou duplicadas
    vocabulario = [e for e in vocabulario if e["termo_galego"]["palavra"] or e["id_entrada"]]

    resultado = {"Vocabulário médico": vocabulario}

    with open(json_path, 'w', encoding='utf-8') as f_json:
        json.dump(resultado, f_json, indent=4, ensure_ascii=False)

    print(f"Feito! O Vid.- agora gera uma entrada separada.")

if __name__ == "__main__":
    parser_medicina_v3('pdfs/medicina.xml', 'medicina.json')