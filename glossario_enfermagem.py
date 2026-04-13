"""Parser do Glossário da Linguagem Especial de Enfermagem (PT/BR)
TP1 - Processamento de Linguagem Natural - Engenharia Biomédica 2025-2026
 
Estrutura do XML:
  - font 49  → termo (bold) — inicia nova entrada
  - font 21  → linhas da definição (texto simples)
  - font 50  → "FONTE:" (ignorar)
  - font 51  → fonte/citação (ignorar, ou guardar opcionalmente)
  - Outras fontes (cabeçalhos, rodapés, letras decorativas) → ignorar
 
Saída JSON: { "termo": "definição completa", ... }
"""
 
import xml.etree.ElementTree as ET
import json
import re
 
 
# ------------------------------------------------------------------
# 1) Ler XML
# ------------------------------------------------------------------
with open("data/glossario_enfermagem.xml", "r", encoding="utf-8") as f:
    raw = f.read()
 
raw = re.sub(r"<!DOCTYPE[^>]*>", "", raw)
root = ET.fromstring(raw)
 
 
# ------------------------------------------------------------------
# 2) Identificar fontes relevantes
# ------------------------------------------------------------------
FONT_TERMO    = "49"   # termos (bold)
FONT_DEF      = "21"   # definição
FONT_FONTE_LB = "50"   # "FONTE:" label
FONT_FONTE_TX = "51"   # texto da fonte/citação
 
GLOSSARY_START_PAGE = 23  # página 24 (índice 0-based = 23)
 
def elem_full_text(e):
    return "".join(e.itertext()).strip()
 
 
# ------------------------------------------------------------------
# 3) Recolher todos os elementos relevantes em ordem de documento
# ------------------------------------------------------------------
elements = []
 
for page in root.findall("page"):
    page_num = int(page.get("number", 0))
    if page_num < GLOSSARY_START_PAGE + 1:
        continue
 
    for t in page.findall("text"):
        font = t.get("font", "")
        if font not in (FONT_TERMO, FONT_DEF, FONT_FONTE_LB, FONT_FONTE_TX):
            continue
 
        text = elem_full_text(t)
        if not text:
            continue
 
        elements.append({
            "font": font,
            "text": text,
            "page": page_num,
        })
 
 
# ------------------------------------------------------------------
# 4) Agrupar em entradas: nova entrada quando font == FONT_TERMO
# ------------------------------------------------------------------
entries = []
current_term = None
current_def_parts = []
 
for elem in elements:
    if elem["font"] == FONT_TERMO:
        # Guardar entrada anterior
        if current_term is not None:
            defn = " ".join(current_def_parts).strip()
            # Limpar espaços múltiplos
            defn = re.sub(r"\s+", " ", defn)
            entries.append((current_term, defn))
        current_term = elem["text"]
        current_def_parts = []
 
    elif elem["font"] == FONT_DEF:
        if current_term is not None:
            current_def_parts.append(elem["text"])
 
    # FONTE_LB e FONTE_TX são ignorados (não incluímos na definição)
 
# Guardar última entrada
if current_term is not None:
    defn = " ".join(current_def_parts).strip()
    defn = re.sub(r"\s+", " ", defn)
    entries.append((current_term, defn))
 
 
# ------------------------------------------------------------------
# 5) Construir dicionário (sem duplicatas — última ocorrência vence)
# ------------------------------------------------------------------
glossario = {}
for termo, defn in entries:
    glossario[termo] = defn
 
 
# ------------------------------------------------------------------
# 6) Guardar JSON
# ------------------------------------------------------------------
out_path = "glossario_enfermagem.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(glossario, f, ensure_ascii=False, indent=4)
 
