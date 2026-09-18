import sqlite3
import json
import os

print("\n" + "="*50)
print(" 🔍 AUDITORIA DE ESTRUTURA DOS DADOS")
print("="*50)

# 1. LER AS COLUNAS DO BANCO SQLITE
arquivo_banco = "questoes.db"
if os.path.exists(arquivo_banco):
    conn = sqlite3.connect(arquivo_banco)
    colunas = [col[1] for col in conn.execute("PRAGMA table_info(questoes)").fetchall()]
    print("\n📦 Colunas na tabela 'questoes' (questoes.db):")
    for c in colunas:
        print(f"  - {c}")
    conn.close()
else:
    print("\n📦 questoes.db não encontrado.")

# 2. LER AS CHAVES DO QUESTOES_DADOS.JSON
arquivo_json = "questoes_dados.json"
if os.path.exists(arquivo_json):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
        if dados:
            primeira_chave = list(dados.keys())[0]
            print(f"\n📄 Estrutura dos itens no 'questoes_dados.json' (ex: {primeira_chave}):")
            for chave in dados[primeira_chave].keys():
                print(f"  - {chave}")
else:
    print("\n📄 questoes_dados.json não encontrado.")

# 3. PROCURAR UM info_AUT.json E LER AS CHAVES
print("\n📂 Estrutura raiz de um 'info_AUT.json' encontrado nas pastas:")
achou_info = False
for raiz, _, arquivos in os.walk("."):
    if "info_AUT.json" in arquivos:
        caminho = os.path.join(raiz, "info_AUT.json")
        with open(caminho, "r", encoding="utf-8") as f:
            info = json.load(f)
            print(f"Arquivo lido: {caminho}")
            for chave in info.keys():
                print(f"  - {chave}")
        achou_info = True
        break

if not achou_info:
    print("  Nenhum info_AUT.json encontrado nas subpastas.")

print("\n" + "="*50)