import os
import json

# Pega a pasta onde este script está rodando
raiz = os.path.dirname(os.path.abspath(__file__))
pastas_disciplinas = ["Fisica", "Matematica_Algebra", "Matematica_Geometria"]

total_atualizados = 0

print("Iniciando a migração dos arquivos JSON para o novo formato de Trilhas...")
print("-" * 60)

for disc in pastas_disciplinas:
    caminho_disc = os.path.join(raiz, disc)
    if not os.path.exists(caminho_disc):
        continue

    # Vasculha todas as subpastas
    for raiz_atual, _, arquivos in os.walk(caminho_disc):
        for arq in arquivos:
            if arq in ["info_AUT.json", "info_ESC.json"]:
                caminho_json = os.path.join(raiz_atual, arq)
                
                try:
                    with open(caminho_json, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                    
                    alterado = False
                    
                    # Garante que a chave nova exista
                    if "trilhas_de_aprendizagem" not in dados:
                        dados["trilhas_de_aprendizagem"] = []
                        alterado = True
                    
                    # Se tiver a chave velha 'videos', vamos converter para Trilhas
                    if "videos" in dados:
                        for vid in dados["videos"]:
                            # Pega a dúvida antiga para transformar na chamada
                            duvida_antiga = vid.get("duvida", "nesta matéria?")
                            titulo_video = vid.get("titulo", "Revisão")
                            
                            nova_trilha = {
                                "subtema": titulo_video, # Usa o título antigo do vídeo como o Subtema
                                "videos": [
                                    {
                                        "chamada": f"Você está {duvida_antiga}",
                                        "titulo": titulo_video,
                                        "autor": vid.get("autor", "Professor"),
                                        "url": vid.get("url", "")
                                    }
                                ]
                            }
                            dados["trilhas_de_aprendizagem"].append(nova_trilha)
                        
                        # Remove a chave antiga "videos" para limpar o JSON
                        del dados["videos"]
                        alterado = True
                    
                    # Se o arquivo era antigo e precisou ser mexido, salva a nova versão
                    if alterado:
                        with open(caminho_json, "w", encoding="utf-8") as f:
                            json.dump(dados, f, ensure_ascii=False, indent=2)
                        
                        # Pegando um caminho mais curto para imprimir bonitinho na tela
                        caminho_curto = os.path.relpath(caminho_json, raiz)
                        print(f"✅ Atualizado: {caminho_curto}")
                        total_atualizados += 1
                        
                except Exception as e:
                    print(f"❌ Erro ao ler {arq} em {raiz_atual}: {e}")

print("-" * 60)
print(f"Migração concluída! Um total de {total_atualizados} arquivos foram convertidos para o novo padrão de Trilhas.")