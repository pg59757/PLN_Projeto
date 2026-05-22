import re
import json
from bs4 import BeautifulSoup

# Passo 1: Leitura do ficheiro
with open("data/glossario_enfermagem.xml", "r", encoding="utf8") as f:
    conteudo = f.read()

# Passo 2: Limpeza de estrutura do PDF
conteudo = re.sub(r'<!DOCTYPE[^>]*>', '', conteudo)
soup = BeautifulSoup(conteudo, "xml")

# Passo 3: Identificação dos diferentes elemnntos
# Encontrar todos os elementos <text>
todos_textos = soup.find_all('text')

# Identificação da fonte de cada elemento
glossario = {}
termo_atual = None
desc_partes = []

FONT_TERMO = "49"
FONT_DESC  = "21"
FONT_FONTE_LABEL = "50"
FONT_FONTE_REF   = "51"

# Função auxiliar de extração dos termos
def guardar_termo():
    if termo_atual and desc_partes:
        #une todas as linhas da descrição e deixa apenas 1 espaço entre elas
        desc = ' '.join(desc_partes).strip()
        desc = re.sub(r'\s+', ' ', desc)
        glossario[termo_atual] = desc

#procura todos os elementos
for elem in todos_textos:
    font = elem.get('font', '')
    texto = elem.get_text(strip=True)
    
    if not texto:
        continue

    #se for um termo guarda o anterior e começa um novo
    if font == FONT_TERMO:
        guardar_termo()
        termo_atual = texto
        desc_partes = []
    
    #Se for uma descrição e existir um termo atual, adiciona a descrição à desc_partes
    elif font == FONT_DESC and termo_atual:
        desc_partes.append(texto)

    #se for um label ou refencia ignora
    elif font in (FONT_FONTE_LABEL, FONT_FONTE_REF):
        pass

# Passo 4: Guarda o último termo processado
guardar_termo()

# Passo 5: Criação do ficheiro JSON com a informação
f_out = "glossario_enfermagem.json"
with open(f_out, "w", encoding="utf8") as f:
    json.dump(glossario, f, indent=4, ensure_ascii=False)

print(f"Concluído. Termos guardados em {f_out}.")