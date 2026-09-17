import os
import json
import re
import sqlite3
import subprocess
import hashlib

try:
    import pymupdf  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    print("[AVISO] PyMuPDF não instalado. As imagens TikZ não serão geradas. Rode: pip install pymupdf")

raiz = os.path.dirname(os.path.abspath(__file__))
arquivo_html = os.path.join(raiz, "index.html")
arquivo_banco = os.path.join(raiz, "questoes.db")
arquivo_dados_json = os.path.join(raiz, "questoes_dados.json")

# Dicionário global para monitorar tudo o que o script faz
ESTATISTICAS = {
    "total_questoes": 0,
    "com_tikz": 0,
    "cache": 0,
    "gerados": 0,
    "erros": 0
}

# =========================================================
# CONFIGURAÇÃO DE FONTE E CORES
# =========================================================
PREAMBULO_FONTE = r"""
\usepackage[T1]{fontenc}
\usepackage[portuguese]{babel}

% --- FONTE PADRÃO ---
\usepackage{helvet} 
\renewcommand{\familydefault}{\sfdefault}
\usepackage{amsmath, amsfonts, amssymb, nccmath, mathastext}

% --- CORES BASE ---
\usepackage{xcolor}
\definecolor{indigo}{HTML}{4F46E5}
\definecolor{CorTitUm}{HTML}{FF6F61}
\definecolor{CorTitDois}{HTML}{FF6F61}
\definecolor{CorTitTres}{HTML}{658894}
\definecolor{CorLinha}{HTML}{B0B0B0} 
\definecolor{metal}{HTML}{7F8C8D}
\definecolor{vidro}{HTML}{3498DB}
\definecolor{ouro}{HTML}{F1C40F}
\definecolor{concreto}{HTML}{95A5A6}
\definecolor{madeira}{HTML}{D35400}
\definecolor{CinzaEscuro}{HTML}{4A4A4A} 
\definecolor{CinzaMedio}{HTML}{848484} 
\definecolor{Cinzablack}{HTML}{353535} 

% --- CORES ESPECÍFICAS DOS EXERCÍCIOS ---
\definecolor{CorNotaBorda}{HTML}{10B981}
\definecolor{CorDicaBorda}{HTML}{17C1BE}
\definecolor{CorDicaFundo}{HTML}{F3FBFB}
\definecolor{PisoVerde}{HTML}{27AE60}
\definecolor{GramaFundo}{HTML}{2ECC71}
\definecolor{AguaPiscina}{HTML}{5DADE2}
\definecolor{asfalto}{HTML}{34495E}
\definecolor{blocoA}{HTML}{E74C3C}
\definecolor{blocoB}{HTML}{3498DB}

% --- PACOTES GRÁFICOS EXTRAS E ESTILOS ---
\usepackage{pgfplots, circuitikz}
\pgfplotsset{compat=1.18}
\tikzset{
    asfalto/.style={fill=asfalto},
    blocoA/.style={fill=blocoA},
    blocoB/.style={fill=blocoB},
    PisoVerde/.style={fill=PisoVerde},
    GramaFundo/.style={fill=GramaFundo},
    AguaPiscina/.style={fill=AguaPiscina},
    CorDicaBorda/.style={fill=CorDicaBorda}
}
"""

MAPA_ANOS = {
    "6_Ano": "6º Ano",
    "7_Ano": "7º Ano",
    "8_Ano": "8º Ano",
    "9_Ano": "9º Ano",
    "1_Serie": "1ª Série (EM)",
    "2_Serie": "2ª Série (EM)",
    "3_Serie": "3ª Série (Intensivo)"
}

def inicializar_banco():
    conn = sqlite3.connect(arquivo_banco)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS questoes;")
    cur.execute("""
        CREATE TABLE questoes (
            id TEXT PRIMARY KEY,
            disciplina TEXT,
            ano TEXT,
            unidade TEXT,
            tipo_caderno TEXT,
            capitulo_indice INTEGER,
            capitulo TEXT,
            numero_questao INTEGER,
            enunciado TEXT,
            codigo_tikz TEXT,
            imagem_tikz TEXT,
            resolucao TEXT,
            nota_pedagogica TEXT,
            contexto_pronto TEXT
        );
    """)
    cur.execute("CREATE INDEX idx_busca_questao ON questoes (disciplina, ano, unidade, tipo_caderno, capitulo_indice, numero_questao);")
    conn.commit()
    return conn

