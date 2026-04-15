import re
import json
from bs4 import BeautifulSoup

# --- 1. LEITURA E PRÉ-PROCESSAMENTO ---
file_path = "data/glossario_termos_medicos.xml"
with open(file_path, "r", encoding="utf8") as f:
    conteudo = f.read()

# Remoção do DOCTYPE para evitar problemas de parsing
conteudo = re.sub(r'<!DOCTYPE[^>]*>', '', conteudo)
soup = BeautifulSoup(conteudo, "xml")

# --- 2. CONFIGURAÇÃO DE FONTES ---
# Com base na análise do XML:
# Font 1 = Termo Técnico (ex: "micrograma", "perioral")
# Font 5 = Termo Popular/Descrição (ex: "a milionésima parte de um grama")
FONT_TECNICO = "1"
FONT_POPULAR = "5"

glossario = {}
termo_tecnico_atual = None
desc_partes = []

def guardar_par():
    """Guarda o par técnico-popular no dicionário."""
    global termo_tecnico_atual, desc_partes
    if termo_tecnico_atual and desc_partes:
        descricao = ' '.join(desc_partes).strip()
        descricao = re.sub(r'\s+', ' ', descricao)
        glossario[termo_tecnico_atual] = descricao
    desc_partes = []

# --- 3. PARSING DOS TEXTOS ---
todos_textos = soup.find_all('text')

for elem in todos_textos:
    font = elem.get('font', '')
    texto = elem.get_text(strip=True)
    
    if not texto or texto in [",", "(pop) ,", "(pop)"]:
        continue

    # Se encontrarmos um termo técnico (Font 1)
    if font == FONT_TECNICO:
        # Se já tínhamos um termo e descrição pendentes, guardamos
        if termo_tecnico_atual and desc_partes:
            guardar_par()
        termo_tecnico_atual = texto
        
    # Se encontrarmos uma descrição/termo popular (Font 5)
    elif font == FONT_POPULAR:
        desc_partes.append(texto)

# Guardar o último par
guardar_par()

# --- 4. EXPORTAÇÃO ---
output_path = "glossario_medico_portugal.json"
with open(output_path, "w", encoding="utf8") as f:
    json.dump(glossario, f, indent=4, ensure_ascii=False)

print(f"Sucesso! {len(glossario)} termos processados.")
print("Exemplo de output:", list(glossario.items())[:3])