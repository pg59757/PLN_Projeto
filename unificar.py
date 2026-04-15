import json
import unicodedata
import re

#FUNÇÕES AUXILIARES
# Função auxiliar para remover acentos e normalizar texto, tornando o todo em minúsculas
def normalizar(texto):
    if not texto:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', texto.lower().strip())
    return "".join([char for char in nfkd_form if not unicodedata.combining(char)])

# Função auxiliar para remover tags tipo [Br.], [Pt.], etc.
def remover_tags(texto):
    if not texto:
        return ""
    return re.sub(r"\s*\[.*?\]", "", texto).strip()

# Função auxiliar juntar novas traduções às já existentes
def juntar_traducao(traducao_atual, nova_traducao):
    nova_traducao = remover_tags(nova_traducao)
    if not traducao_atual: 
        return nova_traducao
    
    termos_existentes = [remover_tags(t.strip()) for t in traducao_atual.split(";") if t.strip()]
    if nova_traducao not in termos_existentes:
        termos_existentes.append(nova_traducao)
    return "; ".join(termos_existentes)

def integrar_definicao(indice, nova_definicao):
    if not nova_definicao: 
        return
    
    # Se o campo estiver vazio, coloca a definição
    if not vocabulario[indice]["definição"]:
        vocabulario[indice]["definição"] = nova_definicao
    else:
        # Se já tiver algo (de outro glossário), junta com |
        # Verificamos se a definição já não está lá para não duplicar
        if nova_definicao not in vocabulario[indice]["definição"]:
            vocabulario[indice]["definição"] += f" | {nova_definicao}"

# Passo 1: Leitura dos ficheiros
with open('medicina.json', 'r', encoding='utf-8') as f:
    dados_medicina = json.load(f)
with open('dicionario_covid.json', 'r', encoding='utf-8') as f:
    dados_covid = json.load(f)
with open('glossario_enfermagem.json', 'r', encoding='utf-8') as f:
    dados_enfermagem = json.load(f)
with open('glossario_termos_medicos.json', 'r', encoding='utf-8') as f:
    dados_termos = json.load(f)

# Definição do dicionário principal
vocabulario = dados_medicina["Vocabulário médico"]

# Passo 2: Remoção de atributos desnecessários no medicina - ficheiro base 
for item in vocabulario:
    item.pop("nota", None)
    item.pop("tipo_entrada", None)
    item.pop("id_entrada", None)
    # Inicialização o campo de definição
    item["definição"] = None


# Passo 3: Criação de dicionários para os termos em galego e português
# Úteis para encontrar termos  sem percorrer a lista toda 
mapa_galego = {}
mapa_portugues = {}

for i, item in enumerate(vocabulario):
    if "termo_galego" in item and item["termo_galego"].get("palavra"):
        mapa_galego[normalizar(item["termo_galego"]["palavra"])] = i
    
    # Mapear pelas traduções em Português já existentes
    if "traducoes" in item and item["traducoes"].get("português"):
        termos_pt = item["traducoes"]["português"].split(";")
        for t in termos_pt:
            t_normalizado = normalizar(remover_tags(t))
            if t_normalizado:
                mapa_portugues[t_normalizado] = i



# Passo 4: Processar os dados do dicionário covid
for chave_covid, info in dados_covid.items():
    traducoes = info.get("traducoes", {})
    termo_gal_norm = normalizar(traducoes.get("galego", ""))

    if termo_gal_norm in mapa_galego:
        indice = mapa_galego[termo_gal_norm]
        
        # Atualizar traduções
        if "traducoes" not in vocabulario[indice]: 
            vocabulario[indice]["traducoes"] = {}

        for lingua, termo_traduzido in traducoes.items():
            if termo_traduzido and lingua != "galego":
                vocabulario[indice]["traducoes"][lingua] = juntar_traducao(vocabulario[indice]["traducoes"].get(lingua, ""), termo_traduzido)
        
        # Adicionar definição
        integrar_definicao(indice, info.get("definicao"))
    else:
        # Criar nova entrada se não existir
        nova_entrada = {
            "termo_galego": {
                "palavra": traducoes.get("galego", ""),
                "genero_palavra": None,
                "sinonimos_galego": []
            },
            "tema": [info["categoria"]] if info.get("categoria") else [],
            "traducoes": {l: remover_tags(v) for l, v in traducoes.items() if v and l != "galego"},
            "definição": info.get("definicao") or None
        }
        vocabulario.append(nova_entrada)

        # Atualizar os mapas para futuras consultas neste mesmo loop
        indice_nova = len(vocabulario) - 1
        mapa_galego[termo_gal_norm] = indice_nova
        if "português" in nova_entrada["traducoes"]:
            pt_norm = normalizar(nova_entrada["traducoes"]["português"])
            mapa_portugues[pt_norm] = indice_nova

# Passo 5. Integrar as definições dos glossários
for glossario in [dados_enfermagem, dados_termos]:
    for termo, definicao in glossario.items():
        t_norm = normalizar(remover_tags(termo))

        #se o termo existir no dicionário principal
        if t_norm in mapa_portugues:
            integrar_definicao(mapa_portugues[t_norm], definicao)

# Passo 6. Limpeza das traduções em português (duplicados)
for item in vocabulario:
    if "traducoes" in item and "português" in item["traducoes"]:
        termos = item["traducoes"]["português"].split(";")
        vistos = set()
        termos_limpos = []

        for t in termos:
            t_l = remover_tags(t.strip())
            if t_l and t_l not in vistos:
                vistos.add(t_l)
                termos_limpos.append(t_l)

        item["traducoes"]["português"] = "; ".join(termos_limpos)

# Passo 7: Criação do ficheiro JSON com a informação unida de todos os JSONs
f_out="dicionario_unificado.json"
with open(f_out, 'w', encoding='utf-8') as f:
    json.dump(dados_medicina, f, ensure_ascii=False, indent=4)

print(f"Concluído. Termos guardados em {f_out}.")