import os
import json
import re

raiz = os.path.dirname(os.path.abspath(__file__))
arquivo_html = os.path.join(raiz, "index.html")
arquivo_alunos = os.path.join(raiz, "alunos.json")

MAPA_ANOS = {
    "6_Ano": "6º Ano",
    "7_Ano": "7º Ano",
    "8_Ano": "8º Ano",
    "9_Ano": "9º Ano",
    "1_Serie": "1ª Série (EM)",
    "2_Serie": "2ª Série (EM)",
    "3_Serie": "3ª Série (Intensivo)"
}

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
        return None

    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_fonte):
        if arq.endswith("_BASE.tex") and tag in arq:
            caminho_rel = os.path.relpath(os.path.join(pasta_fonte, arq), raiz)
            return caminho_rel.replace(os.sep, "/")
    return None

def carregar_alunos():
    if not os.path.exists(arquivo_alunos):
        print(f"[AVISO] Arquivo alunos.json não encontrado em {arquivo_alunos}")
        return {}
    with open(arquivo_alunos, "r", encoding="utf-8") as f:
        return json.load(f)

def construir_catalogo():
    catalogo = {
        "Fisica": {
            "nome": "Física",
            "tipo": "direto",
            "anos": {}
        },
        "Matematica": {
            "nome": "Matemática",
            "tipo": "frentes",
            "frentes": {
                "Algebra": {
                    "nome": "Álgebra",
                    "anos": {}
                },
                "Geometria": {
                    "nome": "Geometria",
                    "anos": {}
                }
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
                caminho_tex = encontrar_tex(raiz_atual, tipo_mat)

                materiais.append({
                    "tipo": tipo_mat,
                    "rotulo": d.get("rotulo", "Caderno de Atividades Suplementar" if tipo_mat == "Autoral" else "Caderno de Atividades"),
                    "pdf": pdf_aluno,
                    "pdfProf": pdf_prof,
                    "tex": caminho_tex,
                    "videos": d.get("videos", [])
                })

            anos_dict[ano_pasta]["unidades"][id_unidade_formatada] = {
                "titulo": titulo_unidade,
                "desc": desc_unidade,
                "materiais": materiais
            }

    return catalogo

def atualizar_html():
    if not os.path.exists(arquivo_html):
        print(f"[ERRO] Arquivo index.html não encontrado em {raiz}")
        return

    with open(arquivo_html, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # 1. Injeção do Catálogo de Materiais
    catalogo = construir_catalogo()
    json_catalogo = json.dumps(catalogo, ensure_ascii=False, indent=12)

    tag_inicio_cat = "/* === CATALOGO_INICIO === */"
    tag_fim_cat = "/* === CATALOGO_FIM === */"

    if tag_inicio_cat not in conteudo or tag_fim_cat not in conteudo:
        print("[ERRO] Marcadores de catálogo não encontrados no index.html.")
        return

    padrao_cat = re.compile(f"{re.escape(tag_inicio_cat)}.*?{re.escape(tag_fim_cat)}", re.DOTALL)
    bloco_cat = f"{tag_inicio_cat}\n        const catalogo = {json_catalogo};\n        {tag_fim_cat}"
    conteudo = padrao_cat.sub(bloco_cat, conteudo)

    # 2. Injeção da Lista de Alunos (se marcadores existirem)
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

    print("[SUCESSO] index.html atualizado dinamicamente com catálogo (PDFs + TeX) e alunos!")

if __name__ == "__main__":
    atualizar_html()