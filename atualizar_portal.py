import os
import json
import re
import sqlite3

raiz = os.path.dirname(os.path.abspath(__file__))
arquivo_html = os.path.join(raiz, "index.html")
arquivo_alunos = os.path.join(raiz, "alunos.json")
arquivo_banco = os.path.join(raiz, "questoes.db")
arquivo_dados_json = os.path.join(raiz, "questoes_dados.json")

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
            resolucao TEXT,
            nota_pedagogica TEXT,
            contexto_pronto TEXT
        );
    """)
    cur.execute("""
        CREATE INDEX idx_busca_questao 
        ON questoes (disciplina, ano, unidade, tipo_caderno, capitulo_indice, numero_questao);
    """)
    conn.commit()
    return conn

def formatar_id_unidade(pasta_unidade):
    m = re.match(r"([A-Za-z]+)(\d+)", pasta_unidade)
    if m:
        return f"{m.group(1).upper()} {m.group(2)}"
    return pasta_unidade

def encontrar_pdf(pasta_unidade_completa, tipo, destino):
    pasta_alvo = os.path.join(pasta_unidade_completa, destino)
    if not os.path.exists(pasta_alvo):
        return None
    
    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_alvo):
        if arq.endswith(".pdf") and tag in arq:
            caminho_rel = os.path.relpath(os.path.join(pasta_alvo, arq), raiz)
            return caminho_rel.replace(os.sep, "/")
    return None

def encontrar_tex(pasta_unidade_completa, tipo):
    pasta_fonte = os.path.join(pasta_unidade_completa, "fonte_tex")
    if not os.path.exists(pasta_fonte):
        return None, None

    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_fonte):
        if arq.endswith("_BASE.tex") and tag in arq:
            caminho_abs = os.path.join(pasta_fonte, arq)
            caminho_rel = os.path.relpath(caminho_abs, raiz)
            return caminho_rel.replace(os.sep, "/"), caminho_abs
    return None, None

def indexar_questoes_no_banco(caminho_abs_tex, prefixo_material, disciplina, ano, unidade, tipo_caderno, cur):
    if not caminho_abs_tex or not os.path.exists(caminho_abs_tex):
        return

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

        contexto = f"--- ENUNCIADO OFICIAL DA QUESTÃO {num_q} (Capítulo {idx_cap}: {capitulo_nome}) ---\n{enunciado}\n"
        if tikz:
            contexto += f"\n--- FIGURA / DIAGRAMA (TIKZ) ---\n{tikz}\n"
        if resolucao:
            contexto += f"\n--- RESOLUÇÃO E GABARITO OFICIAL ---\n{resolucao}\n"
        if nota_pedagogica:
            contexto += f"\n--- ORIENTAÇÃO PEDAGÓGICA AO TUTOR ---\n{nota_pedagogica}\n"

        # ID canônico derivado diretamente do prefixo oficial do caderno
        id_unico = f"{prefixo_material}__C{idx_cap:02d}__Q{num_q:02d}"

        cur.execute("""
            INSERT OR REPLACE INTO questoes 
            (id, disciplina, ano, unidade, tipo_caderno, capitulo_indice, capitulo, numero_questao, enunciado, codigo_tikz, resolucao, nota_pedagogica, contexto_pronto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_unico, disciplina, ano, unidade, tipo_caderno, idx_cap, capitulo_nome, num_q, enunciado, tikz, resolucao, nota_pedagogica, contexto))

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
    except Exception as e:
        print(f"[AVISO] Não foi possível ler o TeX para estrutura: {e}")
        return []

    partes = re.split(r'\\subsection\*\{([^}]+)\}', conteudo)
    capitulos = []
    
    questoes_avulsas = re.findall(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', partes[0])
    if questoes_avulsas:
        nums = [int(q) for q in questoes_avulsas]
        capitulos.append({
            "indice": 1,
            "titulo": "Lista Principal",
            "inicio": min(nums),
            "fim": max(nums),
            "questoes": nums
        })

    idx = len(capitulos) + 1
    for i in range(1, len(partes), 2):
        titulo_bruto = partes[i].strip()
        titulo_limpo = re.sub(r'\\[a-zA-Z]+', '', titulo_bruto).replace('{', '').replace('}', '').strip()
        corpo = partes[i+1]
        
        questoes_encontradas = re.findall(r'\\subsubsection\*\{\s*0*(\d+)\.?\s*\}', corpo)
        if questoes_encontradas:
            nums = [int(q) for q in questoes_encontradas]
            capitulos.append({
                "indice": idx,
                "titulo": titulo_limpo or f"Capítulo {idx}",
                "inicio": min(nums),
                "fim": max(nums),
                "questoes": nums
            })
            idx += 1

    return capitulos

def carregar_alunos():
    if not os.path.exists(arquivo_alunos):
        print(f"[AVISO] Arquivo alunos.json não encontrado em {arquivo_alunos}")
        return {}
    with open(arquivo_alunos, "r", encoding="utf-8") as f:
        return json.load(f)

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

            disciplina_pasta = partes[0]
            ano_pasta = partes[1]
            unidade_pasta = partes[-1]

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
                anos_dict[ano_pasta] = {
                    "nome": nome_ano,
                    "unidades": {}
                }

            materiais = []
            titulo_unidade = ""
            desc_unidade = ""

            jsons_ordenados = sorted(jsons, key=lambda x: 0 if "AUT" in x else 1)

            for j_nome in jsons_ordenados:
                caminho_j = os.path.join(raiz_atual, j_nome)
                with open(caminho_j, "r", encoding="utf-8") as f:
                    d = json.load(f)

                if not titulo_unidade:
                    titulo_unidade = d.get("titulo", "")
                if not desc_unidade:
                    desc_unidade = d.get("desc", "")

                tipo_mat = d.get("tipo", "Autoral")
                pdf_aluno = encontrar_pdf(raiz_atual, tipo_mat, "publica")
                pdf_prof = encontrar_pdf(raiz_atual, tipo_mat, "restrita")
                caminho_tex, caminho_abs_tex = encontrar_tex(raiz_atual, tipo_mat)
                
                estrutura_capitulos = extrair_estrutura_tex(caminho_abs_tex)

                # Prefixo oficial da fonte de verdade (sem abreviações artificiais)
                prefixo_material = f"{disciplina_pasta}__{ano_pasta}__{unidade_pasta}__{tipo_mat}"

                if caminho_abs_tex:
                    indexar_questoes_no_banco(caminho_abs_tex, prefixo_material, disciplina_pasta, ano_pasta, id_unidade_formatada, tipo_mat, cur_banco)

                materiais.append({
                    "tipo": tipo_mat,
                    "rotulo": d.get("rotulo", "Caderno de Atividades Suplementar" if tipo_mat == "Autoral" else "Caderno de Atividades"),
                    "id_prefixo": prefixo_material,  # Carimbo oficial injetado no HTML
                    "pdf": pdf_aluno,
                    "pdfProf": pdf_prof,
                    "tex": caminho_tex,
                    "videos": d.get("videos", []),
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
    print(f"[SUCESSO] questoes_dados.json gerado ({len(dados)} questões prontas).")

def atualizar_html():
    if not os.path.exists(arquivo_html):
        print(f"[ERRO] Arquivo index.html não encontrado em {raiz}")
        return

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

    if tag_inicio_cat not in conteudo or tag_fim_cat not in conteudo:
        print("[ERRO] Marcadores de catálogo não encontrados no index.html.")
        return

    padrao_cat = re.compile(f"{re.escape(tag_inicio_cat)}.*?{re.escape(tag_fim_cat)}", re.DOTALL)
    bloco_cat = f"{tag_inicio_cat}\n        const catalogo = {json_catalogo};\n        {tag_fim_cat}"
    conteudo = padrao_cat.sub(bloco_cat, conteudo)

    tag_inicio_alu = "/* === ALUNOS_INICIO === */"
    tag_fim_alu = "/* === ALUNOS_FIM === */"

    if tag_inicio_alu in conteudo and tag_fim_alu in conteudo:
        alunos = carregar_alunos()
        json_alunos = json.dumps(alunos, ensure_ascii=False, indent=12)
        padrao_alu = re.compile(f"{re.escape(tag_inicio_alu)}.*?{re.escape(tag_fim_alu)}", re.DOTALL)
        bloco_alu = f"{tag_inicio_alu}\n        const listaAlunos = {json_alunos};\n        {tag_fim_alu}"
        conteudo = padrao_alu.sub(bloco_alu, conteudo)

    with open(arquivo_html, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print("[SUCESSO] index.html, questoes.db e questoes_dados.json atualizados em sincronia!")

if __name__ == "__main__":
    atualizar_html()