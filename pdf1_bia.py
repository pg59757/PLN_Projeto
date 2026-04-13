import re
import json

def processar_dicionario_covid(caminho_input):
    with open(caminho_input, "r", encoding="UTF-8") as f:
        texto = f.read()

    # 1. Limpeza de ruído do PDF
    texto = re.sub(r'\.', '', texto)
    texto = re.sub(r'QUADERNS 50 DICCIONARI MULTILINGÜE DE LA COVID-19', '', texto)
    # Remover cabeçalhos de página (Diccionari, Letra, Página)
    texto = re.sub(r'Diccionari\n[A-Z]\n\d+', '', texto)

    # 2. Identificação das línguas presentes
    # Baseado na análise: oc (Occitano), eu (Basco), gl (Galego), es (Espanhol), 
    # en (Inglês), fr (Francês), pt (Português), nl (Neerlandês), ar (Árabe)
    codigos_linguas = ['oc', 'eu', 'gl', 'es', 'en', 'fr', 'pt', 'nl', 'ar']

    # 3. Separar as entradas (Número seguido de espaço no início da linha)
    entradas_raw = re.split(r'\n(?=\d+\s)', texto)
    
    completas = []
    parciais = []

    for bloco in entradas_raw:
        bloco = bloco.strip()
        if not bloco: continue
        
        linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
        if not linhas: continue

        # Cabeçalho da entrada: ID e Termo em Catalão
        header = re.match(r'^(\d+)\s+(.*)', linhas[0])
        if not header: continue
        
        entry_id = int(header.group(1))
        termo_ca_completo = header.group(2)
        
        # Extrair categoria gramatical (ex: n m, adj, v intr)
        gram_match = re.search(r'\s+([nfav]\s+[m f]+|[nfav\.]+)$', termo_ca_completo)
        palavra_ca = termo_ca_completo[:gram_match.start()].strip() if gram_match else termo_ca_completo
        cat_gramatical = gram_match.group(1).strip() if gram_match else None

        # Objeto base (apenas com o que é garantido)
        entry_data = {
            "id": entry_id,
            "català": {
                "terme": palavra_ca
            }
        }
        if cat_gramatical: entry_data["català"]["categoria"] = cat_gramatical

        # Variáveis de controlo para o loop
        current_field = None
        
        for line in linhas[1:]:
            # Referência Cruzada (Incompleta por natureza)
            if line.startswith('veg.'):
                entry_data["ver_tambem"] = line.replace('veg.', '').strip()
                continue
            
            # Sinónimos e Siglas em Catalão
            if line.startswith('sin.'):
                entry_data["català"]["sinonims"] = [s.strip() for s in re.split(r'[;]', line.replace('sin.', '').replace('compl.', '').strip()) if s.strip()]
                continue
            if line.startswith('sigla'):
                entry_data["català"]["sigles"] = [s.strip() for s in re.split(r'[;]', line.replace('sigla', '').strip()) if s.strip()]
                continue
            
            # Campos Técnicos
            if line.startswith('CAS'):
                entry_data["cas_number"] = line.replace('CAS', '').strip()
                continue
            if line.startswith('sbl'):
                entry_data["simbolo"] = line.replace('sbl', '').strip()
                continue

            # Traduções
            # Tratamento especial para Português que tem [PT] e [BR]
            pt_match = re.match(r'^pt\s+\[(PT|BR)\]\s+(.*)', line)
            lang_match = re.match(r'^([a-z]{2})\s+(.*)', line)
            
            if pt_match:
                tipo = "português_" + pt_match.group(1).lower()
                if "traduções" not in entry_data: entry_data["traduções"] = {}
                entry_data["traduções"][tipo] = [t.strip() for t in pt_match.group(2).split(';') if t.strip()]
                continue
            elif lang_match and lang_match.group(1) in codigos_linguas:
                lang = lang_match.group(1)
                if "traduções" not in entry_data: entry_data["traduções"] = {}
                entry_data["traduções"][lang] = [t.strip() for t in lang_match.group(2).split(';') if t.strip()]
                continue

            # Tema e Definição (Tema é sempre em MAIÚSCULAS seguido de ponto)
            tema_match = re.match(r'^([A-ZÀ-Ú\s]{3,})\.\s*(.*)', line)
            if tema_match:
                entry_data["tema"] = tema_match.group(1).strip()
                if tema_match.group(2):
                    entry_data["definição"] = tema_match.group(2).strip()
                current_field = "definição"
                continue
            
            # Notas
            if line.startswith('Nota:'):
                if "notas" not in entry_data: entry_data["notas"] = []
                entry_data["notas"].append(line.replace('Nota:', '').strip())
                current_field = "nota"
                continue
            
            # Continuação de texto (Definição ou Nota que quebrou linha)
            if current_field == "definição" and "definição" in entry_data:
                entry_data["definição"] += " " + line
            elif current_field == "nota" and "notas" in entry_data:
                entry_data["notas"][-1] += " " + line

        # Decidir se é completa ou parcial
        if "tema" in entry_data and "definição" in entry_data:
            completas.append(entry_data)
        else:
            parciais.append(entry_data)

    return {
        "estatisticas": {
            "total_entradas": len(completas) + len(parciais),
            "completas": len(completas),
            "parciais": len(parciais),
            "linguas_disponiveis": ["ca"] + codigos_linguas
        },
        "entradas_completas": completas,
        "entradas_parciais": parciais
    }

