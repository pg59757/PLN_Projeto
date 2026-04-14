import re
import json

# --- 1. LEITURA E LIMPEZA INICIAL ---
with open("pdfs/dicionario_covid.txt", "r", encoding="utf8") as f:
        texto = f.read()

# Limpezas básicas de estrutura do PDF
texto = re.sub(r'\f', '', texto)
texto = re.sub(r'\nQUADERNS.*?\n', '\n', texto)
texto = re.sub(r'\n[A-Z]\n', '\n', texto) 
texto = re.sub(r'\n\d{1,3}\n', '\n', texto)
texto = re.sub(r'\n{2,}', '\n', texto)

# Configuração de línguas
LINGUAS = [
    ('pt [PT]', 'português (PT)'),
    ('pt [BR]', 'português (BR)'),
    ('pt',      'português'),
    ('oc',      'occitan'),
    ('eu',      'euskera'),
    ('gl',      'galego'),
    ('es',      'espanhol'),
    ('en',      'inglês'),
    ('fr',      'francês'),
    ('nl',      'holandês')
]

def limpar_traducao(t):
    # Remove " n f", " adj", " n m", etc.
    t = re.sub(r'\s+(?:n\s*[mf]?|adj|adv)(?:\s*;.*)?$', '', t.strip())
    return t.replace(";", "").strip()

def extrair_traducoes(bloco):
    traducoes = {}
    for linha in bloco.split('\n'):
        linha = linha.strip()
        for prefixo, nome in LINGUAS:
            if linha.startswith(prefixo + " "):
                valor = linha.split(prefixo, 1)[1].strip()
                traducoes[nome] = limpar_traducao(valor)
                break
    return traducoes


blocos = re.split(r'\n(?=\d+\s+[A-ZÀ-Úa-zà-ú])', texto)

dicionario = {}
contagem = 0

for bloco in blocos:
    bloco = bloco.strip()
    if not bloco: continue
    
    linhas = bloco.split('\n')
    primeira_linha = linhas[0]
    
    partes_topo = primeira_linha.split(maxsplit=1)
    if len(partes_topo) < 2: continue
    
    id_numero = partes_topo[0]
    termo_catalao_bruto = partes_topo[1]
    
    termo_catalao = re.sub(r'\s+n\s*[mf]?\s*$', '', termo_catalao_bruto).strip()
    
    if 'veg.' in bloco:
        continue

    categoria, definicao = None, None
    tags_categorias = ['ETIOPATOGÈNIA', 'CLÍNICA', 'EPIDEMIOLOGIA', 'TRACTAMENT', 'PREVENCIÓ', 'DIAGNÒSTIC', 'FARMACOLOGIA']
    
    for tag in tags_categorias:
        if tag + "." in bloco:
            categoria = tag
            parte_pos_categoria = bloco.split(tag + ".")[1]
            defn_limpa = parte_pos_categoria.split("Nota:")[0].split("\n\n")[0]
            definicao = defn_limpa.replace("\n", " ").strip()
            break

    dicionario[termo_catalao] = {
        "id": int(id_numero) if id_numero.isdigit() else 0,
        "termo_catalao": termo_catalao,
        "traducoes": extrair_traducoes(bloco)
    }
    
    if categoria:
        dicionario[termo_catalao]["categoria"] = categoria
        dicionario[termo_catalao]["definicao"] = definicao
    
    contagem += 1

# --- 4. EXPORTAÇÃO ---
with open("dicionario_covid.json", "w", encoding="utf8") as f:
    json.dump(dicionario, f, indent=4, ensure_ascii=False)

print(f"Concluído! {contagem} termos guardados em 'dicionario_covid.json'.")