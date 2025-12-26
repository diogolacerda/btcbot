# Configuracao de GitHub Secrets - BTC Grid Bot

**Data:** 26 de Dezembro de 2025
**Versao:** 1.0

---

## Sumario

1. [Visao Geral](#visao-geral)
2. [Secrets Obrigatorios](#secrets-obrigatorios)
3. [Secrets Opcionais](#secrets-opcionais)
4. [Como Configurar os Secrets](#como-configurar-os-secrets)
5. [Obtendo o Access Token do Docker Hub](#obtendo-o-access-token-do-docker-hub)
6. [Testando a Configuracao](#testando-a-configuracao)
7. [Rotacao de Tokens](#rotacao-de-tokens)
8. [Troubleshooting](#troubleshooting)
9. [Seguranca](#seguranca)

---

## Visao Geral

Os GitHub Secrets sao usados pelos workflows de CI/CD para:

- Autenticar no Docker Hub para push de imagens
- Enviar notificacoes de deploy via Discord (opcional)

Os secrets sao criptografados e nunca aparecem em logs ou outputs dos workflows.

### Workflows que Usam Secrets

| Workflow | Secrets Utilizados |
|----------|-------------------|
| `test-registry-login.yml` | DOCKER_USERNAME, DOCKER_PASSWORD |
| `cd-stage.yml` | DOCKER_USERNAME, DOCKER_PASSWORD, DISCORD_WEBHOOK |
| `cd-prod.yml` | DOCKER_USERNAME, DOCKER_PASSWORD, DISCORD_WEBHOOK |

---

## Secrets Obrigatorios

Estes secrets DEVEM estar configurados para os pipelines de CD funcionarem:

| Secret | Descricao | Exemplo |
|--------|-----------|---------|
| `DOCKER_USERNAME` | Usuario do Docker Hub | `meuusuario` |
| `DOCKER_PASSWORD` | Access Token do Docker Hub | `dckr_pat_xxxxxx...` |

### DOCKER_USERNAME

Seu nome de usuario no Docker Hub. Este e o mesmo usuario que voce usa para fazer login em https://hub.docker.com.

### DOCKER_PASSWORD

**IMPORTANTE:** Use um Access Token, NAO sua senha real do Docker Hub.

Vantagens de usar Access Token:
- Pode ser revogado sem alterar a senha
- Tem permissoes limitadas (apenas push/pull)
- Nao expoe sua senha real
- Facilita auditoria de acesso

---

## Secrets Opcionais

Estes secrets sao opcionais mas recomendados:

| Secret | Descricao | Exemplo |
|--------|-----------|---------|
| `DISCORD_WEBHOOK` | URL do webhook para notificacoes | `https://discord.com/api/webhooks/...` |

### DISCORD_WEBHOOK

Webhook do Discord para receber notificacoes de deploy. Se configurado, os workflows enviarao mensagens:

- Quando CD Stage concluir (sucesso ou falha)
- Quando CD Prod concluir (sucesso ou falha)

Para criar um webhook no Discord:
1. Acesse as configuracoes do seu servidor
2. Va em "Integrations" -> "Webhooks"
3. Clique em "New Webhook"
4. Escolha o canal de destino
5. Copie a URL do webhook

---

## Como Configurar os Secrets

### Passo a Passo

1. Acesse o repositorio no GitHub
2. Va em **Settings** (engrenagem)
3. No menu lateral, clique em **Secrets and variables** -> **Actions**
4. Clique no botao **New repository secret**
5. Preencha:
   - **Name:** Nome do secret (ex: `DOCKER_USERNAME`)
   - **Secret:** Valor do secret
6. Clique em **Add secret**
7. Repita para cada secret necessario

### Verificando Secrets Configurados

Apos configurar, voce vera uma lista como:

```
Repository secrets
  DOCKER_PASSWORD  Updated 2 days ago
  DOCKER_USERNAME  Updated 2 days ago
  DISCORD_WEBHOOK  Updated 2 days ago
```

**Nota:** O valor dos secrets nunca e exibido apos salvo.

---

## Obtendo o Access Token do Docker Hub

### Passo a Passo Detalhado

1. Acesse https://hub.docker.com e faca login
2. Clique no seu avatar no canto superior direito
3. Selecione **Account Settings**
4. No menu lateral, clique em **Security**
5. Na secao "Access Tokens", clique em **New Access Token**
6. Preencha:
   - **Access Token Description:** `btcbot-github-actions`
   - **Access permissions:** Read & Write (para push de imagens)
7. Clique em **Generate**
8. **IMPORTANTE:** Copie o token imediatamente! Ele so e exibido uma vez.
9. Use este token como valor do secret `DOCKER_PASSWORD`

### Permissoes do Token

| Permissao | Descricao | Necessario? |
|-----------|-----------|-------------|
| Read | Pull de imagens | Sim |
| Write | Push de imagens | Sim |
| Delete | Remover imagens | Nao |

Recomendamos usar apenas **Read & Write** para seguir o principio de menor privilegio.

### Exemplo de Token

O token tem o formato:
```
dckr_pat_ABCdefGHI123456789_abcdefghijklmnopqrstuvwxyz
```

---

## Testando a Configuracao

Apos configurar os secrets, execute o workflow de teste:

### Via GitHub Actions UI

1. Va em **Actions** no repositorio
2. Selecione **Test Docker Hub Login** na lista de workflows
3. Clique em **Run workflow**
4. Selecione a branch `main`
5. Deixe `dry_run` como `true` (recomendado)
6. Clique em **Run workflow**

### Interpretando o Resultado

**Sucesso:**
- Job verde com checkmark
- Summary mostra todos os itens como "Configurado"
- Mensagem: "Login no Docker Hub realizado com sucesso!"

**Falha - Secret nao configurado:**
- Job vermelho com X
- Erro: `DOCKER_USERNAME secret nao esta configurado!`
- Solucao: Configure o secret conforme instrucoes

**Falha - Credenciais invalidas:**
- Job vermelho com X
- Erro: `Error: Username and password required`
- Solucao: Verifique se o token foi copiado corretamente

---

## Rotacao de Tokens

### Por que Rotacionar?

- Tokens podem vazar em logs (mesmo criptografados)
- Funcionarios que saem podem ter acesso
- Boas praticas de seguranca recomendam rotacao periodica

### Frequencia Recomendada

| Tipo de Token | Frequencia |
|---------------|------------|
| Docker Hub Access Token | A cada 90 dias |
| Discord Webhook | A cada 6 meses |

### Procedimento de Rotacao

#### 1. Docker Hub Token

```
Data da ultima rotacao: [REGISTRE AQUI]
Proxima rotacao: [DATA + 90 DIAS]
```

**Passos:**

1. Acesse https://hub.docker.com/settings/security
2. Localize o token atual (`btcbot-github-actions`)
3. Clique nos tres pontos (...) e selecione **Edit**
4. Anote a data de criacao para registro
5. Clique em **Regenerate**
6. **IMPORTANTE:** Copie o novo token imediatamente
7. Va no GitHub -> Settings -> Secrets -> Actions
8. Clique em `DOCKER_PASSWORD`
9. Clique em **Update secret**
10. Cole o novo token
11. Clique em **Update secret**
12. Execute o workflow de teste para validar
13. Registre a data da rotacao neste documento

#### 2. Discord Webhook

**Passos:**

1. Acesse as configuracoes do servidor Discord
2. Va em Integrations -> Webhooks
3. Encontre o webhook do btcbot
4. Clique em **Regenerate**
5. Copie a nova URL
6. Atualize o secret `DISCORD_WEBHOOK` no GitHub
7. (Opcional) Envie uma mensagem de teste

### Checklist de Rotacao

- [ ] Novo token gerado
- [ ] Secret atualizado no GitHub
- [ ] Workflow de teste executado com sucesso
- [ ] Data registrada neste documento
- [ ] Token antigo deletado (se aplicavel)

---

## Troubleshooting

### Erro: "Username and password required"

**Causa:** Secrets nao configurados ou com valores vazios.

**Solucao:**
1. Verifique se os secrets existem em Settings -> Secrets
2. Reconfigure os secrets se necessario

### Erro: "incorrect username or password"

**Causa:** Token invalido ou expirado.

**Solucao:**
1. Gere um novo token no Docker Hub
2. Atualize o secret `DOCKER_PASSWORD`
3. Execute o workflow de teste

### Erro: "unauthorized: access token has insufficient scopes"

**Causa:** Token sem permissao de push.

**Solucao:**
1. Gere um novo token com permissao "Read & Write"
2. Atualize o secret

### Erro: "denied: requested access to the resource is denied"

**Causa:** Usuario nao tem acesso ao repositorio de imagens.

**Solucao:**
1. Verifique se o repositorio existe no Docker Hub
2. Verifique permissoes do usuario
3. Crie o repositorio se necessario

### Workflow nao aparece na lista

**Causa:** Arquivo YAML com erro de sintaxe.

**Solucao:**
1. Valide o YAML em https://yamlvalidator.com
2. Verifique indentacao (deve usar espacos, nao tabs)
3. Faca push novamente

---

## Seguranca

### Boas Praticas

1. **Nunca compartilhe tokens:** Cada ambiente/servico deve ter seu proprio token
2. **Use Access Tokens:** Nunca use sua senha real do Docker Hub
3. **Principio do menor privilegio:** Conceda apenas as permissoes necessarias
4. **Rotacao regular:** Siga o calendario de rotacao
5. **Auditoria:** Revise periodicamente os tokens ativos no Docker Hub
6. **Revogacao imediata:** Se suspeitar de vazamento, revogue o token imediatamente

### Em Caso de Vazamento

Se um token for exposto:

1. **IMEDIATAMENTE** revogue o token no Docker Hub
2. Gere um novo token
3. Atualize o secret no GitHub
4. Verifique logs de acesso no Docker Hub
5. Investigue como o vazamento ocorreu
6. Documente o incidente

### Monitoramento

O Docker Hub permite visualizar:
- Ultimo uso do token
- Quantidade de pulls/pushes
- IP de origem

Revise periodicamente para detectar uso anomalo.

---

## Referencia Rapida

### URLs Importantes

| Recurso | URL |
|---------|-----|
| Docker Hub Security | https://hub.docker.com/settings/security |
| GitHub Secrets | https://github.com/[OWNER]/[REPO]/settings/secrets/actions |
| Workflow de Teste | https://github.com/[OWNER]/[REPO]/actions/workflows/test-registry-login.yml |

### Secrets Necessarios

```
# Obrigatorios
DOCKER_USERNAME = <seu_usuario_dockerhub>
DOCKER_PASSWORD = <access_token_dockerhub>

# Opcionais
DISCORD_WEBHOOK = <url_webhook_discord>
```

### Comandos Uteis

```bash
# Testar login localmente
docker login docker.io -u $DOCKER_USERNAME -p $DOCKER_PASSWORD

# Verificar se token funciona
docker pull hello-world
docker tag hello-world docker.io/$DOCKER_USERNAME/test:temp
docker push docker.io/$DOCKER_USERNAME/test:temp
docker rmi docker.io/$DOCKER_USERNAME/test:temp
```

---

*Documento criado em 26/12/2025 - DEVOPS-006*
