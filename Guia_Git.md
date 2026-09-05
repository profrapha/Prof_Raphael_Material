**GUIA PRÁTICO: GIT E TERMINAL NO VS CODE**

**1. Configuração Essencial (Faz apenas uma vez)**
Para evitar que o Git abra telas antigas no terminal e use sempre as abas normais do VS Code:
git config --global core.editor "code --wait"

**2. Destravando o Terminal (Comandos de Fuga)**
* Lista infinita (`git log`): Pressione a tecla `q` para fechar a visualização e liberar o cursor.
* Terminal travado/congelado: Pressione `Ctrl + C` repetidamente até o caminho da pasta voltar a aparecer.
* Cancelar um rebase no meio do caminho (desistir da edição): Digite `git rebase --abort`.

**3. Corrigindo o ÚLTIMO Commit**
Se o erro for exatamente no commit que você acabou de fazer:
git commit --amend -m "Escreva a nova mensagem completa aqui"
(Para confirmar, digite `git log -1`).

**4. Corrigindo Commits ANTIGOS (Rebase)**
Para alterar a mensagem de um ou mais commits que ficaram no passado:
* Passo 1: Conte a distância do commit e digite `git rebase -i HEAD~4` (troque o 4 pela quantidade de commits).
* Passo 2: O VS Code abrirá um arquivo. Troque a palavra `pick` por `reword` na linha dos commits que deseja consertar.
* Passo 3: Salve (`Ctrl + S`) e feche a aba (`Ctrl + W`).
* Passo 4: O Git abrirá uma nova aba para cada commit marcado. Escreva a mensagem nova, salve e feche. O Git passará para o próximo automaticamente.

**5. O Padrão de Escrita da Mensagem**
Para evitar a "linha vermelha" no VS Code, quebre a mensagem do commit assim:
[Linha 1] Título curto do que foi feito (Ex: Ajustes na formatação).
[Linha 2] (Deixe essa linha totalmente vazia).
[Linha 3] Explicação longa do que foi feito (Ex: Adição de 2 novos exercícios no arquivo...).

**6. Atualizando o GitHub / Servidor**
Se você alterou commits antigos usando `--amend` ou `rebase`, o histórico local ficou diferente do servidor. O comando comum dará erro. Use o envio forçado:
git push --force

**7. Quebra de Linha Manual no LaTeX**
* No texto normal: Use `\\` para descer para a linha de baixo sem criar um novo parágrafo.
* Nas alternativas de listas: Use `\\[\espacoAlt]` para respeitar o espaçamento dinâmico do painel de controle.
* Evite usar "Enters" duplos no código-fonte para afastar blocos; prefira sempre `\par\vspace{...}`.

**8. Quebrando texto em duas linhas dentro de um nó TikZ**
* No parâmetro do node, adicione `align=center` (ou `align=left`).
* Use `\\` onde deseja que o texto desça para a linha de baixo.
* Exemplo prático:
  \node[align=center] at (0,0) {Texto da primeira linha \\ Segunda linha abaixo};