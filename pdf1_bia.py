'''import re
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
processar_glossario("pdfs/glossario_ministerio_saude.txt", "glossario_saude_final.json")'''



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


