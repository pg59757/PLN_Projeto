import re
import json

# Ler o ficheiro
with open("pdfs/dicionario_covid.txt", "r", encoding="utf8") as f:
    texto = f.read()

# Passo 1: Limpeza - remover quebras de página e caracteres de controlo
texto = re.sub(r'\f', '', texto)
texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)

# Passo 2: Dividir em entradas (cada entrada começa com número + espaço + termo)
# Usar padrão que captura o número e mantém o resto
entradas_split = re.split(r'\n(\d+)\s+', texto)

vocabulario_covid = []

# Processar pares (id, conteúdo)
for i in range(1, len(entradas_split), 2):
    if i + 1 >= len(entradas_split):
        break
    
    id_entrada = int(entradas_split[i].strip())
    conteudo = entradas_split[i + 1]
    
    # Dividir conteúdo em linhas
    linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
    
    if not linhas:
        continue
    
    # Primeira linha tem o termo catalão
    primeira_linha = linhas[0]
    
    # Extrair termo catalão e classe gramatical
    match_termo = re.match(r'^(.+?)\s+n\s+([mf])$', primeira_linha)
    if not match_termo:
        continue
    
    termo_catala = match_termo.group(1).strip()
    classe_gramatical = match_termo.group(2).strip()
    
    # Criar entrada
    entrada = {
        "id": id_entrada,
        "termo_catala": {
            "palavra": termo_catala,
            "classe_gramatical": classe_gramatical
        }
    }
    
    # Dicionário para traduções
    traducoes = {}
    lingua_atual = None
    definicao_partes = []
    nota_partes = []
    em_definicao = False
    em_nota = False
    
    # Processar resto das linhas
    for linha in linhas[1:]:
        # Verificar se é "veg." (ver)
        if linha.startswith("veg."):
            entrada["veja"] = linha.replace("veg.", "").strip()
            continue
        
        # Verificar se é sinónimo
        if linha.startswith("sin. compl."):
            entrada["sinonimo"] = linha.replace("sin. compl.", "").strip()
            continue
        
        # Verificar se é sigla
        if linha.startswith("sigla"):
            entrada["sigla"] = linha.replace("sigla", "").strip()
            continue
        
        # Verificar se é CAS
        if linha.startswith("CAS"):
            entrada["cas"] = linha.replace("CAS", "").strip()
            continue
        
        # Verificar se é início de definição (categoria em maiúsculas seguida de ponto)
        if re.match(r'^[A-ZÀÈÉÍÒÓÚÄËÏÖÜÇ\s]+\.', linha):
            em_definicao = True
            em_nota = False
            definicao_partes.append(linha)
            lingua_atual = None
            continue
        
        # Verificar se é nota
        if linha.startswith("Nota:"):
            em_nota = True
            em_definicao = False
            nota_partes.append(linha.replace("Nota:", "").strip())
            lingua_atual = None
            continue
        
        # Verificar se é código de língua (oc, eu, gl, es, en, fr, pt, nl, ar)
        match_lingua = re.match(r'^(oc|eu|gl|es|en|fr|nl|ar)\s+(.*)$', linha)
        if match_lingua:
            lingua_atual = match_lingua.group(1)
            texto_trad = match_lingua.group(2).strip()
            em_definicao = False
            em_nota = False
            
            if lingua_atual not in traducoes:
                traducoes[lingua_atual] = []
            if texto_trad:
                traducoes[lingua_atual].append(texto_trad)
            continue
        
        # Verificar se é inglês
        match_en = re.match(r'^en\s+(.*)$', linha)
        if match_en:
            lingua_atual = "en"
            texto_trad = match_en.group(1).strip()
            em_definicao = False
            em_nota = False
            
            if lingua_atual not in traducoes:
                traducoes[lingua_atual] = []
            if texto_trad:
                traducoes[lingua_atual].append(texto_trad)
            continue
        
        # Verificar se é português (com ou sem variante)
        match_pt = re.match(r'^pt(\s+\[(PT|BR)\])?\s+(.*)$', linha)
        if match_pt:
            variante = match_pt.group(2)  # PT, BR ou None
            texto_trad = match_pt.group(3).strip()
            em_definicao = False
            em_nota = False
            
            if "pt" not in traducoes:
                traducoes["pt"] = []
            
            if texto_trad:
                if variante:
                    traducoes["pt"].append(f"[{variante}] {texto_trad}")
                else:
                    traducoes["pt"].append(texto_trad)
            
            lingua_atual = "pt"
            continue
        
        # Se não é nenhum marcador especial, é continuação
        if em_definicao:
            definicao_partes.append(linha)
        elif em_nota:
            nota_partes.append(linha)
        elif lingua_atual and not re.match(r'^\d+\s+', linha):
            # Continuação da tradução atual
            traducoes[lingua_atual].append(linha)
    
    # Adicionar traduções à entrada
    if traducoes:
        entrada["traducoes"] = traducoes
    
    # Adicionar definição se existir
    if definicao_partes:
        entrada["definicao"] = " ".join(definicao_partes)
    
    # Adicionar nota se existir
    if nota_partes:
        entrada["nota"] = " ".join(nota_partes)
    
    vocabulario_covid.append(entrada)

# Criar estrutura final
dicionario_final = {
    "vocabulario_covid": vocabulario_covid
}

# Escrever JSON
with open("pdfs/dicionario_covid_claude.json", "w", encoding="utf8") as f:
    json.dump(dicionario_final, f, indent=4, ensure_ascii=False)

# Estatísticas
print(f"✓ Processadas {len(vocabulario_covid)} entradas")
print(f"✓ Ficheiro criado: dicionario_covid.json")

# Mostrar exemplos
print("\n" + "="*60)
print("EXEMPLOS DE ENTRADAS:")
print("="*60)

for i, entrada in enumerate(vocabulario_covid[:3], 1):
    print(f"\n{i}. Termo catalão: {entrada['termo_catala']['palavra']}")
    print(f"   ID: {entrada['id']}")
    print(f"   Classe gramatical: {entrada['termo_catala']['classe_gramatical']}")
    
    if "traducoes" in entrada:
        if "gl" in entrada["traducoes"]:
            print(f"   Galego: {'; '.join(entrada['traducoes']['gl'][:2])}")
        if "pt" in entrada["traducoes"]:
            print(f"   Português: {'; '.join(entrada['traducoes']['pt'][:2])}")
        if "es" in entrada["traducoes"]:
            print(f"   Espanhol: {'; '.join(entrada['traducoes']['es'][:2])}")
    
    if "veja" in entrada:
        print(f"   [Veja: {entrada['veja']}]")
