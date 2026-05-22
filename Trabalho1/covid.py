import re
import json

# Função auxiliar de limpeza das traduções
# remove a classe gramatica do termo
def limpar_traducao(t):
    t = re.sub(r'\s+(?:n\s*[mf]?|adj|adv)(?:\s*;.*)?$', '', t.strip())
    return t.replace(";", "").strip()

# Função auxiliar de extração das traduções
# Para cada bloco de um termo são extraídas e limpas as traduções
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



# Passo 1: Leitura do ficheiro
with open("data/dicionario_covid.txt", "r", encoding="utf8") as f:
        texto = f.read()

# Passo 2: Limpeza de estrutura do PDF
texto = re.sub(r'\f', '', texto)
texto = re.sub(r'\nQUADERNS.*?\n', '\n', texto)
texto = re.sub(r'\n[A-Z]\n', '\n', texto) 
texto = re.sub(r'\n\d{1,3}\n', '\n', texto)
texto = re.sub(r'\n{2,}', '\n', texto)

# Passo 3: Configuração de línguas para as traduções
LINGUAS = [
    ('pt [PT]', 'português (PT)'),
    ('pt [BR]', 'português (BR)'),
    ('pt', 'português'),
    ('oc', 'occitan'),
    ('eu', 'euskera'),
    ('gl', 'galego'),
    ('es', 'espanhol'),
    ('en', 'inglês'),
    ('fr', 'francês'),
    ('nl', 'holandês')
]

# Passo 4: Divisão do texto em blocos, cada bloco contém um termo
# A divisão é feita através do indice númerico
blocos = re.split(r'\n(?=\d+\s+[A-ZÀ-Úa-zà-ú])', texto)


dicionario = {}

#Passo 5: Extração da informação de cada bloco
for bloco in blocos:
    bloco = bloco.strip()
    if not bloco: continue
    
    #divisão do termo 
    linhas = bloco.split('\n')
    #isola a linha que contém o indice númerico, o termo e a classe gramatical
    primeira_linha = linhas[0] 
    
    #separa o indice númerico do conjunto termo - classe gramatical
    partes_topo = primeira_linha.split(maxsplit=1)
    if len(partes_topo) < 2: continue
    
    id_numero = partes_topo[0]
    termo_catalao_bruto = partes_topo[1]

    # remove a classe gramatica do termo
    termo_catalao = re.sub(r'\s+n\s*[mf]?\s*$', '', termo_catalao_bruto).strip()
    
    #ignora entradas de redirecinamento
    if 'veg.' in bloco:
        continue

    categoria, definicao = None, None
    #Lista das categorias existentes
    tags_categorias = ['CONCEPTES GENERALS.','EPIDEMIOLOGIA.', 'ETIOPATOGÈNIA.', 'CLÍNICA.', 'PREVENCIÓ.', 'TRACTAMENT.', 'PRINCIPIS ACTIUS.', 'ENTORN SOCIAL.']
    
    for tag in tags_categorias:
        if tag in bloco:
            categoria = tag
            parte_pos_categoria = bloco.split(tag)[1]
            defn_limpa = parte_pos_categoria.split("Nota:")[0].split("\n\n")[0]
            #separa a definição das notas
            definicao = defn_limpa.replace("\n", " ").strip()
            break

    #cria o bloco do termo
    dicionario[termo_catalao] = {
        "id": int(id_numero) if id_numero.isdigit() else 0,
        "termo_catalao": termo_catalao,
        "traducoes": extrair_traducoes(bloco)
    }
    #inclui a categoria e a definição
    if categoria:
        dicionario[termo_catalao]["categoria"] = categoria
        dicionario[termo_catalao]["definicao"] = definicao

# Passo 5: Criação do ficheiro JSON com a informação
f_out="dicionario_covid.json"
with open(f_out, "w", encoding="utf8") as f:
    json.dump(dicionario, f, indent=4, ensure_ascii=False)

print(f"Concluído. Termos guardados em {f_out}.")