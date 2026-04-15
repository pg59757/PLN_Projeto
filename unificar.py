import json
import unicodedata
import re

# Função para remover acentos e normalizar texto
def normalizar(texto):
    if not texto:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', texto.lower().strip())
    return "".join([char for char in nfkd_form if not unicodedata.combining(char)])

# Função para remover tags tipo [Br.], [Pt.], etc.
def limpar_tags(texto):
    if not texto:
        return ""
    return re.sub(r"\s*\[.*?\]", "", texto).strip()

# 1. Carregar os ficheiros
with open('medicina.json', 'r', encoding='utf-8') as f:
    pln_data = json.load(f)

with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    covid_data = json.load(f)

with open('glossario_enfermagem_final.json', 'r', encoding='utf-8') as f:
    enfermagem_data = json.load(f)

with open('glossario_medico_portugal.json', 'r', encoding='utf-8') as f:
    portugal_data = json.load(f)

vocabulario = pln_data["Vocabulário médico"]

# 2. Mapeamento com Normalização
pln_lookup_galego = {}
pt_lookup = {}

for i, item in enumerate(vocabulario):
    item.pop("tipo_entrada", None)
    item.pop("id_entrada", None)

    # Galego
    if "termo_galego" in item and item["termo_galego"].get("palavra"):
        gal_key = normalizar(item["termo_galego"]["palavra"])
        pln_lookup_galego[gal_key] = i

    # Português
    if "traducoes" in item and item["traducoes"].get("português"):
        termos_pt = item["traducoes"]["português"].split(";")
        for t in termos_pt:
            t_limpo = limpar_tags(t)
            t_norm = normalizar(t_limpo)
            if t_norm:
                pt_lookup[t_norm] = i

# 3. Funções auxiliares
def juntar_traducao(atual, novo):
    novo = limpar_tags(novo)
    if not atual:
        return novo

    partes = [limpar_tags(p.strip()) for p in atual.split(";") if p.strip()]

    if novo not in partes:
        partes.append(novo)

    return "; ".join(partes)

def adicionar_definicao_por_pt(glossario_novo):
    for termo, definicao in glossario_novo.items():
        termo_limpo = limpar_tags(termo)
        termo_norm = normalizar(termo_limpo)

        if termo_norm in pt_lookup:
            idx = pt_lookup[termo_norm]

            if not vocabulario[idx].get("nota"):
                vocabulario[idx]["nota"] = definicao
            else:
                if definicao[:20] not in vocabulario[idx]["nota"]:
                    vocabulario[idx]["nota"] += f" | Definição: {definicao}"

# 4. Processar COVID
for chave_covid, info in covid_data.items():
    traducoes = info.get("traducoes", {})

    termo_galego_original = traducoes.get("galego", "")
    termo_galego_norm = normalizar(termo_galego_original)

    if not termo_galego_norm:
        continue

    if termo_galego_norm in pln_lookup_galego:
        item = vocabulario[pln_lookup_galego[termo_galego_norm]]

        if "traducoes" not in item:
            item["traducoes"] = {}

        for lingua, valor in traducoes.items():
            if not valor or lingua == "galego":
                continue

            item["traducoes"][lingua] = juntar_traducao(
                item["traducoes"].get(lingua, ""), valor
            )

        if info.get("definicao") and not item.get("nota"):
            item["nota"] = info["definicao"]

    else:
        nova_entrada = {
            "termo_galego": {
                "palavra": termo_galego_original,
                "genero_palavra": None,
                "sinonimos_galego": []
            },
            "tema": [info["categoria"]] if info.get("categoria") else [],
            "traducoes": {
                l: limpar_tags(v)
                for l, v in traducoes.items()
                if v and l != "galego"
            },
            "nota": info.get("definicao") or None
        }

        vocabulario.append(nova_entrada)

        idx_nova = len(vocabulario) - 1
        pln_lookup_galego[termo_galego_norm] = idx_nova

        if "português" in nova_entrada["traducoes"]:
            for t in nova_entrada["traducoes"]["português"].split(";"):
                t_limpo = limpar_tags(t)
                pt_lookup[normalizar(t_limpo)] = idx_nova

# 5. Integrar Glossários
adicionar_definicao_por_pt(enfermagem_data)
adicionar_definicao_por_pt(portugal_data)

# 6. Limpeza final (remove tags + duplicados)
for item in vocabulario:
    if "traducoes" in item and "português" in item["traducoes"]:
        termos = item["traducoes"]["português"].split(";")

        termos_limpos = []
        vistos = set()

        for t in termos:
            t_limpo = limpar_tags(t.strip())
            if t_limpo and t_limpo not in vistos:
                vistos.add(t_limpo)
                termos_limpos.append(t_limpo)

        item["traducoes"]["português"] = "; ".join(termos_limpos)

# 7. Gravar
with open('pln_final_unificado.json', 'w', encoding='utf-8') as f:
    json.dump(pln_data, f, ensure_ascii=False, indent=4)

print("Fusão concluída com sucesso (sem tags de língua).")