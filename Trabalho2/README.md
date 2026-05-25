# MedLex — Plataforma Médica PLN (TP2)

## Funcionalidades

- **Vocabulário Médico** — navegação, filtros por tema/género, paginação, busca
- **Enriquecimento** — adicionar/editar termos com definições, sinónimos, traduções
- **Information Retrieval** — pesquisa TF-IDF sobre coleção de artigos científicos
- **Question Answering** — modelo BERT (deepset/minilm-uncased-squad2) via HuggingFace

## Instalação

```bash
pip install -r requirements.txt
```

Para o módulo QA (pesado, ~500MB):
```bash
pip install transformers torch
```

## Executar

```bash
# 1. Gerar o dataset unificado (só na primeira vez)
python3 unificar.py

# 2. Iniciar o servidor
python3 app.py
```

Abrir em: http://localhost:4003

## Estrutura

```
trabalho2/
├── app.py                    # Aplicação Flask principal
├── unificar.py               # Script de unificação do dataset
├── dicionario_unificado.json # Dataset (gerado por unificar.py)
├── requirements.txt
├── data_files/               # Dados originais do TP1
│   ├── medicina.json
│   ├── dicionario_covid.json
│   ├── glossario_enfermagem.json
│   └── glossario_termos_medicos.json
└── templates/
    ├── layout.html
    ├── home.html
    ├── conceitos.html        # Lista com filtros + paginação
    ├── conceito.html         # Detalhe com relacionados
    ├── editar.html           # Edição persistente
    ├── novo.html             # Novo conceito
    ├── ir.html               # Information Retrieval (TF-IDF)
    ├── artigo.html           # Detalhe artigo
    ├── qa.html               # Question Answering (BERT)
    └── 404.html
```
