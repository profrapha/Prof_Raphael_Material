import os
import json
import re

raiz = os.path.dirname(os.path.abspath(__file__))
arquivo_html = os.path.join(raiz, "index.html")

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
    # Converte 'UNIDADE6' -> 'UNIDADE 6' e 'SEMANA10' -> 'SEMANA 10'
    m = re.match(r"([A-Za-z]+)(\d+)", pasta_unidade)
    if m:
        return f"{m.group(1).upper()} {m.group(2)}"
    return pasta_unidade

def encontrar_pdf(pasta_unidade_completa, tipo, destino):
    # destino: 'publica' ou 'restrita'
    pasta_alvo = os.path.join(pasta_unidade_completa, destino)
    if not os.path.exists(pasta_alvo):
        return None
    
    tag = "_AUT_" if tipo == "Autoral" else "_ESC_"
    for arq in os.listdir(pasta_alvo):
        if arq.endswith(".pdf") and tag in arq:
            caminho_rel = os.path.relpath(os.path.join(pasta_alvo, arq), raiz)
            return caminho_rel.replace(os.sep, "/")
    return None

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

    # Varre as pastas das três disciplinas
    pastas_disciplinas = ["Fisica", "Matematica_Algebra", "Matematica_Geometria"]

    for disc in pastas_disciplinas:
        caminho_disc = os.path.join(raiz, disc)
        if not os.path.exists(caminho_disc):
            continue

        for raiz_atual, _, arquivos in os.walk(caminho_disc):
            # Procura pastas que tenham info_AUT.json ou info_ESC.json
            jsons = [f for f in arquivos if f in ["info_AUT.json", "info_ESC.json"]]
            if not jsons:
                continue

            rel = os.path.relpath(raiz_atual, raiz)
            partes = rel.split(os.sep)

            # Estruturas suportadas:
            # Disciplina / Ano / Unidade
            # Disciplina / Ano / Subpasta / Unidade (ex: Matematica_Algebra/3_Serie/Intensivo/SEMANA10)
            disciplina_pasta = partes[0]
            ano_pasta = partes[1]
            unidade_pasta = partes[-1]

            id_unidade_formatada = formatar_id_unidade(unidade_pasta)
            nome_ano = MAPA_ANOS.get(ano_pasta, ano_pasta)

            # Posiciona no nó de dados correto do catálogo
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

            # Lê os JSONs disponíveis na unidade
            materiais = []
            titulo_unidade = ""
            desc_unidade = ""

            # Garante ordem: Autoral primeiro, Escola depois
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

                materiais.append({
                    "tipo": tipo_mat,
                    "rotulo": d.get("rotulo", "Caderno de Atividades Suplementar" if tipo_mat == "Autoral" else "Caderno de Atividades"),
                    "pdf": pdf_aluno,
                    "pdfProf": pdf_prof,
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

    catalogo = construir_catalogo()
    json_catalogo = json.dumps(catalogo, ensure_ascii=False, indent=12)

    with open(arquivo_html, "r", encoding="utf-8") as f:
        conteudo = f.read()

    tag_inicio = "/* === CATALOGO_INICIO === */"
    tag_fim = "/* === CATALOGO_FIM === */"

    if tag_inicio not in conteudo or tag_fim not in conteudo:
        print("[ERRO] Marcadores /* === CATALOGO_INICIO === */ e /* === CATALOGO_FIM === */ não encontrados no index.html.")
        return

    padrao = re.compile(f"{re.escape(tag_inicio)}.*?{re.escape(tag_fim)}", re.DOTALL)
    novo_bloco = f"{tag_inicio}\n        const catalogo = {json_catalogo};\n        {tag_fim}"

    conteudo_atualizado = padrao.sub(novo_bloco, conteudo)

    with open(arquivo_html, "w", encoding="utf-8") as f:
        f.write(conteudo_atualizado)

    print("[SUCESSO] index.html atualizado dinamicamente a partir dos JSONs!")

if __name__ == "__main__":
    atualizar_html()