def formatar_id_unidade(pasta_unidade):
    m = re.match(r"([A-Za-z]+)(\d+)", pasta_unidade)
    if m: return f"{m.group(1).upper()} {m.group(2)}"
    return pasta_unidade

def encontrar_pdf(pasta_unidade_completa, tipo, destino):
    pasta_alvo = os.path.join(pasta_unidade_completa, destino)
    if not os.path.exists(pasta_alvo): return None
    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_alvo):
        if arq.endswith(".pdf") and tag in arq:
            return os.path.relpath(os.path.join(pasta_alvo, arq), raiz).replace(os.sep, "/")
    return None

def encontrar_tex(pasta_unidade_completa, tipo):
    pasta_fonte = os.path.join(pasta_unidade_completa, "fonte_tex")
    if not os.path.exists(pasta_fonte): return None, None
    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_fonte):
        if arq.endswith("_BASE.tex") and tag in arq:
            caminho_abs = os.path.join(pasta_fonte, arq)
            return os.path.relpath(caminho_abs, raiz).replace(os.sep, "/"), caminho_abs
    return None, None

def compilar_tikz_para_png(tikz_code, id_questao, pasta_unidade_completa, pasta_fonte_tex):
    if not HAS_FITZ or not tikz_code.strip():
        return "NENHUM", ""
    
    pasta_imagens = os.path.join(pasta_unidade_completa, "imagens_tikz")
    if not os.path.exists(pasta_imagens):
        os.makedirs(pasta_imagens)

    hash_atual = hashlib.md5(tikz_code.encode('utf-8')).hexdigest()
    
    caminho_tex = os.path.join(pasta_imagens, f"{id_questao}.tex")
    caminho_pdf = os.path.join(pasta_imagens, f"{id_questao}.pdf")
    caminho_png = os.path.join(pasta_imagens, f"{id_questao}.png")
    caminho_hash = os.path.join(pasta_imagens, f"{id_questao}.hash")
    caminho_relativo_png = os.path.relpath(caminho_png, raiz).replace(os.sep, "/")

    if os.path.exists(caminho_png) and os.path.exists(caminho_hash):
        with open(caminho_hash, "r", encoding="utf-8") as f:
            hash_salvo = f.read().strip()
        if hash_atual == hash_salvo:
            return "CACHE", caminho_relativo_png

    tex_code = f"""\\documentclass[tikz,border=2mm]{{standalone}}
\\usepackage[utf8]{{inputenc}}
{PREAMBULO_FONTE}
\\usetikzlibrary{{shadows,shapes,arrows,positioning,calc,patterns,shapes.misc,angles,quotes,decorations.markings}}
\\newlength{{\\larguraTikz}}
\\setlength{{\\larguraTikz}}{{10cm}}
\\begin{{document}}
{tikz_code}
\\end{{document}}
"""
    with open(caminho_tex, "w", encoding="utf-8") as f:
        f.write(tex_code)

    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", pasta_imagens, caminho_tex], 
            cwd=pasta_fonte_tex if pasta_fonte_tex else raiz,
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  [ERRO TIKZ] A questão {id_questao} falhou na compilação.")
        if e.stdout:
            for linha in e.stdout.split('\n'):
                if linha.startswith('!'):
                    print(f"     -> CAUSA: {linha.strip()}")
                    break
        return "ERRO", ""

    try:
        doc = fitz.open(caminho_pdf)
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        pix.save(caminho_png)
        doc.close()
        
        with open(caminho_hash, "w", encoding="utf-8") as f:
            f.write(hash_atual)
            
        for ext in [".tex", ".pdf", ".aux", ".log"]:
            arq_temp = os.path.join(pasta_imagens, f"{id_questao}{ext}")
            if os.path.exists(arq_temp):
                os.remove(arq_temp)
                
        return "GERADO", caminho_relativo_png
    except Exception as e:
        print(f"  [ERRO PNG] Falha ao converter PDF para a questão {id_questao}: {e}")
        return "ERRO", ""

