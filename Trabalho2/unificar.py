import json
import unicodedata
import re

# ─── Mapeamento de línguas para siglas ISO ─────────────────────────────────
MAP_LINGUA = {
    "espanhol":       "es",
    "inglês":         "en",
    "português":      "pt",
    "latim":          "la",
    "francês":        "fr",
    "euskera":        "eu",
    "holandês":       "nl",
    "occitan":        "oc",
    "português (BR)": "pt_BR",
    "português (PT)": "pt_PT",
}

# ─── Funções auxiliares ────────────────────────────────────────────────────
def normalizar(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', texto.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def remover_tags(texto):
    if not texto:
        return ""
    return re.sub(r"\s*\[.*?\]", "", texto).strip()

def juntar_traducao(atual, nova):
    nova = remover_tags(nova)
    if not atual:
        return nova
    existentes = [remover_tags(t.strip()) for t in atual.split(";") if t.strip()]
    if nova not in existentes:
        existentes.append(nova)
    return "; ".join(existentes)

def integrar_definicao(indice, nova):
    if not nova:
        return
    if not vocabulario[indice]["def"]:
        vocabulario[indice]["def"] = nova
    elif nova not in vocabulario[indice]["def"]:
        vocabulario[indice]["def"] += f" | {nova}"

# ─── Leitura dos ficheiros ─────────────────────────────────────────────────
with open('medicina.json', 'r', encoding='utf-8') as f:
    dados_medicina = json.load(f)
with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    dados_covid = json.load(f)
with open('glossario_enfermagem.json', 'r', encoding='utf-8') as f:
    dados_enfermagem = json.load(f)
with open('glossario_termos_medicos.json', 'r', encoding='utf-8') as f:
    dados_termos = json.load(f)

# ─── Construção do vocabulário com chaves curtas ───────────────────────────
vocabulario = []
for item in dados_medicina.get("Vocabulário médico", []):
    tg_orig   = item.get("termo_galego", {})
    trad_orig = item.get("traducoes", {})
    novo = {
        "tg": {
            "pal": tg_orig.get("palavra", ""),
            "gen": tg_orig.get("genero_palavra"),
            "sin": tg_orig.get("sinonimos_galego", [])
        },
        "tema": item.get("tema", []),
        "trad": {MAP_LINGUA.get(k, k): remover_tags(v)
                 for k, v in trad_orig.items() if v},
        "def": None
    }
    vocabulario.append(novo)

# ─── Mapas de lookup ──────────────────────────────────────────────────────
mapa_galego    = {normalizar(v["tg"]["pal"]): i for i, v in enumerate(vocabulario) if v["tg"]["pal"]}
mapa_portugues = {}
for i, item in enumerate(vocabulario):
    pt = item["trad"].get("pt", "")
    for t in pt.split(";"):
        t_n = normalizar(remover_tags(t))
        if t_n:
            mapa_portugues[t_n] = i

# ─── Integrar dicionário COVID ────────────────────────────────────────────
for chave, info in dados_covid.items():
    traducoes = info.get("traducoes", {})
    gal_norm  = normalizar(traducoes.get("galego", ""))

    if gal_norm in mapa_galego:
        idx = mapa_galego[gal_norm]
        for lingua, termo in traducoes.items():
            if termo and lingua != "galego":
                sigla = MAP_LINGUA.get(lingua, lingua)
                vocabulario[idx]["trad"][sigla] = juntar_traducao(
                    vocabulario[idx]["trad"].get(sigla, ""), termo)
        integrar_definicao(idx, info.get("definicao"))
    else:
        nova = {
            "tg":   {"pal": traducoes.get("galego", ""), "gen": None, "sin": []},
            "tema": [info["categoria"]] if info.get("categoria") else [],
            "trad": {MAP_LINGUA.get(l, l): remover_tags(v)
                     for l, v in traducoes.items() if v and l != "galego"},
            "def":  info.get("definicao") or None
        }
        vocabulario.append(nova)
        idx_nova = len(vocabulario) - 1
        mapa_galego[gal_norm] = idx_nova
        if "pt" in nova["trad"]:
            mapa_portugues[normalizar(nova["trad"]["pt"])] = idx_nova

# ─── Integrar glossários (definições) ────────────────────────────────────
for glossario in [dados_enfermagem, dados_termos]:
    for termo, definicao in glossario.items():
        t_n = normalizar(remover_tags(termo))
        if t_n in mapa_portugues:
            integrar_definicao(mapa_portugues[t_n], definicao)

# ─── Limpeza traduções PT duplicadas ─────────────────────────────────────
for item in vocabulario:
    pt = item["trad"].get("pt", "")
    if pt:
        vistos, limpos = set(), []
        for t in pt.split(";"):
            t_l = remover_tags(t.strip())
            if t_l and t_l not in vistos:
                vistos.add(t_l)
                limpos.append(t_l)
        item["trad"]["pt"] = "; ".join(limpos)

# ─── Remover campos vazios/None ───────────────────────────────────────────
vocabulario = [v for v in vocabulario if v["tg"]["pal"]]
for item in vocabulario:
    if not item["def"]:
        item.pop("def", None)
    if not item["trad"]:
        item.pop("trad", None)
    if not item["tema"]:
        item.pop("tema", None)
    if not item["tg"]["sin"]:
        item["tg"].pop("sin", None)
    if not item["tg"]["gen"]:
        item["tg"].pop("gen", None)

# ─── Guardar ──────────────────────────────────────────────────────────────
out = "dicionario_unificado.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump({"vocab": vocabulario}, f, ensure_ascii=False, indent=2)

import os
print(f"Concluído. {len(vocabulario)} termos guardados em {out}.")
print(f"Tamanho: {os.path.getsize(out)/1024:.1f} KB")