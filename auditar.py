import os
import re
import sqlite3

# 1. Abre o banco gerado
conn = sqlite3.connect("questoes.db")
cur = conn.cursor()

print("=== DISTRIBUIÇÃO POR CADERNO NO BANCO ===")
query = """
SELECT disciplina, ano, unidade, tipo_caderno, COUNT(*) 
FROM questoes 
GROUP BY disciplina, ano, unidade, tipo_caderno
"""
for d, a, u, t, total in cur.execute(query).fetchall():
    print(f"{d} | {a} | {u} | {t}: {total} questoes")

total_db = cur.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]

# 2. Conta direto nos arquivos .tex brutos
total_tex = 0
for r, _, fs in os.walk("."):
    for f in fs:
        if f.endswith("_BASE.tex"):
            with open(os.path.join(r, f), "r", encoding="utf-8", errors="ignore") as arq:
                total_tex += len(re.findall(r"\\subsubsection\*\{\s*0*\d+\.?\s*\}", arq.read()))

print("\n=== AUDITORIA FINAL ===")
print(f"Total encontrado nos arquivos .tex fisicos: {total_tex}")
print(f"Total gravado no questoes.db:              {total_db}")