# Execução
resultado_final = processar_dicionario_covid("pdfs/dicionario_covid.txt")

with open("dicionario_covid_final.json", "w", encoding="UTF-8") as f:
    json.dump(resultado_final, f, indent=4, ensure_ascii=False)

print("Processamento terminado com sucesso.")



import re
import json

def limpar_texto(texto):
    # 1. Remover números de página isolados e cabeçalhos de 3 letras (Ex: 15, 16, ACI, ADJ)
    texto = re.sub(r'\n\d+\s*\n', '\n', texto)
    texto = re.sub(r'\n[A-Z]{3}\s*\n', '\n', texto)
    
    # 2. Corrigir palavras cortadas por hifenização no final da linha (ex: "encon- tram")
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
    
    # 3. Normalizar espaços e carateres de controlo (como o \u0007 que vimos antes)
    texto = "".join(ch for ch in texto if ch.isprintable() or ch == '\n')
    
    return texto

def processar_glossario(caminho_input, caminho_output):
    try:
        with open(caminho_input, "r", encoding="utf8") as f:
            conteudo = f.read()
    except UnicodeDecodeError:
        with open(caminho_input, "r", encoding="latin1") as f:
            conteudo = f.read()

    texto_limpo = limpar_texto(conteudo)

    # A expressão regular mágica:
    # Ela procura um bloco que termina quando encontra o próximo termo 
    # (um termo é seguido por "Categoria:" ou "Ver ")
    blocos = re.split(r'\n(?=[^\n]+\n(?:Categoria:|Ver ))', texto_limpo)
    
    resultados = []
    
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
            
        linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
        
        # Estrutura: Entrada com Categoria e Descrição
        if "Categoria:" in bloco:
            # O termo pode ter mais de uma linha se o split falhar em casos raros
            idx_cat = next(i for i, v in enumerate(linhas) if "Categoria:" in v)
            termo = " ".join(linhas[:idx_cat])
            categoria = linhas[idx_cat].replace("Categoria:", "").strip()
            descricao = " ".join(linhas[idx_cat+1:])
            
            resultados.append({
                "id": len(resultados) + 1,
                "termo": termo,
                "categoria": categoria,
                "definicao": descricao
            })
            
        # Estrutura: Remissiva (Ver...)
        elif "Ver " in bloco:
            idx_ver = next(i for i, v in enumerate(linhas) if v.startswith("Ver "))
            termo = " ".join(linhas[:idx_ver])
            referencia = linhas[idx_ver].replace("Ver ", "").strip().rstrip('.')
            
            resultados.append({
                "id": len(resultados) + 1,
                "termo": termo,
                "ver_tambem": referencia
            })

    # Guardar o ficheiro JSON final
    output_dict = {
        "Glossário Ministério da Saúde": resultados,
        "metadados": {
            "total_entradas": len(resultados),
            "fonte": caminho_input
        }
    }

    with open(caminho_output, "w", encoding="utf8") as f_json:
        json.dump(output_dict, f_json, indent=4, ensure_ascii=False)

    print(f"Sucesso! {len(resultados)} entradas processadas no ficheiro {caminho_output}")

