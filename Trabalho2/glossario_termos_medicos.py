import re
import json
from bs4 import BeautifulSoup

# Passo 1: Leitura do ficheiro
with open("data/glossario_termos_medicos.xml", "r", encoding="utf8") as f:
    conteudo = f.read()

# Passo 2: Limpeza de estrutura do PDF
conteudo = re.sub(r'<!DOCTYPE[^>]*>', '', conteudo)
soup = BeautifulSoup(conteudo, "xml")

# Identificação da fonte de cada elemento
FONT_TECNICO = "1"
FONT_POPULAR = "5"

glossario = {}
termo_atual = None
termo_pop = []


# Passo 3: Extração dos termos e descrições
todos_textos = soup.find_all('text')

for elem in todos_textos:
    font = elem.get('font', '')
    texto = elem.get_text(strip=True)
    
    #se for a tag de termo popular e não o termo, ignorar
    if not texto or texto in [",", "(pop) ,", "(pop)"]:
        continue

    # Se for um termo técnico
    if font == FONT_TECNICO:
        # Guarda o anterior e começa um novo
        if termo_atual and termo_pop:
            termo_popular = ' '.join(termo_pop).strip()
            termo_popular = re.sub(r'\s+', ' ', termo_popular)
            glossario[termo_atual] = termo_popular
            
        termo_atual = texto
        termo_pop = []
        
    # Se for um termo popular
    elif font == FONT_POPULAR:
        # Adiciona ao 
        termo_pop.append(texto)

# Passo 4: Guarda o último termo processado
if termo_atual and termo_pop:
    termo_popular = ' '.join(termo_pop).strip()
    termo_popular = re.sub(r'\s+', ' ', termo_popular)
    glossario[termo_atual] = termo_popular

# Passo 5: Criação do ficheiro JSON com a informação
f_out = "glossario_termos_medicos.json"
with open(f_out, "w", encoding="utf8") as f:
    json.dump(glossario, f, indent=4, ensure_ascii=False)

print(f"Concluído. Termos guardados em {f_out}.")