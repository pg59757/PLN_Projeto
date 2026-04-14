import re
import json

f = open("pdfs/dicionario_covid.txt", "r", encoding="utf8")
texto = f.read()
f.close()

# Passo 1: Remoção das quebras de página e cabeçalhos de página
texto = re.sub(r'\f', '', texto)

# Passo 2: Remover cabeçalhos/rodapés do PDF (linhas com "QUADERNS", letras soltas de índice)
texto = re.sub(r'\nQUADERNS.*?\n', '\n', texto)
texto = re.sub(r'\n[A-Z]\n', '\n', texto)          # letra isolada de separador de índice
texto = re.sub(r'\n\d{1,3}\n', '\n', texto)         # número de página isolado

# Passo 3: Remoção de linhas vazias múltiplas
texto = re.sub(r'\n{2,}', '\n', texto)

# Prefixos de língua e respetivo nome
# Ordem importa: os mais específicos primeiro (pt [PT] e pt [BR] antes de pt simples)
LINGUAS = [
    ('pt [PT]', 'português (PT)'),
    ('pt [BR]', 'português (BR)'),
    ('oc',      'occitan'),
    ('eu',      'euskera'),
    ('gl',      'galego'),
    ('es',      'espanhol'),
    ('en',      'inglês'),
    ('fr',      'francês'),
    ('pt',      'português'),
    ('nl',      'neerlandês'),
    # árabe não é extraído (caracteres RTL problemáticos no txt)
]

def limpar_tradução(t):
    """Remove sufixos gramaticais (n m, n f, adj, etc.) e espaços."""
    t = t.strip()
    # Remover sufixos gramaticais no fim
    t = re.sub(r'\s+(?:n\s*[mf]?|adj|adv)(?:\s*;.*)?$', '', t).strip()
    # Remover ponto e vírgula sobrante no fim
    t = t.rstrip(';').strip()
    return t

def extrair_traducoes(bloco):
    """Extrai as traduções de um bloco de texto de uma entrada."""
    traducoes = {}
    linhas = bloco.split('\n')
    
    for prefixo, nome in LINGUAS:
        # Construir padrão que garante que 'pt' não apanha 'pt [PT]' ou 'pt [BR]'
        if prefixo == 'pt':
            # pt simples: não pode ser seguido de ' ['
            pat = re.compile(
                r'(?:^|\n)\s*pt(?!\s*\[)\s+([^\n]+)',
                re.MULTILINE
            )
        else:
            pat = re.compile(
                r'(?:^|\n)\s*' + re.escape(prefixo) + r'\s+([^\n]+)',
                re.MULTILINE
            )
        
        m = pat.search(bloco)
        if m:
            valor = m.group(1).strip()
            valor = limpar_tradução(valor)
            if valor and not re.match(r'^[\x00-\x08\x0b-\x1f]', valor):  # evitar control chars
                traducoes[nome] = valor
    
    return traducoes

def extrair_definicao(bloco):
    """Extrai a definição após a categoria temática."""
    categorias = (
        r'ETIOPATOG[ÈE]NIA|CL[IÍ]NICA|EPIDEMIOLOGIA|TRACTAMENT|PREVENCI[OÓ]|'
        r'ENTORN SOCIAL|PRINCIPIS ACTIUS|DIAGN[ÒO]STIC|FARMACOLOGIA'
    )
    m = re.search(rf'({categorias})\.\s*(.+?)(?=\nNota:|\Z)', bloco, re.DOTALL)
    if m:
        categoria = m.group(1)
        definicao = m.group(2).strip()
        definicao = re.sub(r'\n', ' ', definicao).strip()
        return categoria, definicao
    return None, None

# Dividir o texto em blocos por entrada numerada
# Cada entrada começa com: número(s) + espaço + termo
blocos = re.split(r'\n(?=\d+\s+[A-ZÀ-Úa-zà-ú])', texto)

dicionario = {}
remissoes = {}  # entradas do tipo "veg." (ver também)
contagem = 0

for bloco in blocos:
    bloco = bloco.strip()
    if not bloco:
        continue
    
    linhas = bloco.split('\n')
    primeira = linhas[0]
    
    # Extrair número e termo da primeira linha
    m = re.match(r'^(\d+)\s+(.+?)(?:\s+n\s*[mf].*)?$', primeira)
    if not m:
        continue
    
    numero = int(m.group(1))
    termo_raw = m.group(2).strip()
    # Limpar sufixos gramaticais do termo
    termo = re.sub(r'\s+n\s*[mf]?\s*$', '', termo_raw).strip()
    
    if not termo:
        continue
    
    # Verificar se é remissão ("veg." = ver)
    segunda = linhas[1].strip() if len(linhas) > 1 else ''
    if segunda.startswith('veg.') or segunda.startswith('sin.') and 'veg.' in bloco:
        # Guarda para referência mas não inclui no dicionário principal
        alvo_m = re.search(r'veg\.\s+(.+?)\s+n\s*[mf]', bloco)
        if alvo_m:
            remissoes[termo] = alvo_m.group(1).strip()
        continue
    
    traducoes = extrair_traducoes(bloco)
    categoria, definicao = extrair_definicao(bloco)
    
    entrada = {
        "número": numero,
        "catalão": termo,
        "traduções": traducoes,
    }
    if categoria and definicao:
        entrada["categoria"] = categoria
        entrada["definição"] = definicao
    
    dicionario[termo] = entrada
    contagem += 1

print(f"Total de entradas extraídas: {contagem}")
print(f"Total de remissões ignoradas: {len(remissoes)}")

# Guardar JSON
def escreve_json(d, filename):
    ficheiro = open(filename, "w", encoding="utf8")
    json.dump(d, ficheiro, indent=4, ensure_ascii=False)
    ficheiro.close()

escreve_json(dicionario, "dicionario_covid_claude.json")
print("Ficheiro JSON criado: dicionario_covid.json")
