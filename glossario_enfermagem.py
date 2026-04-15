import re
import json
from bs4 import BeautifulSoup

# --- 1. LEITURA E PRÉ-PROCESSAMENTO ---
with open("data/glossario_enfermagem.xml", "r", encoding="utf8") as f:
    conteudo = f.read()

# O BeautifulSoup lida bem com DOCTYPE, mas mantemos a limpeza por segurança
conteudo = re.sub(r'<!DOCTYPE[^>]*>', '', conteudo)
soup = BeautifulSoup(conteudo, "xml")

# --- 2. IDENTIFICAÇÃO DAS FONTES ---
# Encontrar todos os elementos <text>
todos_textos = soup.find_all('text')

# --- 3. PARSING PRINCIPAL ---
glossario = {}
termo_atual = None
desc_partes = []

FONT_TERMO = "49"
FONT_DESC  = "21"
FONT_FONTE_LABEL = "50"
FONT_FONTE_REF   = "51"

def guardar_termo():
    if termo_atual and desc_partes:
        desc = ' '.join(desc_partes).strip()
        desc = re.sub(r'\s+', ' ', desc)
        glossario[termo_atual] = desc

for elem in todos_textos:
    font = elem.get('font', '')
    # O .get_text() do BS4 já extrai texto de tags filhas (<b>, <i>) automaticamente
    texto = elem.get_text(strip=True)
    
    if not texto:
        continue

    if font == FONT_TERMO:
        guardar_termo()
        termo_atual = texto
        desc_partes = []

    elif font == FONT_DESC and termo_atual:
        desc_partes.append(texto)

    elif font in (FONT_FONTE_LABEL, FONT_FONTE_REF):
        pass

# Guardar o último termo processado
guardar_termo()

# --- 4. EXPORTAÇÃO ---
output_path = "glossario_enfermagem_final.json"
with open(output_path, "w", encoding="utf8") as f:
    json.dump(glossario, f, indent=4, ensure_ascii=False)

print(f"Concluído! {len(glossario)} termos exportados para '{output_path}'.")