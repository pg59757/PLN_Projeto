from flask import Flask, render_template, redirect, url_for, request
import json
import os
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

DATA_FILE = "dicionario_unificado.json"

# Mapeamento sigla → nome por extenso (para display nos templates)
LINGUA_LABEL = {
    "es":    "Espanhol",
    "en":    "Inglês",
    "pt":    "Português",
    "pt_PT": "Português (PT)",
    "pt_BR": "Português (BR)",
    "la":    "Latim",
    "fr":    "Francês",
    "eu":    "Euskera",
    "nl":    "Holandês",
    "oc":    "Occitan",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalizar(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', texto.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def carregar_dados():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler: {e}")
        return {"vocab": []}

def guardar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def get_conceitos():
    return carregar_dados().get("vocab", [])

# ─── Artigos para IR ──────────────────────────────────────────────────────────

ARTIGOS = [
    {
        "id": 1,
        "titulo": "COVID-19: Pathophysiology and Clinical Manifestations",
        "autores": "Silva J, Costa M",
        "ano": 2021,
        "resumo": "COVID-19 is caused by SARS-CoV-2, a novel coronavirus that emerged in Wuhan, China. The virus primarily affects the respiratory system, causing symptoms ranging from mild fever and cough to severe pneumonia and acute respiratory distress syndrome (ARDS). The pathophysiology involves viral entry via ACE2 receptors, triggering an intense inflammatory response and cytokine storm in severe cases. Common clinical manifestations include fever, dyspnea, anosmia, and fatigue. Risk factors for severe disease include advanced age, obesity, diabetes, and cardiovascular disease.",
        "keywords": ["COVID-19", "SARS-CoV-2", "coronavirus", "pneumonia", "cytokine storm", "ACE2"]
    },
    {
        "id": 2,
        "titulo": "Diabetes Mellitus Type 2: Current Management Strategies",
        "autores": "Fernandes A, Rocha P",
        "ano": 2022,
        "resumo": "Type 2 diabetes mellitus is a chronic metabolic disorder characterized by insulin resistance and relative insulin deficiency. Management involves lifestyle modification, including dietary changes and physical activity, alongside pharmacological therapy. First-line pharmacotherapy includes metformin, which reduces hepatic glucose production. Additional agents such as SGLT2 inhibitors and GLP-1 receptor agonists have shown cardiovascular and renal benefits. Monitoring HbA1c levels remains essential for glycemic control assessment. Complications include nephropathy, retinopathy, neuropathy, and cardiovascular disease.",
        "keywords": ["diabetes", "insulin", "metformin", "HbA1c", "glycemia", "metabolic"]
    },
    {
        "id": 3,
        "titulo": "Hypertension: Diagnosis and Treatment Guidelines",
        "autores": "Martins R, Sousa L",
        "ano": 2023,
        "resumo": "Arterial hypertension is defined as persistent systolic blood pressure ≥130 mmHg or diastolic ≥80 mmHg. It is the leading risk factor for cardiovascular and cerebrovascular disease globally. Lifestyle interventions including sodium restriction, weight loss, and regular aerobic exercise form the cornerstone of treatment. Antihypertensive pharmacotherapy includes ACE inhibitors, angiotensin receptor blockers, calcium channel blockers, and thiazide diuretics. Treatment goals aim to reduce blood pressure below 130/80 mmHg in most patients. Resistant hypertension may require combination therapy.",
        "keywords": ["hypertension", "blood pressure", "ACE inhibitor", "cardiovascular", "diuretic"]
    },
    {
        "id": 4,
        "titulo": "Alzheimer's Disease: Biomarkers and Early Detection",
        "autores": "Pereira C, Lima D",
        "ano": 2022,
        "resumo": "Alzheimer's disease is the most common form of dementia, accounting for 60-80% of cases. It is characterized by progressive cognitive decline, memory loss, and behavioral changes. Pathologically, it involves amyloid-beta plaques and neurofibrillary tau tangles. Early biomarkers include cerebrospinal fluid levels of amyloid and tau proteins, as well as PET imaging of amyloid deposition. Current treatments are symptomatic, including cholinesterase inhibitors and NMDA receptor antagonists. Novel disease-modifying therapies targeting amyloid clearance are under investigation.",
        "keywords": ["Alzheimer", "dementia", "amyloid", "tau", "cognitive decline", "biomarker"]
    },
    {
        "id": 5,
        "titulo": "Sepsis: Early Recognition and Management in ICU",
        "autores": "Gomes F, Alves S",
        "ano": 2021,
        "resumo": "Sepsis is a life-threatening organ dysfunction caused by a dysregulated host response to infection. The Sepsis-3 definition uses the SOFA score to identify organ dysfunction. Early recognition is critical and includes monitoring for tachycardia, hypotension, altered mental status, and elevated lactate. Management follows the hour-1 bundle: blood cultures before antibiotics, broad-spectrum antibiotic administration, fluid resuscitation, vasopressors for refractory hypotension, and lactate measurement. Septic shock carries a mortality rate exceeding 40%. Source control and supportive organ care are central to management.",
        "keywords": ["sepsis", "infection", "ICU", "SOFA", "antibiotics", "organ dysfunction", "lactate"]
    },
    {
        "id": 6,
        "titulo": "Cardiovascular Disease: Risk Assessment and Prevention",
        "autores": "Santos T, Correia B",
        "ano": 2023,
        "resumo": "Cardiovascular disease remains the leading cause of mortality worldwide. Risk assessment tools such as the Framingham Risk Score and SCORE2 calculate 10-year event probability. Major modifiable risk factors include hypertension, dyslipidemia, smoking, diabetes, and obesity. Statins reduce LDL cholesterol and cardiovascular events significantly. Antiplatelet therapy with aspirin is indicated in secondary prevention. Lifestyle modification including Mediterranean diet, regular exercise, and smoking cessation reduces cardiovascular risk substantially. Cardiac rehabilitation improves outcomes after myocardial infarction.",
        "keywords": ["cardiovascular", "heart disease", "cholesterol", "statin", "prevention", "myocardial infarction"]
    },
    {
        "id": 7,
        "titulo": "Asthma: Pathophysiology, Diagnosis and Inhaler Therapy",
        "autores": "Ribeiro H, Moura I",
        "ano": 2022,
        "resumo": "Asthma is a chronic inflammatory airway disease characterized by reversible airflow obstruction, bronchial hyperresponsiveness, and airway remodeling. Allergens, exercise, cold air, and respiratory infections are common triggers. Diagnosis is confirmed by spirometry demonstrating reversible airflow limitation. Short-acting beta-2 agonists (SABA) provide rescue bronchodilation, while inhaled corticosteroids (ICS) form the foundation of maintenance therapy. Severe asthma may require biologic agents targeting IL-5, IL-4/IL-13, or IgE pathways. Regular monitoring of symptoms and lung function guides step-up or step-down treatment.",
        "keywords": ["asthma", "bronchial", "inhaler", "corticosteroid", "bronchodilator", "allergy", "spirometry"]
    },
    {
        "id": 8,
        "titulo": "Acute Myocardial Infarction: Emergency Care and Reperfusion",
        "autores": "Nunes G, Faria J",
        "ano": 2023,
        "resumo": "Acute myocardial infarction results from sudden occlusion of a coronary artery, typically by plaque rupture and thrombus formation. ST-elevation MI (STEMI) requires immediate reperfusion therapy, ideally primary percutaneous coronary intervention (PCI) within 90 minutes of first medical contact. Non-ST-elevation MI (NSTEMI) is managed with anticoagulation, dual antiplatelet therapy, and risk-stratified invasive strategy. Biomarkers including troponin and CK-MB confirm myocardial necrosis. Post-MI care includes beta-blockers, ACE inhibitors, statins, and antiplatelet therapy for secondary prevention.",
        "keywords": ["myocardial infarction", "STEMI", "troponin", "PCI", "coronary", "thrombus", "reperfusion"]
    }
]

# ─── TF-IDF ───────────────────────────────────────────────────────────────────

def build_tfidf():
    corpus = [f"{a['titulo']} {a['resumo']} {' '.join(a['keywords'])}" for a in ARTIGOS]
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    return vectorizer, matrix

VECTORIZER, TFIDF_MATRIX = build_tfidf()

def ir_search(query, top_n=5):
    q_vec = VECTORIZER.transform([query])
    scores = cosine_similarity(q_vec, TFIDF_MATRIX).flatten()
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return [
        {**ARTIGOS[i], "score": round(float(s), 3)}
        for i, s in ranked[:top_n] if s > 0
    ]

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    conceitos = get_conceitos()
    temas = {}
    for c in conceitos:
        for t in c.get("tema", []):
            temas[t] = temas.get(t, 0) + 1
    top_temas = sorted(temas.items(), key=lambda x: x[1], reverse=True)[:8]
    return render_template("home.html", total=len(conceitos), top_temas=top_temas)

@app.route("/conceitos")
def listar_conceitos():
    conceitos = get_conceitos()
    query  = request.args.get("q", "").strip()
    tema   = request.args.get("tema", "").strip()
    genero = request.args.get("genero", "").strip()
    ordem  = request.args.get("ordem", "az")

    todos_temas   = sorted(set(t for c in conceitos for t in c.get("tema", [])))
    todos_generos = sorted(set(
        c.get("tg", {}).get("gen") or ""
        for c in conceitos if c.get("tg", {}).get("gen")
    ))

    filtrados = []
    for c in conceitos:
        pal = c.get("tg", {}).get("pal", "")
        if not pal:
            continue
        if query  and normalizar(query) not in normalizar(pal):
            continue
        if tema   and tema not in c.get("tema", []):
            continue
        if genero and c.get("tg", {}).get("gen") != genero:
            continue
        filtrados.append(c)

    if ordem == "az":
        filtrados.sort(key=lambda c: normalizar(c.get("tg", {}).get("pal", "")))
    elif ordem == "za":
        filtrados.sort(key=lambda c: normalizar(c.get("tg", {}).get("pal", "")), reverse=True)
    elif ordem == "tema":
        filtrados.sort(key=lambda c: (
            c.get("tema", [""])[0] if c.get("tema") else "",
            normalizar(c.get("tg", {}).get("pal", ""))
        ))

    page       = int(request.args.get("page", 1))
    per_page   = 60
    total      = len(filtrados)
    pagina     = filtrados[(page - 1) * per_page : page * per_page]
    total_pages = (total + per_page - 1) // per_page

    return render_template("conceitos.html",
        conceitos=pagina, total=total, page=page, total_pages=total_pages,
        query=query, tema=tema, genero=genero, ordem=ordem,
        todos_temas=todos_temas, todos_generos=todos_generos)

@app.route("/conceitos/<designacao>")
def detalhe(designacao):
    conceitos = get_conceitos()
    item = next((c for c in conceitos if c.get("tg", {}).get("pal") == designacao), None)
    if not item:
        return render_template("404.html"), 404
    relacionados = [
        c for c in conceitos
        if c.get("tg", {}).get("pal") != designacao
        and any(t in item.get("tema", []) for t in c.get("tema", []))
    ][:6]
    return render_template("conceito.html", conceito=item,
                           relacionados=relacionados, lingua_label=LINGUA_LABEL)

@app.route("/conceitos/<designacao>/editar", methods=["GET", "POST"])
def editar(designacao):
    dados     = carregar_dados()
    conceitos = dados.get("vocab", [])
    idx = next((i for i, c in enumerate(conceitos)
                if c.get("tg", {}).get("pal") == designacao), None)
    if idx is None:
        return render_template("404.html"), 404
    item = conceitos[idx]

    if request.method == "POST":
        f = request.form
        item["tg"]["gen"] = f.get("genero") or None
        item["tg"]["sin"] = [s.strip() for s in f.get("sinonimos", "").split(",") if s.strip()]
        item["tema"]      = [t.strip() for t in f.get("tema", "").split(",") if t.strip()]
        item["def"]       = f.get("definicao") or None
        item["trad"]      = {k: v for k, v in {
            "pt": f.get("pt", ""),
            "es": f.get("es", ""),
            "en": f.get("en", ""),
            "la": f.get("la", ""),
            "fr": f.get("fr", ""),
        }.items() if v}
        conceitos[idx] = item
        guardar_dados(dados)
        return redirect(url_for("detalhe", designacao=designacao))

    return render_template("editar.html", conceito=item)

@app.route("/conceitos/novo", methods=["GET", "POST"])
def novo_conceito():
    if request.method == "POST":
        f      = request.form
        palavra = f.get("palavra", "").strip()
        if not palavra:
            return render_template("novo.html", erro="O termo galego é obrigatório.")
        dados     = carregar_dados()
        conceitos = dados.get("vocab", [])
        if any(c.get("tg", {}).get("pal") == palavra for c in conceitos):
            return render_template("novo.html", erro="Termo já existe.")
        novo = {
            "tg": {
                "pal": palavra,
                "gen": f.get("genero") or None,
                "sin": [s.strip() for s in f.get("sinonimos", "").split(",") if s.strip()]
            },
            "tema": [t.strip() for t in f.get("tema", "").split(",") if t.strip()],
            "def":  f.get("definicao") or None,
            "trad": {k: v for k, v in {
                "pt": f.get("pt", ""),
                "es": f.get("es", ""),
                "en": f.get("en", ""),
                "la": f.get("la", ""),
                "fr": f.get("fr", ""),
            }.items() if v}
        }
        conceitos.append(novo)
        guardar_dados(dados)
        return redirect(url_for("detalhe", designacao=palavra))
    return render_template("novo.html", erro=None)

@app.route("/ir")
def information_retrieval():
    query = request.args.get("q", "").strip()
    resultados = ir_search(query) if query else []
    return render_template("ir.html", query=query, resultados=resultados, artigos=ARTIGOS)

@app.route("/ir/artigo/<int:artigo_id>")
def artigo(artigo_id):
    art = next((a for a in ARTIGOS if a["id"] == artigo_id), None)
    if not art:
        return render_template("404.html"), 404
    return render_template("artigo.html", artigo=art, query=request.args.get("q", ""))

@app.route("/qa", methods=["GET", "POST"])
def question_answering():
    resposta  = None
    pergunta  = ""
    artigo_id = request.args.get("artigo_id") or request.form.get("artigo_id")
    art = next((a for a in ARTIGOS if a["id"] == int(artigo_id)), None) if artigo_id else None

    if request.method == "POST":
        pergunta  = request.form.get("pergunta", "").strip()
        artigo_id = request.form.get("artigo_id", "")
        if art and pergunta:
            try:
                from transformers import pipeline
                qa = pipeline(
                    "question-answering",
                    model="deepset/minilm-uncased-squad2",
                    tokenizer="deepset/minilm-uncased-squad2"
                )
                r = qa(question=pergunta, context=art["resumo"])
                resposta = {
                    "texto": r["answer"],
                    "score": round(r["score"] * 100, 1),
                    "start": r["start"],
                    "end":   r["end"]
                }
            except Exception as e:
                resposta = {"erro": str(e)}

    return render_template("qa.html", artigo=art, pergunta=pergunta,
                           resposta=resposta, artigos=ARTIGOS)

if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        import subprocess
        subprocess.run(["python", "unificar.py"])
    app.run(host="localhost", port=4003, debug=True)