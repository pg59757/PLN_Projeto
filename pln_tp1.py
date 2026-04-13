import re
import json

# ---------------------------------------------------------
# 1) Ler ficheiro
# ---------------------------------------------------------
with open("data/medicina_raw.txt", "r", encoding="utf-8") as f:
    texto = f.read()

# ---------------------------------------------------------
# 2) Limpeza básica
# ---------------------------------------------------------
texto = re.sub(r"\f", "", texto)   # remover quebras de página

# ---------------------------------------------------------
# 3) Criar marcas para separar entradas
# ---------------------------------------------------------

# Entradas completas começam com número
texto = re.sub(r"\n(?=\d+\s)", "\n@", texto)

# Entradas remissivas começam com texto e têm "Vid.-"
texto = re.sub(r"\n(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ].+Vid\.-)", "\n#", texto)

# ---------------------------------------------------------
# 4) Separar entradas
# ---------------------------------------------------------
entradas_completas = re.split(r"@", texto)
entradas_remissivas = re.split(r"#", texto)

# Lista final
vocabulario = []

# ---------------------------------------------------------
# 5) Função auxiliar
# ---------------------------------------------------------
def limpa(linha):
    linha = linha.strip()
    linha = re.sub(r"\s+", " ", linha)
    return linha


# ---------------------------------------------------------
# 6) Processar ENTRADAS COMPLETAS
# ---------------------------------------------------------
for e in entradas_completas:
    e = e.strip()
    if not re.match(r"^\d+", e):
        continue

    linhas = e.split("\n")

    # Linha 1 → id + termo + categoria
    m = re.match(r"^(\d+)\s+(.+?)\s+([mf])$", linhas[0])
    if not m:
        continue

    id_ = int(m.group(1))
    termo = m.group(2)
    categoria = m.group(3)

    entrada = {
        "entrada": "definicao",
        "id": id_,
        "termo_galego": {
            "palavra": termo,
            "classe_gramatical": categoria,
            "sinonimos_galego": []
        },
        "tema": [],
        "espanhol": [],
        "ingles": [],
        "portugues": [],
        "latim": [],
        "nota": None
    }

    # Processar restantes linhas
    for linha in linhas[1:]:
        linha = limpa(linha)

        # Área temática (linha com palavra inicial maiúscula e sem prefixos)
        if (
            re.match(r"^[A-ZÁÉÍÓÚ].+", linha)
            and not linha.startswith(("SIN.-", "es ", "en ", "pt ", "la ", "Nota"))
        ):
            entrada["tema"].append(linha)

        # Sinónimos galegos
        elif linha.startswith("SIN.-"):
            sin = linha.replace("SIN.-", "").strip()
            entrada["termo_galego"]["sinonimos_galego"] = [
                s.strip() for s in sin.split(";")
            ]

        # Espanhol
        elif linha.startswith("es "):
            entrada["espanhol"] = [s.strip() for s in linha[3:].split(";")]

        # Inglês
        elif linha.startswith("en "):
            entrada["ingles"] = [s.strip() for s in linha[3:].split(";")]

        # Português
        elif linha.startswith("pt "):
            entrada["portugues"] = [s.strip() for s in linha[3:].split(";")]

        # Latim
        elif linha.startswith("la "):
            entrada["latim"] = [s.strip() for s in linha[3:].split(";")]

        # Nota
        elif linha.startswith("Nota.-"):
            entrada["nota"] = linha.replace("Nota.-", "").strip()

    vocabulario.append(entrada)


# ---------------------------------------------------------
# 7) Processar ENTRADAS REMISSIVAS
# ---------------------------------------------------------
for e in entradas_remissivas:
    e = e.strip()
    if "Vid.-" not in e:
        continue

    m = re.match(r"(.+?)\s+Vid\.-\s+(.+)", e)
    if not m:
        continue

    termo = limpa(m.group(1))
    destino = limpa(m.group(2))

    entrada = {
        "entrada": "remissiva",
        "termo_galego": {
            "palavra": termo,
            "classe_gramatical": None
        },
        "remete_para": destino
    }

    vocabulario.append(entrada)


# ---------------------------------------------------------
# 8) Guardar JSON final
# ---------------------------------------------------------
with open("pln_tp1.json", "w", encoding="utf-8") as f:
    json.dump({"Vocabulário médico": vocabulario}, f, ensure_ascii=False, indent=4)
