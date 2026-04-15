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
with open('medicina2.json', 'r', encoding='utf-8') as f:
    pln_data = json.load(f)
with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    covid_data = json.load(f)
with open('glossario_enfermagem_final.json', 'r', encoding='utf-8') as f:
    enfermagem_data = json.load(f)
with open('glossario_medico_portugal.json', 'r', encoding='utf-8') as f:
    portugal_data = json.load(f)

vocabulario = pln_data["Vocabulário médico"]

# --- PADRONIZAÇÃO INICIAL ---
# Removemos as notas antigas do medicina2 para garantir que só ficam as dos glossários
for item in vocabulario:
    item.pop("nota", None)
    item["definição"] = None
    item.pop("tipo_entrada", None)
    item.pop("id_entrada", None)

# 2. Mapeamento
pln_lookup_galego = {}
pt_lookup = {}

for i, item in enumerate(vocabulario):
    if "termo_galego" in item and item["termo_galego"].get("palavra"):
        pln_lookup_galego[normalizar(item["termo_galego"]["palavra"])] = i
    
    if "traducoes" in item and item["traducoes"].get("português"):
        termos_pt = item["traducoes"]["português"].split(";")
        for t in termos_pt:
            t_norm = normalizar(limpar_tags(t))
            if t_norm:
                pt_lookup[t_norm] = i

# 3. Funções auxiliares
def juntar_traducao(atual, novo):
    novo = limpar_tags(novo)
    if not atual: return novo
    partes = [limpar_tags(p.strip()) for p in atual.split(";") if p.strip()]
    if novo not in partes:
        partes.append(novo)
    return "; ".join(partes)

def adicionar_ou_fundir_definicao(idx, nova_def):
    if not nova_def: return
    
    # Se o campo estiver vazio, coloca a definição
    if not vocabulario[idx]["definição"]:
        vocabulario[idx]["definição"] = nova_def
    else:
        # Se já tiver algo (de outro glossário), junta com |
        # Verificamos se a definição já não está lá para não duplicar
        if nova_def not in vocabulario[idx]["definição"]:
            vocabulario[idx]["definição"] += f" | Definição: {nova_def}"

# 4. Processar COVID
for chave_covid, info in covid_data.items():
    traducoes = info.get("traducoes", {})
    termo_gal_norm = normalizar(traducoes.get("galego", ""))

    if termo_gal_norm in pln_lookup_galego:
        idx = pln_lookup_galego[termo_gal_norm]
        
        # Atualizar traduções
        if "traducoes" not in vocabulario[idx]: vocabulario[idx]["traducoes"] = {}
        for lingua, valor in traducoes.items():
            if valor and lingua != "galego":
                vocabulario[idx]["traducoes"][lingua] = juntar_traducao(
                    vocabulario[idx]["traducoes"].get(lingua, ""), valor
                )
        
        # Adicionar definição
        adicionar_ou_fundir_definicao(idx, info.get("definicao"))
    else:
        # Criar nova entrada se não existir
        nova_entrada = {
            "termo_galego": {
                "palavra": traducoes.get("galego", ""),
                "genero_palavra": None,
                "sinonimos_galego": []
            },
            "tema": [info["categoria"]] if info.get("categoria") else [],
            "traducoes": {l: limpar_tags(v) for l, v in traducoes.items() if v and l != "galego"},
            "definição": info.get("definicao") or None
        }
        vocabulario.append(nova_entrada)
        idx_nova = len(vocabulario) - 1
        pln_lookup_galego[termo_gal_norm] = idx_nova
        if "português" in nova_entrada["traducoes"]:
            pt_lookup[normalizar(nova_entrada["traducoes"]["português"])] = idx_nova

# 5. Integrar Glossários (Enfermagem e Portugal)
for glossario in [enfermagem_data, portugal_data]:
    for termo, definicao in glossario.items():
        t_norm = normalizar(limpar_tags(termo))
        if t_norm in pt_lookup:
            adicionar_ou_fundir_definicao(pt_lookup[t_norm], definicao)

# 6. Limpeza final de traduções PT (duplicados)
for item in vocabulario:
    if "traducoes" in item and "português" in item["traducoes"]:
        termos = item["traducoes"]["português"].split(";")
        vistos = set()
        termos_limpos = []
        for t in termos:
            t_l = limpar_tags(t.strip())
            if t_l and t_l not in vistos:
                vistos.add(t_l)
                termos_limpos.append(t_l)
        item["traducoes"]["português"] = "; ".join(termos_limpos)

# 7. Gravar
with open('dicionario_unificado.json', 'w', encoding='utf-8') as f:
    json.dump(pln_data, f, ensure_ascii=False, indent=4)

print("Processo concluído.")