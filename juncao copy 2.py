import json

# 1. Carregar os ficheiros
# pln_vocab_medicina.json deve ser o resultado do parser do XML que fizemos antes
with open('medicina.json', 'r', encoding='utf-8') as f:
    pln_data = json.load(f)

with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    covid_data = json.load(f)

vocabulario = pln_data["Vocabulário médico"]

# 2. Mapa de busca rápida e limpeza inicial de campos
# Aproveitamos para remover tipo_entrada e id_entrada do que já existe
pln_lookup = {}
for i, item in enumerate(vocabulario):
    # Remover campos indesejados se existirem
    item.pop("tipo_entrada", None)
    item.pop("id_entrada", None)
    
    if "termo_galego" in item and item["termo_galego"].get("palavra"):
        palavra_chave = item["termo_galego"]["palavra"].lower().strip()
        pln_lookup[palavra_chave] = i

# 3. Configurações de processamento
linguas_ignorar = {"galego"}

def juntar_traducao(atual, novo):
    if not atual:
        return novo
    partes = [p.strip() for p in atual.split(";")]
    if novo not in partes:
        partes.append(novo)
    return "; ".join(partes)

# 4. Processar cada entrada do dicionário COVID
for chave_covid, info in covid_data.items():
    traducoes = info.get("traducoes", {})
    termo_galego = traducoes.get("galego", "").lower().strip()

    if not termo_galego:
        continue

    if termo_galego in pln_lookup:
        # --- TERMO EXISTE: Atualizar ---
        item = vocabulario[pln_lookup[termo_galego]]

        if "traducoes" not in item or item["traducoes"] is None:
            item["traducoes"] = {}

        for lingua, valor in traducoes.items():
            if not valor or lingua in linguas_ignorar:
                continue
            
            if lingua not in item["traducoes"]:
                item["traducoes"][lingua] = valor
            else:
                item["traducoes"][lingua] = juntar_traducao(item["traducoes"][lingua], valor)
        
        # Se o COVID tiver definição, podemos preencher a nota se estiver vazia
        if info.get("definicao") and not item.get("nota"):
            item["nota"] = info["definicao"]

    else:
        # --- TERMO NÃO EXISTE: Criar nova entrada (Layout Limpo) ---
        nova_entrada = {
            "termo_galego": {
                "palavra": termo_galego,
                "genero_palavra": None,
                "sinonimos_galego": []
            },
            "tema": [info["categoria"]] if info.get("categoria") else [],
            "traducoes": {
                lingua: valor
                for lingua, valor in traducoes.items()
                if valor and lingua not in linguas_ignorar
            },
            "nota": info.get("definicao") or None
        }
        vocabulario.append(nova_entrada)

# 5. Guardar o resultado final
with open('pln_final_limpo_2.json', 'w', encoding='utf-8') as f:
    json.dump(pln_data, f, ensure_ascii=False, indent=4)

print("Processo concluído.")