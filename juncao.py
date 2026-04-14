import json

# Carregar os ficheiros
with open('pln_vocab_medicina.json', 'r', encoding='utf-8') as f:
    pln_data = json.load(f)

with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    covid_data = json.load(f)

vocabulario = pln_data["Vocabulário médico"]

# 1. Mapa de termos galegos do PLN para busca rápida
pln_lookup = {
    item["termo_galego"]["palavra"].lower().strip(): i
    for i, item in enumerate(vocabulario)
    if "termo_galego" in item
}

# 2. Línguas a ignorar (galego já está no termo_galego do PLN)
linguas_ignorar = {"galego"}

# 3. Função para juntar traduções sem duplicar
def juntar_traducao(atual, novo):
    if not atual:
        return novo
    partes = [p.strip() for p in atual.split(";")]
    if novo not in partes:
        partes.append(novo)
    return "; ".join(partes)

# 4. Processar cada entrada do COVID
for chave_covid, info in covid_data.items():
    traducoes = info.get("traducoes", {})

    # Obter o termo em galego
    termo_galego = traducoes.get("galego", "").lower().strip()

    if not termo_galego:
        continue

    if termo_galego in pln_lookup:
        # --- TERMO EXISTE: acrescentar traduções em línguas novas ---
        item = vocabulario[pln_lookup[termo_galego]]

        if "traducoes" not in item or item["traducoes"] is None:
            item["traducoes"] = {}

        for lingua, valor in traducoes.items():
            if not valor or lingua in linguas_ignorar:
                continue
            # Só acrescenta se a língua ainda não existir
            if lingua not in item["traducoes"]:
                item["traducoes"][lingua] = valor
            else:
                item["traducoes"][lingua] = juntar_traducao(item["traducoes"][lingua], valor)

    else:
        # --- TERMO NÃO EXISTE: criar nova entrada no formato PLN ---
        nova_entrada = {
            "tipo_entrada": "definicao_completa",
            "id_entrada": None,
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

# 5. Guardar
with open('pln_final_com_todas_linguas.json', 'w', encoding='utf-8') as f:
    json.dump(pln_data, f, ensure_ascii=False, indent=4)



# --- Teste ---
with open('pln_final_com_todas_linguas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

vocab = data["Vocabulário médico"]

teste = [item for item in vocab if item["termo_galego"]["palavra"].lower() == "aerosol"]

if teste:
    print("--- Exemplo de Termo Fundido ---")
    print(json.dumps(teste[0], indent=4, ensure_ascii=False))
else:
    print("Termo não encontrado.")

novas = [item for item in vocab if item.get("id_entrada") is None]
print(f"\nNovas entradas criadas: {len(novas)}")
print(f"Total de entradas: {len(vocab)}")