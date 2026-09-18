import os

raiz_projeto = os.path.dirname(os.path.abspath(__file__))

extensoes_para_remover = [
    ".aux", ".fdb_latexmk", ".fls", ".log", 
    ".synctex.gz", ".pdf", ".out", ".toc"
]

removidos = 0

for pasta_atual, _, arquivos in os.walk(raiz_projeto):
    if os.path.basename(pasta_atual) == "fonte_tex":
        for arq in arquivos:
            _, ext = os.path.splitext(arq)
            if ext.lower() in extensoes_para_remover:
                caminho = os.path.join(pasta_atual, arq)
                os.remove(caminho)
                print(f"[REMOVIDO de fonte_tex] {arq}")
                removidos += 1

print(f"\nLimpeza concluída! Total de {removidos} arquivos removidos das pastas fonte_tex.")