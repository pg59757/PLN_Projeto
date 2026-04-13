"""Parser do Glossário de Termos Médicos Técnicos e Populares (PT)
TP1 - Processamento de Linguagem Natural - Engenharia Biomédica 2025-2026

Estratégia correcta:
  O XML do pdf2xml tem todos os elementos de uma página com o mesmo top=1248/1250.
  Cada entrada começa com left=128 e os seus fragmentos têm left crescente.
  Quando left volta a 128, começa uma nova entrada.
  Processamos os elementos em ordem de documento e agrupamos por "reset a left=128".

Formatos de entrada:
  A) técnico , popular (pop)           → <b>T</b> ,  <i>P</i>  (pop)
  B) popular (pop) , técnico           → <i>P</i>  (pop) ,  <b>T</b>
  C) técnico , popular (pop)           → <b>T</b> , espinha (pop)   [sem <i>]

Saída JSON: { "técnico": "popular", ... }
"""

import xml.etree.ElementTree as ET
import json
import re


# ------------------------------------------------------------------
# 1) Ler XML
# ------------------------------------------------------------------
with open("data/glossario_termos_medicos.xml", "r", encoding="utf-8") as f:
    raw = f.read()

raw = re.sub(r"<!DOCTYPE[^>]*>", "", raw)
root = ET.fromstring(raw)


# ------------------------------------------------------------------
# 2) Extrair todos os elementos <text> em ordem de documento
# ------------------------------------------------------------------
def elem_text_full(e):
    """Texto completo de um elemento incluindo sub-tags."""
    return "".join(e.itertext()).strip()

def bold_text(e):
    b = e.find("b")
    return b.text.strip() if b is not None and b.text else None

def italic_text(e):
    i = e.find("i")
    return i.text.strip() if i is not None and i.text else None

def is_section_letter(e):
    """<b>A</b> — cabeçalho de secção, ignorar."""
    b = e.find("b")
    if b is not None and b.text:
        return len(b.text.strip()) == 1 and b.text.strip().isupper()
    return False


all_texts = []  # lista de dicts com info de cada <text>

for page in root.findall("page"):
    page_num = int(page.get("number", 0))
    for t in page.findall("text"):
        left = int(t.get("left", 0))
        top  = int(t.get("top", 0))
        full = elem_text_full(t)
        bt   = bold_text(t)
        it   = italic_text(t)
        has_pop = "(pop)" in full

        # Ignorar elementos vazios e cabeçalhos de página
        if not full:
            continue
        if is_section_letter(t):
            continue

        all_texts.append({
            "page": page_num,
            "left": left,
            "top":  top,
            "full": full,
            "bold": bt,
            "italic": it,
            "has_pop": has_pop,
        })


# ------------------------------------------------------------------
# 3) Agrupar em entradas: nova entrada quando left volta a 128
#    (com margem de ±5 px para variações de digitização)
# ------------------------------------------------------------------
def is_entry_start(elem):
    return elem["left"] <= 135  # left ≈ 128

entries = []
current = []

# Ignorar os primeiros elementos da página 1 (cabeçalho do documento)
# Começamos a partir do primeiro elemento que seja um termo ou popular
skip_header = True
header_keywords = {
    "em português de portugal", "fonte:", "multilingual", "languages",
    "observação:", "this project", "http://", "glossário de termos"
}

for elem in all_texts:
    # Pular cabeçalho do documento (página 1)
    if skip_header:
        if any(kw in elem["full"].lower() for kw in header_keywords):
            continue
        if elem["page"] > 1:
            skip_header = False
        elif elem["left"] <= 135 and (elem["bold"] or elem["italic"]):
            # Primeiro termo real da página 1
            skip_header = False

    if is_entry_start(elem) and current:
        entries.append(current)
        current = [elem]
    else:
        current.append(elem)

if current:
    entries.append(current)


# ------------------------------------------------------------------
# 4) Parsear cada entrada
# ------------------------------------------------------------------
glossario = {}

def parse_entry(elems):
    """
    Analisa uma entrada e retorna (técnico, popular) ou None.
    """
    # Reconstruir sequência de tokens
    tokens = []
    for e in elems:
        if e["bold"] and len(e["bold"]) > 1:
            tokens.append(("bold", e["bold"]))
        elif e["italic"]:
            tokens.append(("italic", e["italic"]))
        elif e["has_pop"]:
            tokens.append(("pop", "(pop)"))
        # Ignorar separadores " , " e espaços

    if not tokens:
        return None

    # Padrão B: italic (pop) [, bold]
    if tokens[0][0] == "italic":
        popular = tokens[0][1]
        # Verificar (pop) a seguir
        if len(tokens) > 1 and tokens[1][0] == "pop":
            # Verificar bold depois
            if len(tokens) > 2 and tokens[2][0] == "bold":
                return (tokens[2][1], popular)
            # Sem bold: entrada só popular (sem designação técnica associada)
            return None

    # Padrão A: bold [, italic (pop)]
    if tokens[0][0] == "bold":
        tecnico = tokens[0][1]
        if len(tokens) >= 3:
            # bold , italic (pop)
            if tokens[1][0] == "italic" and tokens[2][0] == "pop":
                return (tecnico, tokens[1][1])
        # Padrão especial: bold , texto-normal (pop) — ex: "acne , espinha (pop)"
        # Neste caso, o popular está no full text de um dos elementos sem <i>
        # Procurar "BOLD , POPULAR (pop)" no texto completo concatenado
        full_line = " ".join(e["full"] for e in elems)
        m = re.search(r"\(pop\)", full_line)
        if m:
            # Extrair o popular que precede (pop)
            before_pop = full_line[:m.start()].strip().rstrip(",").strip()
            # Remover o próprio termo técnico do início
            if before_pop.lower().startswith(tecnico.lower()):
                popular = before_pop[len(tecnico):].strip().lstrip(",").strip()
            else:
                popular = before_pop
            if popular:
                return (tecnico, popular)

    return None


for entry in entries:
    result = parse_entry(entry)
    if result:
        tecnico, popular = result
        if tecnico not in glossario:
            glossario[tecnico] = popular


# ------------------------------------------------------------------
# 5) Guardar JSON
# ------------------------------------------------------------------
out_path = "glossario_termos_medicos.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(glossario, f, ensure_ascii=False, indent=4)