# Execução
processar_glossario("pdfs/glossario_ministerio_saude.txt", "glossario_saude_final.json")


from bs4 import BeautifulSoup
import json

from bs4 import BeautifulSoup
import json

from bs4 import BeautifulSoup
import json

def processar_glossario_html(caminho_input, caminho_output):
    # 1. Abrir o ficheiro
    f = open(caminho_input, "r", encoding="utf-8")
    conteudo = f.read()
    f.close()

    soup = BeautifulSoup(conteudo, "xml")

    res = []
    todos_textos = soup.find_all("text")

    entrada_atual = None
    # Flags para controlar onde estamos
    esperando_valor_categoria = False
    ja_tem_campos_extra = False # Indica se já saímos do nome do termo

    for t in todos_textos:
        font_id = t.get("font")
        texto = t.get_text().strip()

        # Ignorar lixo e números de página
        if not texto or texto.isdigit() or len(texto) <= 1:
            continue

        # SE FOR FONTE 1 (Pode ser Termo ou continuação do Termo)
        if font_id == "1":
            # Se encontrarmos Bold e já tínhamos categoria ou definição, 
            # ENTÃO isto é obrigatoriamente um NOVO termo.
            if entrada_atual and ja_tem_campos_extra:
                res.append(entrada_atual)
                entrada_atual = {"id": len(res) + 1, "termo": texto}
                ja_tem_campos_extra = False
                esperando_valor_categoria = False
            
            # Se já temos entrada mas ainda não saímos do nome do termo, juntamos
            elif entrada_atual and not ja_tem_campos_extra:
                entrada_atual["termo"] += " " + texto
            
            # Se não há entrada nenhuma, criamos a primeira
            else:
                entrada_atual = {"id": len(res) + 1, "termo": texto}
                ja_tem_campos_extra = False

        # SE FOR CATEGORIA, DEFINIÇÃO OU VER
        elif entrada_atual:
            ja_tem_campos_extra = True # Bloqueia a adição de mais texto ao "termo"

            # Caso 1: Marcador de Categoria
            if "Categoria:" in texto or font_id == "2":
                entrada_atual["categoria"] = texto.replace("Categoria:", "").strip()
                if not entrada_atual["categoria"]:
                    esperando_valor_categoria = True
            
            # Caso 2: Remissiva
            elif texto.startswith("Ver "):
                entrada_atual["ver_tambem"] = texto.replace("Ver ", "").strip()
                esperando_valor_categoria = False

            # Caso 3: Conteúdo (Fonte 3)
            elif font_id == "3":
                if esperando_valor_categoria:
                    entrada_atual["categoria"] = texto
                    esperando_valor_categoria = False
                else:
                    if "definicao" not in entrada_atual:
                        entrada_atual["definicao"] = texto
                    else:
                        entrada_atual["definicao"] += " " + texto

    # Guardar a última entrada
    if entrada_atual:
        res.append(entrada_atual)

    # LIMPEZA DE HIFENIZAÇÃO (Final)
    for item in res:
        for chave in ["termo", "categoria", "definicao"]:
            if chave in item:
                item[chave] = item[chave].replace("- ", "").strip()

    # 2. Guardar o JSON
    f_out = open(caminho_output, "w", encoding="utf-8")
    json.dump(res, f_out, indent=4, ensure_ascii=False)
    f_out.close()

    print(f"Sucesso! {len(res)} termos processados.")
processar_glossario_html("pdfs/glossario_ministerio_saude.html.xml", "glossario_ministerio_xml.json")



from bs4 import BeautifulSoup
import json

