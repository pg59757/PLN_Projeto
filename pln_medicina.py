import re
import json

# ---------------------------------------------------------
# 1) Ler ficheiro
# ---------------------------------------------------------
with open("data/medicina_raw.txt", "r", encoding="utf-8") as f:
    texto = f.read()

# ---------------------------------------------------------
# 2) Remover tudo antes da primeira entrada real (id 1)
# ---------------------------------------------------------
if "\n1 " in texto:
    texto = texto.split("\n1 ")[1]
    texto = "1 " + texto

# ---------------------------------------------------------
# 3) Limpeza básica
# ---------------------------------------------------------
texto = re.sub(r"\f", "", texto)

# ---------------------------------------------------------
# 4) Criar marcas para separar entradas
# ---------------------------------------------------------
texto = re.sub(r"\n(?=\d+\s)", "\n@", texto)
texto = re.sub(r"\n(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ].+Vid\.-)", "\n#", texto)

# ---------------------------------------------------------
# 5) Separar entradas
# ---------------------------------------------------------
entradas_completas = re.split(r"@", texto)
entradas_alternativas = re.split(r"#", texto)

vocabulario = []

# ---------------------------------------------------------
# 6) Função auxiliar
# ---------------------------------------------------------
def limpa(linha):
    linha = linha.strip()
    linha = re.sub(r"\s+", " ", linha)
    return linha


# ---------------------------------------------------------
# 7) Processar ENTRADAS COMPLETAS
# ---------------------------------------------------------
for e in entradas_completas:
    e = e.strip()
    if not re.match(r"^\d+", e):
        continue

    linhas = e.split("\n")

    m = re.match(r"^(\d+)\s+(.+?)\s+([mf])$", linhas[0])
    if not m:
        continue

    id_ = int(m.group(1))
    termo = m.group(2)
    genero = m.group(3)

    entrada = {
        "tipo_entrada": "definicao_completa",
        "id_entrada": id_,
        "termo_galego": {
            "palavra": termo,
            "genero_palavra": genero,
            "sinonimos_galego": []
        },
        "tema": [],
        "traducoes": {},   # <- substituiu os campos separados por língua
        "nota": None
    }

    i = 1
    while i < len(linhas):
        linha_bruta = linhas[i]
        linha = limpa(linha_bruta)

        # Área temática
        if (
            re.match(r"^[A-ZÁÉÍÓÚ].+", linha)
            and not linha.startswith(("SIN.-", "es ", "en ", "pt ", "la ", "Nota"))
        ):
            entrada["tema"].append(linha)

         # Sinónimos galegos
        elif linha.startswith("SIN.-"):
            sin = linha.replace("SIN.-", "").strip()
            entrada["termo_galego"]["sinonimos_galego"] = sin

        # Espanhol
        elif linha.startswith("es "):
            vals = [s.strip() for s in linha[3:].split(";")]
            entrada["traducoes"]["espanhol"] = vals[0] if len(vals) == 1 else "; ".join(vals)

        # Inglês
        elif linha.startswith("en "):
            vals = [s.strip() for s in linha[3:].split(";")]
            entrada["traducoes"]["inglês"] = vals[0] if len(vals) == 1 else "; ".join(vals)

        # Português
        elif linha.startswith("pt "):
            vals = [s.strip() for s in linha[3:].split(";")]
            entrada["traducoes"]["português"] = vals[0] if len(vals) == 1 else "; ".join(vals)

        # Latim
        elif linha.startswith("la "):
            vals = [s.strip() for s in linha[3:].split(";")]
            entrada["traducoes"]["latim"] = vals[0] if len(vals) == 1 else "; ".join(vals)

        # Nota (multi-linha)
        elif linha.startswith("Nota.-"):
            nota = linha.replace("Nota.-", "").strip()

            j = i + 1
            while j < len(linhas):
                prox = limpa(linhas[j])
                if prox.startswith(("es ", "en ", "pt ", "la ", "SIN.-", "Nota.-")):
                    break
                if re.match(r"^\d+\s", prox):
                    break
                if prox == "":
                    break
                nota += " " + prox
                j += 1

            entrada["nota"] = nota
            i = j
            continue

        i += 1

    vocabulario.append(entrada)


# ---------------------------------------------------------
# 8) Processar ENTRADAS ALTERNATIVAS
# ---------------------------------------------------------
for e in entradas_alternativas:
    e = e.strip()
    if "Vid.-" not in e:
        continue

    m = re.match(r"(.+?)\s+Vid\.-\s+(.+)", e)
    if not m:
        continue

    termo = limpa(m.group(1))
    equivalente = limpa(m.group(2))

    entrada = {
        "tipo_entrada": "alternativa",
        "termo_galego": {
            "palavra": termo,
            "genero_palavra": None
        },
        "termo_equivalente": equivalente
    }

    vocabulario.append(entrada)


# ---------------------------------------------------------
# 9) Guardar JSON final
# ---------------------------------------------------------
with open("pln_vocab_medicina.json", "w", encoding="utf-8") as f:
    json.dump({"Vocabulário médico": vocabulario}, f, ensure_ascii=False, indent=4)