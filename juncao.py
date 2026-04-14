import json

# Carregar os ficheiros
with open('pln_tp1.json', 'r', encoding='utf-8') as f:
    pln_data = json.load(f)

with open('dicionario_covid_final_gemini.json', 'r', encoding='utf-8') as f:
    covid_data = json.load(f)

vocabulario = pln_data["Vocabulário médico"]

# 1. Mapa de termos galegos para busca rápida
pln_lookup = {str(item["termo_galego"]["palavra"]).lower().strip(): i 
              for i, item in enumerate(vocabulario) if "termo_galego" in item}

# 2. Mapa de normalização de nomes de línguas (COVID -> PLN)
# O PLN usa nomes sem acentos. Vamos mapear os principais e o resto fica como está.
mapa_nomes_linguas = {
    "inglês": "ingles",
    "espanhol": "espanhol",
    "português": "portugues",
    "português (PT)": "portugues",
    "francês": "frances",
    "holandês": "holandes",
    "euskera": "basco",
    "occitan": "occitano"
}

# 3. Processar
for entrada_id, info in covid_data.items():
    traducoes = info.get("traduções", {})
    termo_gl_covid = traducoes.get("galego", "").lower().strip()
    
    if not termo_gl_covid:
        continue

    if termo_gl_covid in pln_lookup:
        item = vocabulario[pln_lookup[termo_gl_covid]]
        
        # --- JUNTAR TRADUÇÕES DINAMICAMENTE ---
        for ling_covid, valor in traducoes.items():
            if not valor or ling_covid == "galego": continue
            
            # Normaliza o nome da língua (ex: "neerlandês" -> "neerlandes")
            ling_pln = mapa_nomes_linguas.get(ling_covid, ling_covid)
            
            # Se o campo não existir no item do PLN, cria uma lista vazia
            if ling_pln not in item or item[ling_pln] is None:
                item[ling_pln] = []
            
            # Adiciona a tradução se ela ainda não estiver lá
            if isinstance(item[ling_pln], list):
                if valor not in item[ling_pln]:
                    item[ling_pln].append(valor)
            else:
                # Caso o campo original não seja uma lista (segurança)
                if item[ling_pln] != valor:
                    item[ling_pln] = [item[ling_pln], valor]

        # --- JUNTAR DEFINIÇÃO E TEMA ---
        def_covid = info.get("definição") or ""
        nota_atual = item.get("nota") or ""
        if def_covid and def_covid not in nota_atual:
            item["nota"] = f"{nota_atual} | [Def. COVID]: {def_covid}".strip(" | ")
            
        cat = info.get("categoria")
        if cat and cat not in item.get("tema", []):
            if "tema" not in item or item["tema"] is None: item["tema"] = []
            item["tema"].append(cat)
            
    else:
        # Criar nova entrada com todas as traduções
        nova_entrada = {
            "entrada": "definicao",
            "termo_galego": {"palavra": termo_gl_covid, "classe_gramatical": None, "sinonimos_galego": []},
            "tema": [info.get("categoria")] if info.get("categoria") else [],
            "nota": f"Fonte COVID: {info.get('definição', '')}",
            "latim": []
        }
        # Adiciona as línguas dinamicamente
        for ling_covid, valor in traducoes.items():
            if valor and ling_covid != "galego":
                ling_pln = mapa_nomes_linguas.get(ling_covid, ling_covid)
                nova_entrada[ling_pln] = [valor]
        
        vocabulario.append(nova_entrada)

# Guardar
with open('pln_final_com_todas_linguas.json', 'w', encoding='utf-8') as f:
    json.dump(pln_data, f, ensure_ascii=False, indent=4)



import json

with open('pln_final_com_todas_linguas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

vocab = data["Vocabulário médico"]

# 1. Testar um termo que devia ter sido fundido
teste = [item for item in vocab if item["termo_galego"]["palavra"].lower() == "acalabrutinib"]

if teste:
    print("--- Exemplo de Termo Fundido ---")
    print(json.dumps(teste[0], indent=4, ensure_ascii=False))
else:
    print("Termo não encontrado.")

# 2. Contar quantos têm a marca de [COVID] na nota
fundidos = [item for item in vocab if "[COVID]" in (item.get("nota") or "")]
print(f"\nTotal de termos que receberam dados do COVID: {len(fundidos)}")