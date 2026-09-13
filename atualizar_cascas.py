import os

def sincronizar_cascas():
    raiz = os.getcwd()
    contador = 0
    
    print("[AUTOMATIZADOR] Iniciando varredura de arquivos BASE...")
    
    for diretorio, pastas, arquivos in os.walk(raiz):
        for arquivo in arquivos:
            if arquivo.endswith("_BASE.tex"):
                base_name = arquivo                # Ex: ALG_8EF_AUT_U08-PROD_NOTAVEIS_BASE.tex
                prefixo = base_name[:-9]           # Remove "_BASE.tex" -> ALG_8EF_AUT_U08-PROD_NOTAVEIS
                
                aluno_name = prefixo + "_ALUNO.tex"
                prof_name = prefixo + "_PROF.tex"
                
                caminho_aluno = os.path.join(diretorio, aluno_name)
                caminho_prof = os.path.join(diretorio, prof_name)
                
                # Conteúdo padrão limpo para a casca do Aluno
                conteudo_aluno = f"""\\documentclass[twoside, 10pt, a4paper]{{article}}

% --- DECLARAÇÃO SEGURA DA VARIÁVEL DE GABARITO ---
\\newif\\ifgabarito
\\gabaritofalse

\\input{{{base_name}}}
"""

                # Conteúdo padrão limpo para a casca do Professor
                conteudo_prof = f"""\\documentclass[twoside, 10pt, a4paper]{{article}}

% --- DECLARAÇÃO SEGURA DA VARIÁVEL DE GABARITO ---
\\newif\\ifgabarito
\\gabaritotrue

\\input{{{base_name}}}
"""

                # Escreve ou limpa/atualiza a casca do Aluno
                with open(caminho_aluno, 'w', encoding='utf-8') as f:
                    f.write(conteudo_aluno)
                
                # Escreve ou limpa/atualiza a casca do Professor
                with open(caminho_prof, 'w', encoding='utf-8') as f:
                    f.write(conteudo_prof)
                
                print(f"[SINCRONIZADO] Cascas limpas e atualizadas em: {os.path.relpath(diretorio, raiz)}")
                contador += 1

    print(f"\n[SUCESSO] Processo concluído! {contador} pares de cascas (Aluno/Professor) foram limpos e sincronizados.")

if __name__ == "__main__":
    sincronizar_cascas()