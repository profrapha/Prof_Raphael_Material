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

**9. Apontamento de DNS (Registro.br)**
Apenas 3 entradas do tipo `A` apontando diretamente para o IPv4 da VPS (`167.99.238.175`):
* Domínio raiz (`profraphaelpaulino.com.br`): Tipo `A` -> `167.99.238.175`
* Subdomínio `www` (`www.profraphaelpaulino.com.br`): Tipo `A` -> `167.99.238.175`
* Subdomínio de testes (`dev.profraphaelpaulino.com.br`): Tipo `A` -> `167.99.238.175`
*(Regra: Exclua quaisquer apontamentos antigos do tipo `A` que apontavam para o GitHub Pages como `185.199...`)*.

**10. Subindo os Containers Web na VPS (Docker)**
Com os repositórios clonados em `/root/portal/dev` e `/root/portal/prod`, execute no terminal da VPS:
* Subir ambiente de Desenvolvimento (Porta 8080):
docker run -d --name site-dev --restart always -p 8080:80 -v /root/portal/dev:/usr/share/nginx/html:ro nginx:alpine
* Subir ambiente de Produção (Porta 8081):
docker run -d --name site-prod --restart always -p 8081:80 -v /root/portal/prod:/usr/share/nginx/html:ro nginx:alpine
* Verificar se ambos estão ativos:
docker ps

**11. Configurando Rotas e SSL no Nginx Proxy Manager**
Acesse o painel web em `http://167.99.238.175:81` e vá em **Hosts > Proxy Hosts > Add Proxy Host**:
* **Host 1: Desenvolvimento**
  * Aba *Details*:
    * Domain Names: `dev.profraphaelpaulino.com.br`
    * Scheme: `http` | Forward Hostname / IP: `172.17.0.1` | Forward Port: `8080`
    * Ative: `Block Common Exploits` e `Websockets Support`
  * Aba *SSL*:
    * Selecione `Request a new SSL Certificate`
    * Ative `Force SSL` e `HTTP/2 Support`
    * Marque `I Agree to the Let's Encrypt Terms of Service` e clique em **Save**.
* **Host 2: Produção**
  * Aba *Details*:
    * Domain Names: `profraphaelpaulino.com.br` e `www.profraphaelpaulino.com.br` (aperte Enter em cada um)
    * Scheme: `http` | Forward Hostname / IP: `172.17.0.1` | Forward Port: `8081`
    * Ative: `Block Common Exploits` e `Websockets Support`
  * Aba *SSL*:
    * Mesma configuração do host anterior (novo certificado Let's Encrypt com `Force SSL`).

**12. Destravando o Deploy na VPS (Divergent Branches)**
Se o GitHub Actions acusar erro de `divergent branches` ou travar no `git pull`:
* Entre na pasta do ambiente com problema no terminal da VPS:
cd /root/portal/dev
* Force a pasta a ficar 100% idêntica ao que está no GitHub:
git fetch origin dev && git reset --hard origin/dev
*(Para a pasta de produção, use `cd /root/portal/prod` e troque `dev` por `main` no comando).*

**13. Rotina Diária de Trabalho no VS Code**
Fluxo contínuo entre desenvolvimento, testes e publicação oficial:
* **Passo 1 (Criar e testar novidades na branch de desenvolvimento):**
git checkout dev
(faça as alterações nos arquivos)
git add .
git commit -m "feat: descrição da alteração"
git push origin dev
*(O GitHub Actions atualizará automaticamente o site `dev.profraphaelpaulino.com.br`)*.
* **Passo 2 (Publicar alterações aprovadas na Produção):**
git checkout main
git pull origin main
git merge dev
git push origin main
git checkout dev
*(O GitHub Actions atualizará automaticamente o site oficial `profraphaelpaulino.com.br`)*.

**14. Prevenção Definitiva no GitHub Actions (`deploy.yml`)**
Para evitar que o deploy automático quebre caso ocorra alteração de histórico no Git, altere os blocos de comando do arquivo `.github/workflows/deploy.yml`:
* No script da branch `dev`, use:
cd /root/portal/dev && git fetch origin dev && git reset --hard origin/dev
* No script da branch `main`, use:
cd /root/portal/prod && git fetch origin main && git reset --hard origin/main