def indexar_questoes_no_banco(caminho_abs_tex, prefixo_material, disciplina, ano, unidade, tipo_caderno, pasta_unidade_completa, cur):
    if not caminho_abs_tex or not os.path.exists(caminho_abs_tex):
        return

    pasta_fonte_tex = os.path.dirname(caminho_abs_tex)

    try:
        with open(caminho_abs_tex, "r", encoding="utf-8", errors="ignore") as f:
            conteudo = f.read()
    except Exception:
        return

    secoes = re.split(r'\\subsection\*\{([^}]+)\}', conteudo)

    def salvar_bloco(num_q, corpo_bruto, capitulo_nome, idx_cap):
        corpo_quest = re.split(r'\\subsubsection\*|\\subsection\*', corpo_bruto)[0]

        m_enun = re.search(r'\\begin\{enunciadoLiteral\}(.*?)\\end\{enunciadoLiteral\}', corpo_quest, re.DOTALL)
        enunciado = m_enun.group(1).strip() if m_enun else ""

        m_tikz = re.search(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', corpo_quest, re.DOTALL)
        tikz = m_tikz.group(1).strip() if m_tikz else ""

        m_resol = re.search(r'\\begin\{tcolorbox\}(?:\[.*?\])?(.*?)\\end\{tcolorbox\}', corpo_quest, re.DOTALL)
        resolucao = m_resol.group(1).strip() if m_resol else ""

        m_nota = re.search(r'\\begin\{boxexplicacao\}(.*?)\\end\{boxexplicacao\}', corpo_quest, re.DOTALL)
        nota_pedagogica = m_nota.group(1).strip() if m_nota else ""

        id_unico = f"{prefixo_material}__C{idx_cap:02d}__Q{num_q:02d}"
        
        # AUDITORIA E ESTATÍSTICAS
        ESTATISTICAS["total_questoes"] += 1
        caminho_imagem = ""
        
        if tikz:
            ESTATISTICAS["com_tikz"] += 1
            status, caminho_imagem = compilar_tikz_para_png(tikz, id_unico, pasta_unidade_completa, pasta_fonte_tex)
            
            if status == "GERADO":
                ESTATISTICAS["gerados"] += 1
                print(f"  [NOVO] Imagem gerada: {id_unico}")
            elif status == "CACHE":
                ESTATISTICAS["cache"] += 1
            elif status == "ERRO":
                ESTATISTICAS["erros"] += 1

        contexto = f"--- ENUNCIADO OFICIAL DA QUESTÃO {num_q} (Capítulo {idx_cap}: {capitulo_nome}) ---\n{enunciado}\n"
        if resolucao: contexto += f"\n--- RESOLUÇÃO E GABARITO OFICIAL ---\n{resolucao}\n"
        if nota_pedagogica: contexto += f"\n--- ORIENTAÇÃO PEDAGÓGICA AO TUTOR ---\n{nota_pedagogica}\n"

        cur.execute("""
            INSERT OR REPLACE INTO questoes 
            (id, disciplina, ano, unidade, tipo_caderno, capitulo_indice, capitulo, numero_questao, enunciado, codigo_tikz, imagem_tikz, resolucao, nota_pedagogica, contexto_pronto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_unico, disciplina, ano, unidade, tipo_caderno, idx_cap, capitulo_nome, num_q, enunciado, tikz, caminho_imagem, resolucao, nota_pedagogica, contexto))

    idx_cap = 1
    if len(secoes) > 0 and secoes[0]:
        partes_iniciais = re.split(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', secoes[0])
        if len(partes_iniciais) > 1:
            for j in range(1, len(partes_iniciais), 2):
                salvar_bloco(int(partes_iniciais[j]), partes_iniciais[j+1], "Lista Principal", idx_cap)
            idx_cap += 1

    for i in range(1, len(secoes), 2):
        cap_titulo = re.sub(r'\\[a-zA-Z]+', '', secoes[i]).replace('{', '').replace('}', '').strip()
        corpo_cap = secoes[i + 1]
        partes_cap = re.split(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', corpo_cap)
        for j in range(1, len(partes_cap), 2):
            salvar_bloco(int(partes_cap[j]), partes_cap[j+1], cap_titulo or f"Capítulo {idx_cap}", idx_cap)
        idx_cap += 1

def extrair_estrutura_tex(caminho_abs_tex):
    if not caminho_abs_tex or not os.path.exists(caminho_abs_tex):
        return []
    try:
        with open(caminho_abs_tex, "r", encoding="utf-8", errors="ignore") as f:
            conteudo = f.read()
    except Exception:
        return []

    secoes = re.split(r'\\subsection\*\{([^}]+)\}', conteudo)
    capitulos = []
    idx_cap = 1

    if len(secoes) > 0 and secoes[0]:
        questoes_avulsas = re.findall(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', secoes[0])
        if questoes_avulsas:
            nums = sorted([int(q) for q in questoes_avulsas])
            capitulos.append({
                "indice": idx_cap,
                "titulo": "Lista Principal",
                "inicio": nums[0],
                "fim": nums[-1],
                "questoes": nums
            })
            idx_cap += 1

    for i in range(1, len(secoes), 2):
        titulo_bruto = secoes[i].strip()
        titulo_limpo = re.sub(r'\\[a-zA-Z]+', '', titulo_bruto).replace('{', '').replace('}', '').strip()
        corpo_cap = secoes[i+1]
        questoes_encontradas = re.findall(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', corpo_cap)
        if questoes_encontradas:
            nums = sorted([int(q) for q in questoes_encontradas])
            capitulos.append({
                "indice": idx_cap,
                "titulo": titulo_limpo or f"Capítulo {idx_cap}",
                "inicio": nums[0],
                "fim": nums[-1],
                "questoes": nums
            })
        idx_cap += 1

    return capitulos

def construir_catalogo(cur_banco):
    catalogo = {
        "Fisica": {"nome": "Física", "tipo": "direto", "anos": {}},
        "Matematica": {
            "nome": "Matemática",
            "tipo": "frentes",
            "frentes": {
                "Algebra": {"nome": "Álgebra", "anos": {}},
                "Geometria": {"nome": "Geometria", "anos": {}}
            }
        }
    }

    pastas_disciplinas = ["Fisica", "Matematica_Algebra", "Matematica_Geometria"]

    for disc in pastas_disciplinas:
        caminho_disc = os.path.join(raiz, disc)
        if not os.path.exists(caminho_disc):
            continue

        for raiz_atual, _, arquivos in os.walk(caminho_disc):
            jsons = [f for f in arquivos if f in ["info_AUT.json", "info_ESC.json"]]
            if not jsons:
                continue

            rel = os.path.relpath(raiz_atual, raiz)
            partes = rel.split(os.sep)
            disciplina_pasta, ano_pasta, unidade_pasta = partes[0], partes[1], partes[-1]
            id_unidade_formatada = formatar_id_unidade(unidade_pasta)
            nome_ano = MAPA_ANOS.get(ano_pasta, ano_pasta)

            if disciplina_pasta == "Fisica":
                anos_dict = catalogo["Fisica"]["anos"]
            elif "Algebra" in disciplina_pasta:
                anos_dict = catalogo["Matematica"]["frentes"]["Algebra"]["anos"]
            elif "Geometria" in disciplina_pasta:
                anos_dict = catalogo["Matematica"]["frentes"]["Geometria"]["anos"]
            else:
                continue

            if ano_pasta not in anos_dict:
                anos_dict[ano_pasta] = {"nome": nome_ano, "unidades": {}}

            materiais = []
            titulo_unidade = ""
            desc_unidade = ""

            jsons_ordenados = sorted(jsons, key=lambda x: 0 if "AUT" in x else 1)

            for j_nome in jsons_ordenados:
                with open(os.path.join(raiz_atual, j_nome), "r", encoding="utf-8") as f:
                    d = json.load(f)

                if not titulo_unidade: titulo_unidade = d.get("titulo", "")
                if not desc_unidade: desc_unidade = d.get("desc", "")

                tipo_mat = d.get("tipo", "Autoral")
                pdf_aluno = encontrar_pdf(raiz_atual, tipo_mat, "publica")
                pdf_prof = encontrar_pdf(raiz_atual, tipo_mat, "restrita")
                caminho_tex, caminho_abs_tex = encontrar_tex(raiz_atual, tipo_mat)
                estrutura_capitulos = extrair_estrutura_tex(caminho_abs_tex)
                prefixo_material = f"{disciplina_pasta}__{ano_pasta}__{unidade_pasta}__{tipo_mat}"

                if caminho_abs_tex:
                    indexar_questoes_no_banco(caminho_abs_tex, prefixo_material, disciplina_pasta, ano_pasta, id_unidade_formatada, tipo_mat, raiz_atual, cur_banco)

                materiais.append({
                    "tipo": tipo_mat,
                    "rotulo": d.get("rotulo", "Caderno de Atividades Suplementar" if tipo_mat == "Autoral" else "Caderno de Atividades"),
                    "id_prefixo": prefixo_material,  
                    "pdf": pdf_aluno,
                    "pdfProf": pdf_prof,
                    "tex": caminho_tex,
                    "trilhas_de_aprendizagem": d.get("trilhas_de_aprendizagem", []),
                    "estrutura": estrutura_capitulos
                })

            anos_dict[ano_pasta]["unidades"][id_unidade_formatada] = {
                "titulo": titulo_unidade,
                "desc": desc_unidade,
                "materiais": materiais
            }

    return catalogo

def exportar_indice_n8n():
    conn = sqlite3.connect(arquivo_banco)
    cur = conn.cursor()
    cur.execute("SELECT id, capitulo, numero_questao, contexto_pronto FROM questoes")
    dados = {
        linha[0]: {
            "capitulo": linha[1],
            "numero": linha[2],
            "contexto": linha[3]
        }
        for linha in cur.fetchall()
    }
    conn.close()

    with open(arquivo_dados_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)

def atualizar_html():
    print("\nIniciando varredura e estruturação do banco...")
    conn_banco = inicializar_banco()
    cur_banco = conn_banco.cursor()

    with open(arquivo_html, "r", encoding="utf-8") as f:
        conteudo = f.read()

    catalogo = construir_catalogo(cur_banco)
    conn_banco.commit()
    conn_banco.close()

    exportar_indice_n8n()

    json_catalogo = json.dumps(catalogo, ensure_ascii=False, indent=12)
    tag_inicio_cat = "/* === CATALOGO_INICIO === */"
    tag_fim_cat = "/* === CATALOGO_FIM === */"
    padrao_cat = re.compile(f"{re.escape(tag_inicio_cat)}.*?{re.escape(tag_fim_cat)}", re.DOTALL)
    bloco_cat = f"{tag_inicio_cat}\n        const catalogo = {json_catalogo};\n        {tag_fim_cat}"
    conteudo = padrao_cat.sub(bloco_cat, conteudo)

    with open(arquivo_html, "w", encoding="utf-8") as f:
        f.write(conteudo)

    # Painel Gerencial (Dashboard) impresso no Terminal
    print("\n" + "="*50)
    print(" 📊 RELATÓRIO DE ATUALIZAÇÃO DO PORTAL")
    print("="*50)
    print(f"Total de Questões Lidas:     {ESTATISTICAS['total_questoes']}")
    print(f"Questões com Gráfico (TikZ): {ESTATISTICAS['com_tikz']}")
    print(f"  -> Usaram Cache Rápido:    {ESTATISTICAS['cache']}")
    print(f"  -> Geradas Novas:          {ESTATISTICAS['gerados']}")
    print(f"  -> Falhas de Compilação:   {ESTATISTICAS['erros']}")
    print("="*50)
    if ESTATISTICAS['erros'] == 0:
        print("[SUCESSO] Sincronização perfeita!\n")
    else:
        print("[AVISO] Verifique os erros acima.\n")

if __name__ == "__main__":
    atualizar_html()