def processar_dicionario_covid_html(caminho_input, caminho_output):
    f = open(caminho_input, "r", encoding="utf-8")
    conteudo = f.read()
    f.close()

    soup = BeautifulSoup(conteudo, "xml")
    res = []
    entrada_atual = None
    lingua_atual = None
    
    codigos_linguas = ['oc', 'eu', 'gl', 'es', 'en', 'fr', 'pt', 'nl', 'ar']
    # Categorias lexicais comuns no dicionário
    cat_lexicais = ['n m', 'n f', 'n', 'adj', 'v', 'n f pl', 'n m pl']

    todos_textos = soup.find_all("text")

    for t in todos_textos:
        font_id = t.get("font")
        texto = t.get_text().strip()
        
        if not texto:
            continue

        # 1. NOVO TERMO (Número isolado)
        if font_id == "1" and re.match(r'^\d+$', texto):
            if entrada_atual:
                res.append(entrada_atual)
            
            entrada_atual = {
                "id": texto,
                "termo_catalão": "",
                "categoria_lexical": "",
                "traduções": {},
                "definicao": ""
            }
            lingua_atual = None
            continue

        if entrada_atual:
            # 2. CATEGORIA LEXICAL (Geralmente font 3 e está na lista de categorias)
            if font_id == "3" and (texto in cat_lexicais or texto.startswith('n ')):
                # Se ainda não mudámos para uma língua estrangeira, a categoria é do termo principal
                if not lingua_atual:
                    entrada_atual["categoria_lexical"] = texto
                continue # Não queremos guardar isto como tradução nem como termo

            # 3. NOME DO TERMO (Catalão) - Font 2 antes de entrar nas línguas
            if font_id == "2" and not lingua_atual and "ETIOPATOGÈNIA" not in texto and "PRINCIPIS" not in texto:
                if entrada_atual["termo_catalão"]:
                    entrada_atual["termo_catalão"] += " " + texto
                else:
                    entrada_atual["termo_catalão"] = texto

            # 4. IDENTIFICAR A LÍNGUA (Siglas específicas)
            # Nota: usamos 'in' porque às vezes vem 'pt [BR]' ou 'pt [PT]'
            sigla_detectada = None
            for sigla in codigos_linguas:
                if texto.startswith(sigla) and font_id == "3":
                    sigla_detectada = sigla
                    break
            
            if sigla_detectada:
                lingua_atual = sigla_detectada
                if lingua_atual not in entrada_atual["traduções"]:
                    entrada_atual["traduções"][lingua_atual] = []
                continue

            # 5. TRADUÇÃO (Font 1 ou 4 após a língua, ignorando categorias lexicais)
            elif lingua_atual and font_id in ["1", "4"]:
                if "ETIOPATOGÈNIA" in texto or "PRINCIPIS" in texto:
                    lingua_atual = None
                else:
                    # Limpar o ponto e vírgula e o carácter \u0007
                    limpo = texto.replace('\x07', '').replace(';', '').strip()
                    if limpo and limpo not in cat_lexicais:
                        entrada_atual["traduções"][lingua_atual].append(limpo)

            # 6. DEFINIÇÃO
            elif "ETIOPATOGÈNIA" in texto or "PRINCIPIS ACTIUS" in texto:
                entrada_atual["definicao"] += texto
                lingua_atual = None
            
            elif font_id == "1" and entrada_atual["definicao"]:
                entrada_atual["definicao"] += " " + texto

    if entrada_atual:
        res.append(entrada_atual)

    # LIMPEZA FINAL: Juntar as listas de traduções em strings limpas
    for item in res:
        for lang in item["traduções"]:
            # Juntar as partes da tradução e remover espaços duplos
            texto_final = " ".join(item["traduções"][lang])
            item["traduções"][lang] = texto_final.replace("  ", " ").strip()

    # Guardar o ficheiro
    f_out = open(caminho_output, "w", encoding="utf-8")
    json.dump(res, f_out, indent=4, ensure_ascii=False)
    f_out.close()
    print(f"Processado: {len(res)} termos.")

processar_dicionario_covid_html("pdfs/dicionario_covid.xml", "covid_final.json")