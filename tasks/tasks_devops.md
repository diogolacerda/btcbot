# Tarefas de DevOps - BTC Grid Bot

**Data:** 26 de Dezembro de 2025
**Versao:** 1.6
**Infraestrutura:** Homeserver + Portainer + Watchtower + Docker Hub

---

## Configuracao do Homeserver

| Componente | Valor |
|------------|-------|
| **IP Local** | `192.168.68.99` |
| **Acesso SSH** | `ssh usuario@192.168.68.99` |
| **Portainer** | `http://192.168.68.99:9000` |
| **Stage URL** | `http://192.168.68.99:3001` |
| **Production URL** | `http://192.168.68.99:3000` |
| **Registry** | Docker Hub (`docker.io`) |
| **Watchtower** | Ja configurado e funcional |

---

## Controle de Progresso

### Legenda de Status (GitFlow)
| Status | Descricao |
|--------|-----------|
| `TODO` | Nao iniciada |
| `IN_PROGRESS` | Em desenvolvimento |
| `REVIEW` | Aguardando code review |
| `ACCEPTANCE_TESTING` | Testando em Stage |
| `BLOCKED_BY_BUG` | Bug encontrado no teste |
| `READY_TO_PROD` | Aprovado para producao |
| `DONE` | Concluida e em producao |

### Sprint 0 - Infraestrutura Base
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| DEVOPS-001 | Criar Dockerfile | TODO | - |
| DEVOPS-002 | docker-compose.stage.yml | TODO | - |
| DEVOPS-002B | docker-compose.prod.yml | TODO | - |
| DEVOPS-003 | Repositorio GitHub + GitFlow | REVIEW | Claude |
| DEVOPS-004 | GitHub Actions - CI | TODO | - |
| DEVOPS-006 | GitHub Secrets Docker Hub | TODO | - |
| DEVOPS-008 | Stack Stage no Portainer | TODO | - |
| DEVOPS-014 | Pre-commit hooks | TODO | - |
| DEVOPS-015 | Script setup desenvolvimento | TODO | - |
| DEVOPS-016 | Setup inicial homeserver | TODO | - |

### Sprint 0.5 - Testes de Integracao
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| DEVOPS-005 | GitHub Actions - Testes Integracao | TODO | - |

### Sprint 1 - Deploy Automatizado
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| DEVOPS-007 | GitHub Actions - CD Stage | TODO | - |
| DEVOPS-007B | GitHub Actions - CD Production | TODO | - |
| DEVOPS-009 | Validar Watchtower + Stage | TODO | - |
| DEVOPS-011 | Healthcheck endpoint | TODO | - |

### Sprint 2 - Production + Monitoramento
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| DEVOPS-008B | Stack Production no Portainer | TODO | - |
| DEVOPS-009B | Validar Watchtower + Production | TODO | - |
| DEVOPS-010 | Backup automatico bancos | TODO | - |
| DEVOPS-012 | Prometheus/Grafana | TODO | - |
| DEVOPS-013 | Logging Loki | TODO | - |
| DEVOPS-017 | Documentacao deploy/operacao | TODO | - |
| DEVOPS-018 | Documentacao promocao Stage->Prod | TODO | - |

### Sprint 5 - Futuro
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| DEVOPS-019 | SSL/TLS interface web | TODO | - |
| DEVOPS-020 | Documentacao migracao cloud | TODO | - |

---

## Resumo

Este documento contem todas as tarefas relacionadas a infraestrutura, Docker, CI/CD e deploy para o ambiente de homeserver.

**Documentacao Relacionada:**
- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md) - Estados das tasks, code review, branches, deploy
- [Tasks de Bugfixes](/tasks/tasks_bugfixes.md) - Bugs encontrados durante Acceptance Testing

---

## Contexto de Infraestrutura

### Homeserver - Dois Ambientes

| Ambiente | Imagem | Porta | Watchtower | TRADING_MODE | Banco |
|----------|--------|-------|------------|--------------|-------|
| **Stage** | `btcbot:stage` | 3001 | Habilitado | `demo` | postgres-stage |
| **Production** | `btcbot:latest` | 3000 | Habilitado | `live` | postgres-prod |

### Fluxo de Deploy (Stage -> Production)

```
PR merged para main
        |
        v
+-------------------+
| CD Stage (auto)   |
| Build + Push      |
| btcbot:stage      |
+--------+----------+
         |
         v
+-------------------+
| Watchtower Stage  |
| Auto-update       |
+--------+----------+
         |
         v
+-------------------+
| Testes em Stage   |
| (ACCEPTANCE_TEST) |
+--------+----------+
         |
         | Se bug: Task -> BLOCKED_BY_BUG
         |         Tester cria task em tasks_bugfixes.md
         | Se OK: Aprovado para prod
         v
+-------------------+
| CD Prod (manual)  |
| Retag stage ->    |
| latest + Push     |
+--------+----------+
         |
         v
+-------------------+
| Watchtower Prod   |
| Auto-update       |
+-------------------+
```

**Vantagens:**
- Stage atualiza automaticamente apos merge
- Production usa a **mesma imagem** ja testada em Stage (sem novo build)
- CD Prod apenas retagueia a imagem
- Rollback simples via Portainer (tag anterior)

### GitFlow (Estados das Tasks)

```
TODO -> IN_PROGRESS -> REVIEW -> ACCEPTANCE_TESTING -> READY_TO_PROD -> DONE
                                        |
                                   (Se bug encontrado)
                                        |
                                        v
                               +------------------+
                               | BLOCKED_BY_BUG   |
                               | Task bloqueada   |
                               +--------+---------+
                                        |
                                        v
                               Tester cria task em
                               tasks_bugfixes.md
                                        |
                                        | Dev corrige bugfix
                                        v
                               Bugfix DONE -> Task desbloqueada
                                        |
                                        v
                               ACCEPTANCE_TESTING (reteste)
```

Ver documentacao completa: [GitFlow](/docs/GITFLOW.md)

---

## Legenda

- **Complexidade:** P (Pequena ~0.5 dia), M (Media ~1-2 dias), G (Grande ~3-5 dias)
- **Prioridade:** Alta, Media, Baixa

---

## Tarefas

### DEVOPS-001: Criar Dockerfile para o bot

**Status:** TODO

**Descricao:**
Criar Dockerfile otimizado para executar o bot Python em container, com healthcheck integrado para funcionamento com Watchtower.

**Criterios de Aceite:**
- [ ] Arquivo `Dockerfile` na raiz do projeto
- [ ] Base image: `python:3.12-slim`
- [ ] Multi-stage build para imagem menor
- [ ] Instalar apenas dependencias de producao
- [ ] Usuario nao-root para seguranca:
  ```dockerfile
  RUN useradd --create-home --shell /bin/bash btcbot
  USER btcbot
  ```
- [ ] Healthcheck configurado (usado por Watchtower e Portainer):
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
  ```
- [ ] Labels OCI para metadados:
  ```dockerfile
  LABEL org.opencontainers.image.source="https://github.com/OWNER/btcbot"
  LABEL org.opencontainers.image.description="BTC Grid Trading Bot"
  ```
- [ ] Instalar curl para healthcheck
- [ ] Volume para logs: `VOLUME ["/app/logs"]`
- [ ] Tamanho da imagem < 500MB
- [ ] Build sem warnings: `docker build -t btcbot .`

**Dependencias:** Nenhuma

**Paralelo com:** DEVOPS-003, DEVOPS-016

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-002: Criar docker-compose.stage.yml

**Status:** TODO

**Descricao:**
Criar arquivo docker-compose para ambiente de Stage, com Watchtower habilitado e TRADING_MODE=demo.

**Criterios de Aceite:**
- [ ] Arquivo `docker-compose.stage.yml` na raiz do projeto
- [ ] Servico `bot-stage`:
  ```yaml
  bot-stage:
    image: docker.io/${DOCKER_USERNAME}/btcbot:stage
    container_name: btcbot-stage
    restart: unless-stopped
    ports:
      - "3001:8080"
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    volumes:
      - ./logs-stage:/app/logs
    environment:
      - TRADING_MODE=demo
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-stage:5432/${POSTGRES_DB}
    env_file:
      - .env.stage
    networks:
      - btcbot-stage-network
    depends_on:
      postgres-stage:
        condition: service_healthy
  ```
- [ ] Servico `postgres-stage`:
  ```yaml
  postgres-stage:
    image: postgres:15
    container_name: btcbot-postgres-stage
    restart: unless-stopped
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-btcbot}"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata-stage:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-btcbot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-btcbot_stage}
    networks:
      - btcbot-stage-network
  ```
- [ ] Volume `pgdata-stage` para persistencia do banco
- [ ] Network `btcbot-stage-network` (bridge)
- [ ] Arquivo `.env.stage.example` com todas as variaveis
- [ ] Labels Watchtower:
  - `enable=true` para bot (auto-update)
  - `enable=false` para postgres (nunca auto-update)
- [ ] TRADING_MODE=demo (OBRIGATORIO para Stage)

**Dependencias:** DEVOPS-001

**Paralelo com:** DEVOPS-003

**Complexidade:** M

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-002B: Criar docker-compose.prod.yml

**Status:** TODO

**Descricao:**
Criar arquivo docker-compose para ambiente de Production, com Watchtower habilitado e TRADING_MODE=live.

**Criterios de Aceite:**
- [ ] Arquivo `docker-compose.prod.yml` na raiz do projeto
- [ ] Servico `bot-prod`:
  ```yaml
  bot-prod:
    image: docker.io/${DOCKER_USERNAME}/btcbot:latest
    container_name: btcbot-prod
    restart: unless-stopped
    ports:
      - "3000:8080"
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    volumes:
      - ./logs-prod:/app/logs
    environment:
      - TRADING_MODE=live
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-prod:5432/${POSTGRES_DB}
    env_file:
      - .env.prod
    networks:
      - btcbot-prod-network
    depends_on:
      postgres-prod:
        condition: service_healthy
  ```
- [ ] Servico `postgres-prod`:
  ```yaml
  postgres-prod:
    image: postgres:15
    container_name: btcbot-postgres-prod
    restart: unless-stopped
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-btcbot}"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata-prod:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-btcbot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-btcbot_prod}
    networks:
      - btcbot-prod-network
  ```
- [ ] Volume `pgdata-prod` para persistencia do banco (SEPARADO de stage)
- [ ] Network `btcbot-prod-network` (bridge, SEPARADA de stage)
- [ ] Arquivo `.env.prod.example` com todas as variaveis
- [ ] Labels Watchtower:
  - `enable=true` para bot (auto-update apos CD Prod manual)
  - `enable=false` para postgres (nunca auto-update)
- [ ] TRADING_MODE=live (producao real)
- [ ] Credenciais de API de producao (diferentes de stage)

**Dependencias:** DEVOPS-002

**Paralelo com:** DEVOPS-006

**Complexidade:** M

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-003: Criar repositorio GitHub com estrutura GitFlow

**Status:** REVIEW

**Descricao:**
Criar repositorio no GitHub seguindo a estrutura definida no [GitFlow](/docs/GITFLOW.md), com branches protegidos e templates de PR.

**Criterios de Aceite:**
- [ ] Repositorio criado no GitHub
- [ ] Branch `main` como principal (codigo de producao)
- [ ] Branch protection para `main`:
  - Requer PR aprovado por reviewer da mesma disciplina
  - Requer CI passando
  - Nao permitir push direto
- [ ] Templates de PR criados (conforme GitFlow):
  - `.github/PULL_REQUEST_TEMPLATE/feature.md`
  - `.github/PULL_REQUEST_TEMPLATE/bugfix.md`
  - `.github/PULL_REQUEST_TEMPLATE/hotfix.md`
- [ ] Issue templates:
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] Labels configurados:
  - Por tipo: `feature`, `bugfix`, `hotfix`, `documentation`
  - Por prioridade: `priority:high`, `priority:medium`, `priority:low`
  - Por disciplina: `backend`, `frontend`, `devops`, `database`
  - Por status: `needs-review`, `approved`, `blocked`
- [ ] `.gitignore` completo:
  ```
  .env
  .env.*
  !.env.*.example
  logs*/
  *.log
  __pycache__/
  *.pyc
  .pytest_cache/
  .venv/
  venv/
  .idea/
  .vscode/
  pgdata*/
  ```
- [ ] README.md com badges de CI/CD
- [ ] CONTRIBUTING.md referenciando GitFlow
- [ ] LICENSE (MIT)

**Dependencias:** Nenhuma

**Paralelo com:** DEVOPS-001, DEVOPS-016

**Complexidade:** M

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-004: Configurar GitHub Actions - CI

**Status:** TODO

**Descricao:**
Pipeline de CI que roda em todo push e PR, validando codigo antes do code review.

**Criterios de Aceite:**
- [ ] Arquivo `.github/workflows/ci.yml`
- [ ] Triggers:
  ```yaml
  on:
    push:
      branches: ['**']  # Todas as branches
    pull_request:
      branches: [main]
  ```
- [ ] Jobs paralelos:
  ```yaml
  jobs:
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: '3.12'
        - run: pip install ruff
        - run: ruff check .
        - run: ruff format --check .

    typecheck:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: '3.12'
        - run: pip install mypy types-all
        - run: mypy .

    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: '3.12'
        - run: pip install -r requirements.txt -r requirements-dev.txt
        - run: pytest --cov --cov-report=xml
        - uses: codecov/codecov-action@v3

    build:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: docker/setup-buildx-action@v3
        - name: Build (sem push)
          uses: docker/build-push-action@v5
          with:
            context: .
            push: false
            tags: btcbot:test
  ```
- [ ] Cache de pip dependencies
- [ ] Report de cobertura no PR
- [ ] Badge de status no README
- [ ] Tempo de execucao < 5 minutos
- [ ] Todos os jobs devem passar para PR ser aprovavel

**Dependencias:** DEVOPS-003

**Paralelo com:** DEVOPS-006, DEVOPS-014

**Complexidade:** M

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-005: Configurar GitHub Actions - Testes de Integracao

**Status:** TODO

**Descricao:**
Pipeline para testes de integracao com banco PostgreSQL real, roda em PRs para main.

**Criterios de Aceite:**
- [ ] Arquivo `.github/workflows/integration.yml`
- [ ] Triggers:
  - Pull Request para `main`
  - Manual (workflow_dispatch)
- [ ] Service container PostgreSQL:
  ```yaml
  services:
    postgres:
      image: postgres:15
      env:
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
        POSTGRES_DB: btcbot_test
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  ```
- [ ] Steps:
  - Checkout
  - Setup Python 3.12
  - Install dependencies
  - Run migrations
  - Run integration tests: `pytest -m integration`
- [ ] Variaveis de ambiente para conexao com banco de teste
- [ ] Timeout de 15 minutos
- [ ] Deve passar para PR poder ser mergeado

**Dependencias:** DEVOPS-004, DB-011

**Paralelo com:** Nenhuma

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### DEVOPS-006: Configurar GitHub Secrets para Docker Hub

**Status:** TODO

**Descricao:**
Configurar secrets necessarios no GitHub para os pipelines de CD fazerem push de imagens no Docker Hub.

**Criterios de Aceite:**
- [ ] Secrets obrigatorios configurados:
  ```
  DOCKER_REGISTRY   = docker.io
  DOCKER_USERNAME   = <usuario_dockerhub>
  DOCKER_PASSWORD   = <access_token_dockerhub>
  ```
- [ ] Secrets opcionais para notificacao:
  ```
  DISCORD_WEBHOOK   - Webhook para notificacoes de deploy
  ```
- [ ] Como obter o Access Token do Docker Hub:
  1. Acessar https://hub.docker.com/settings/security
  2. Clicar em "New Access Token"
  3. Nome: `btcbot-github-actions`
  4. Permissoes: Read & Write
  5. Copiar token gerado (mostrado apenas uma vez)
- [ ] Testar login no registry via workflow de teste
- [ ] Documentar procedimento de rotacao de tokens (a cada 90 dias)

**Dependencias:** DEVOPS-003

**Paralelo com:** DEVOPS-004

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-007: Configurar GitHub Actions - CD Stage

**Status:** TODO

**Descricao:**
Pipeline de CD que faz build da imagem e push da tag `btcbot:stage` automaticamente apos merge em main.

**Criterios de Aceite:**
- [ ] Arquivo `.github/workflows/cd-stage.yml`:
  ```yaml
  name: CD Stage

  on:
    push:
      branches: [main]

  concurrency:
    group: cd-stage
    cancel-in-progress: true

  env:
    REGISTRY: docker.io
    IMAGE_NAME: ${{ secrets.DOCKER_USERNAME }}/btcbot

  jobs:
    build-and-push-stage:
      runs-on: ubuntu-latest
      permissions:
        contents: read
        packages: write

      steps:
        - name: Checkout
          uses: actions/checkout@v4

        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3

        - name: Login to Registry
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ secrets.DOCKER_USERNAME }}
            password: ${{ secrets.DOCKER_PASSWORD }}

        - name: Extract metadata
          id: meta
          uses: docker/metadata-action@v5
          with:
            images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
            tags: |
              type=raw,value=stage
              type=sha,prefix=stage-

        - name: Build and push
          uses: docker/build-push-action@v5
          with:
            context: .
            push: true
            tags: ${{ steps.meta.outputs.tags }}
            labels: ${{ steps.meta.outputs.labels }}
            cache-from: type=gha
            cache-to: type=gha,mode=max

    notify:
      needs: build-and-push-stage
      runs-on: ubuntu-latest
      if: always()
      steps:
        - name: Notify Discord
          if: ${{ secrets.DISCORD_WEBHOOK != '' }}
          uses: sarisia/actions-status-discord@v1
          with:
            webhook: ${{ secrets.DISCORD_WEBHOOK }}
            status: ${{ needs.build-and-push-stage.result }}
            title: "BTC Grid Bot - Stage Deploy"
            description: |
              Image btcbot:stage pushed to registry.
              Watchtower Stage will update automatically.
              Commit: ${{ github.sha }}
  ```
- [ ] Tags geradas:
  - `stage` - sempre atualizada em cada merge para main
  - `stage-xxxxxxx` - commit SHA para rastreabilidade
- [ ] Cache de build via GitHub Actions cache
- [ ] Concurrency para cancelar builds anteriores
- [ ] Notificacao Discord de sucesso/falha

**Dependencias:** DEVOPS-004, DEVOPS-005, DEVOPS-006

**Paralelo com:** DEVOPS-011

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Alta

---

### DEVOPS-007B: Configurar GitHub Actions - CD Production

**Status:** TODO

**Descricao:**
Pipeline de CD **manual** que promove a imagem de Stage para Production, retagueando `btcbot:stage` para `btcbot:latest`. NAO faz novo build.

**Criterios de Aceite:**
- [ ] Arquivo `.github/workflows/cd-prod.yml`:
  ```yaml
  name: CD Production

  on:
    workflow_dispatch:
      inputs:
        stage_sha:
          description: 'SHA da imagem stage a promover (ex: stage-abc1234). Deixe vazio para usar stage:latest'
          required: false
          default: ''
        confirm:
          description: 'Digite "DEPLOY" para confirmar'
          required: true

  concurrency:
    group: cd-prod
    cancel-in-progress: false  # NAO cancelar deploy de producao

  env:
    REGISTRY: docker.io
    IMAGE_NAME: ${{ secrets.DOCKER_USERNAME }}/btcbot

  jobs:
    validate:
      runs-on: ubuntu-latest
      steps:
        - name: Validate confirmation
          if: ${{ github.event.inputs.confirm != 'DEPLOY' }}
          run: |
            echo "ERROR: Confirmacao invalida. Digite 'DEPLOY' para confirmar."
            exit 1

    promote-to-prod:
      needs: validate
      runs-on: ubuntu-latest
      permissions:
        contents: read
        packages: write

      steps:
        - name: Login to Registry
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ secrets.DOCKER_USERNAME }}
            password: ${{ secrets.DOCKER_PASSWORD }}

        - name: Set source tag
          id: source
          run: |
            if [ -z "${{ github.event.inputs.stage_sha }}" ]; then
              echo "tag=stage" >> $GITHUB_OUTPUT
            else
              echo "tag=${{ github.event.inputs.stage_sha }}" >> $GITHUB_OUTPUT
            fi

        - name: Pull stage image
          run: |
            docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.source.outputs.tag }}

        - name: Retag as latest
          run: |
            docker tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.source.outputs.tag }} \
                       ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

        - name: Push latest
          run: |
            docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

    notify:
      needs: promote-to-prod
      runs-on: ubuntu-latest
      if: always()
      steps:
        - name: Notify Discord
          if: ${{ secrets.DISCORD_WEBHOOK != '' }}
          uses: sarisia/actions-status-discord@v1
          with:
            webhook: ${{ secrets.DISCORD_WEBHOOK }}
            status: ${{ needs.promote-to-prod.result }}
            title: "BTC Grid Bot - PRODUCTION Deploy"
            color: 0xff0000
            description: |
              PRODUCTION DEPLOY
              Image btcbot:latest updated.
              Watchtower Prod will update automatically.
              Triggered by: ${{ github.actor }}
  ```
- [ ] Trigger **manual** via workflow_dispatch
- [ ] Requer confirmacao digitando "DEPLOY"
- [ ] NAO faz novo build (usa imagem ja testada em Stage)
- [ ] Operacoes:
  1. Pull `btcbot:stage` (ou SHA especifico)
  2. Retag para `btcbot:latest`
  3. Push `btcbot:latest`
- [ ] Notificacao destacada no Discord (producao)
- [ ] Concurrency NAO cancela deploys em andamento

**Dependencias:** DEVOPS-007

**Paralelo com:** DEVOPS-018

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Alta

---

### DEVOPS-008: Configurar stack Stage no Portainer

**Status:** TODO

**Descricao:**
Criar e configurar stack do bot no Portainer do homeserver para ambiente de Stage.

**Criterios de Aceite:**
- [ ] Acessar Portainer: `http://192.168.68.99:9000`
- [ ] Criar stack com nome `btcbot-stage`
- [ ] Importar/colar docker-compose.stage.yml
- [ ] Configurar variaveis de ambiente:
  - `DOCKER_REGISTRY=docker.io`
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
  - `BINGX_API_KEY`, `BINGX_SECRET_KEY` (credenciais de DEMO)
  - `TRADING_MODE=demo` (OBRIGATORIO)
  - Demais configuracoes do bot
- [ ] Verificar volumes mapeados corretamente:
  - `pgdata-stage` para banco
  - `logs-stage` para logs (`/opt/btcbot/logs-stage`)
- [ ] Verificar network `btcbot-stage-network` criada
- [ ] Confirmar containers visiveis:
  - `btcbot-stage` - porta 3001, status healthy
  - `btcbot-postgres-stage` - status healthy
- [ ] Testar acesso a logs via Portainer
- [ ] Verificar acesso ao bot: `http://192.168.68.99:3001/health`

**Dependencias:** DEVOPS-002, DEVOPS-016

**Paralelo com:** DEVOPS-015

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-008B: Configurar stack Production no Portainer

**Status:** TODO

**Descricao:**
Criar e configurar stack do bot no Portainer do homeserver para ambiente de Production.

**Criterios de Aceite:**
- [ ] Acessar Portainer: `http://192.168.68.99:9000`
- [ ] Criar stack com nome `btcbot-prod`
- [ ] Importar/colar docker-compose.prod.yml
- [ ] Configurar variaveis de ambiente:
  - `DOCKER_REGISTRY=docker.io`
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
  - `BINGX_API_KEY`, `BINGX_SECRET_KEY` (credenciais de PRODUCAO - DIFERENTES de stage!)
  - `TRADING_MODE=live` (producao real)
  - Demais configuracoes do bot
- [ ] Verificar volumes mapeados corretamente:
  - `pgdata-prod` para banco (SEPARADO de stage)
  - `logs-prod` para logs (`/opt/btcbot/logs-prod`)
- [ ] Verificar network `btcbot-prod-network` criada (SEPARADA de stage)
- [ ] Confirmar containers visiveis:
  - `btcbot-prod` - porta 3000, status healthy
  - `btcbot-postgres-prod` - status healthy
- [ ] Testar acesso a logs via Portainer
- [ ] Verificar acesso ao bot: `http://192.168.68.99:3000/health`
- [ ] **IMPORTANTE:** Nao subir ate Stage estar validado

**Dependencias:** DEVOPS-002B, DEVOPS-008

**Paralelo com:** Nenhuma

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Alta

---

### DEVOPS-009: Validar integracao Watchtower com Stage

**Status:** TODO

**Descricao:**
Verificar e testar que Watchtower esta configurado corretamente para auto-update do container de Stage.

**Criterios de Aceite:**
- [ ] Verificar Watchtower rodando no homeserver:
  ```bash
  docker ps | grep watchtower
  ```
- [ ] Verificar configuracao do Watchtower:
  ```yaml
  environment:
    - WATCHTOWER_POLL_INTERVAL=30      # Check a cada 30s
    - WATCHTOWER_CLEANUP=true          # Remove imagens antigas
    - WATCHTOWER_LABEL_ENABLE=true     # Usar labels para filtrar
  ```
- [ ] Verificar label no container btcbot-stage:
  ```bash
  docker inspect btcbot-stage | grep watchtower
  # Deve mostrar: "com.centurylinklabs.watchtower.enable": "true"
  ```
- [ ] Testar fluxo completo Stage:
  1. Fazer pequena mudanca no codigo
  2. Abrir PR, passar code review, fazer merge para main
  3. Aguardar CD Stage pipeline (build + push btcbot:stage)
  4. Verificar logs do Watchtower: `docker logs watchtower`
  5. Confirmar que container btcbot-stage foi atualizado (< 1 min apos push)
  6. Verificar healthcheck passou
- [ ] Documentar tempo medio de deploy Stage (merge -> container atualizado)

**Dependencias:** DEVOPS-007, DEVOPS-008

**Paralelo com:** DEVOPS-017

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Alta

---

### DEVOPS-009B: Validar integracao Watchtower com Production

**Status:** TODO

**Descricao:**
Verificar e testar que Watchtower esta configurado corretamente para auto-update do container de Production.

**Criterios de Aceite:**
- [ ] Verificar label no container btcbot-prod:
  ```bash
  docker inspect btcbot-prod | grep watchtower
  # Deve mostrar: "com.centurylinklabs.watchtower.enable": "true"
  ```
- [ ] Testar fluxo completo Production:
  1. Task em ACCEPTANCE_TESTING foi aprovada em Stage
  2. Task movida para READY_TO_PROD
  3. Executar CD Prod manualmente (workflow_dispatch)
  4. Confirmar retag stage -> latest
  5. Verificar logs do Watchtower: `docker logs watchtower`
  6. Confirmar que container btcbot-prod foi atualizado
  7. Verificar healthcheck passou
  8. Mover task para DONE
- [ ] Documentar tempo medio de deploy Prod (trigger manual -> container atualizado)

**Dependencias:** DEVOPS-007B, DEVOPS-008B

**Paralelo com:** Nenhuma

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Alta

---

### DEVOPS-010: Configurar backup automatico dos bancos

**Status:** TODO

**Descricao:**
Script de backup automatico do PostgreSQL com armazenamento local no homeserver, para ambos os ambientes.

**Criterios de Aceite:**
- [ ] Script `scripts/backup_db.sh`:
  ```bash
  #!/bin/bash
  set -e

  ENV="${1:-stage}"  # stage ou prod
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_DIR="/opt/btcbot/backups/${ENV}"
  BACKUP_FILE="backup_${ENV}_${TIMESTAMP}.sql.gz"
  CONTAINER="btcbot-postgres-${ENV}"

  mkdir -p $BACKUP_DIR

  # Backup via docker exec
  docker exec $CONTAINER pg_dump -U ${POSTGRES_USER:-btcbot} ${POSTGRES_DB:-btcbot} | gzip > $BACKUP_DIR/$BACKUP_FILE

  # Manter apenas ultimos 30 backups
  ls -t $BACKUP_DIR/*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm -f

  echo "[$(date)] Backup criado: $BACKUP_FILE"
  ```
- [ ] Script `scripts/restore_db.sh`:
  ```bash
  #!/bin/bash
  set -e

  ENV="${1:-stage}"
  BACKUP_FILE="$2"
  CONTAINER="btcbot-postgres-${ENV}"

  if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: ./restore_db.sh <stage|prod> <arquivo.sql.gz>"
    exit 1
  fi

  echo "ATENCAO: Isso vai sobrescrever o banco de $ENV!"
  read -p "Continuar? (y/N) " confirm
  [ "$confirm" = "y" ] || exit 0

  gunzip -c $BACKUP_FILE | docker exec -i $CONTAINER psql -U ${POSTGRES_USER:-btcbot} ${POSTGRES_DB:-btcbot}
  echo "Restore concluido em $ENV"
  ```
- [ ] Cron jobs no homeserver:
  ```
  # Stage: backup diario as 3h
  0 3 * * * /opt/btcbot/scripts/backup_db.sh stage >> /opt/btcbot/logs/backup-stage.log 2>&1

  # Prod: backup a cada 6h
  0 */6 * * * /opt/btcbot/scripts/backup_db.sh prod >> /opt/btcbot/logs/backup-prod.log 2>&1
  ```
- [ ] Retencao: 30 backups por ambiente
- [ ] Testar restore em ambiente de desenvolvimento
- [ ] Documentar procedimento de restore

**Dependencias:** DEVOPS-002, DEVOPS-002B, DEVOPS-008, DEVOPS-008B

**Paralelo com:** DEVOPS-012

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Alta

---

### DEVOPS-011: Implementar healthcheck endpoint no bot

**Status:** TODO

**Descricao:**
Criar endpoint HTTP para verificacao de saude do bot, essencial para funcionamento do Watchtower e Portainer.

**Criterios de Aceite:**
- [ ] Servidor HTTP leve (aiohttp) rodando em paralelo ao bot
- [ ] Endpoint `GET /health` na porta configuravel (`HEALTH_PORT=8080`)
- [ ] Resposta JSON:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "timestamp": "2025-01-01T00:00:00Z",
    "environment": "stage",
    "trading_mode": "demo",
    "components": {
      "database": {"status": "healthy", "latency_ms": 5},
      "websocket": {"status": "healthy", "connected": true},
      "exchange_api": {"status": "healthy", "latency_ms": 120}
    },
    "grid": {
      "state": "ACTIVE",
      "open_positions": 3,
      "pending_orders": 5
    }
  }
  ```
- [ ] Status codes:
  - `200`: Todos componentes healthy
  - `503`: Algum componente unhealthy (Watchtower nao atualiza)
- [ ] Timeout de 5 segundos para cada componente
- [ ] Usado por:
  - Docker healthcheck (Dockerfile)
  - docker-compose healthcheck
  - Portainer status
  - Watchtower (verifica apos restart)
- [ ] Nao expor informacoes sensiveis (API keys, etc)
- [ ] Log de requests apenas em nivel DEBUG

**Dependencias:** Nenhuma

**Paralelo com:** DEVOPS-007

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Alta

---

### DEVOPS-012: Configurar monitoramento com Prometheus/Grafana

**Status:** TODO

**Descricao:**
Integrar metricas do bot com Prometheus/Grafana existente no homeserver (se disponivel).

**Criterios de Aceite:**
- [ ] Verificar se Prometheus/Grafana ja existem no homeserver
- [ ] Expor metricas do bot via endpoint `/metrics`:
  ```python
  from prometheus_client import Counter, Gauge, Histogram

  # Metricas
  btcbot_trades_total = Counter('btcbot_trades_total', 'Total de trades executados', ['environment'])
  btcbot_price_current = Gauge('btcbot_price_current', 'Preco atual BTC')
  btcbot_positions_open = Gauge('btcbot_positions_open', 'Posicoes abertas', ['environment'])
  btcbot_pnl_total = Gauge('btcbot_pnl_total', 'PnL total', ['environment'])
  btcbot_orders_pending = Gauge('btcbot_orders_pending', 'Ordens pendentes')
  btcbot_api_latency = Histogram('btcbot_api_latency_seconds', 'Latencia da API')
  ```
- [ ] Adicionar jobs no Prometheus para scrape (ambos ambientes):
  ```yaml
  - job_name: 'btcbot-stage'
    static_configs:
      - targets: ['btcbot-stage:8080']
        labels:
          environment: 'stage'

  - job_name: 'btcbot-prod'
    static_configs:
      - targets: ['btcbot-prod:8080']
        labels:
          environment: 'prod'
  ```
- [ ] Dashboard Grafana com:
  - Seletor de ambiente (Stage/Prod)
  - Preco atual e historico
  - PnL total e por trade
  - Posicoes abertas
  - Latencia das APIs
  - Status dos componentes
- [ ] Alertas Grafana para:
  - Bot desconectado (> 5 min sem metricas)
  - Erro de margem
  - API latency > 1s

**Dependencias:** DEVOPS-011

**Paralelo com:** DEVOPS-013

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Media

---

### DEVOPS-013: Configurar logging centralizado com Loki

**Status:** TODO

**Descricao:**
Integrar logs do bot com Loki/Grafana existente no homeserver (se disponivel).

**Criterios de Aceite:**
- [ ] Verificar se Loki ja existe no homeserver
- [ ] Configurar Promtail para coletar logs dos containers:
  ```yaml
  scrape_configs:
    - job_name: btcbot
      docker_sd_configs:
        - host: unix:///var/run/docker.sock
      relabel_configs:
        - source_labels: ['__meta_docker_container_name']
          regex: '/btcbot-(stage|prod)'
          action: keep
        - source_labels: ['__meta_docker_container_name']
          target_label: 'environment'
          regex: '/btcbot-(stage|prod)'
          replacement: '$1'
  ```
- [ ] Labels nos logs:
  - `app`: btcbot
  - `environment`: stage ou prod
  - `level`: info, warning, error, critical
  - `module`: main, orders, trades, macd, grid
- [ ] Dashboard de logs no Grafana com filtro por ambiente
- [ ] Alertas por padrao de log:
  - 5+ erros em 5 minutos (por ambiente)
  - Qualquer CRITICAL

**Dependencias:** DEVOPS-012

**Paralelo com:** DEVOPS-012

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Media

---

### DEVOPS-014: Configurar pre-commit hooks

**Status:** TODO

**Descricao:**
Configurar hooks de pre-commit para garantir qualidade de codigo antes do commit.

**Criterios de Aceite:**
- [ ] Arquivo `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.8.0
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format

    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.13.0
      hooks:
        - id: mypy
          additional_dependencies: [types-all]

    - repo: https://github.com/Yelp/detect-secrets
      rev: v1.5.0
      hooks:
        - id: detect-secrets
          args: ['--baseline', '.secrets.baseline']

    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v5.0.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
        - id: check-added-large-files
        - id: check-merge-conflict
  ```
- [ ] Arquivo `.ruff.toml` com configuracao
- [ ] Arquivo `mypy.ini` ou `pyproject.toml` com configuracao mypy
- [ ] Arquivo `.secrets.baseline` para detect-secrets
- [ ] Documentacao de instalacao no CONTRIBUTING.md:
  ```bash
  pip install pre-commit
  pre-commit install
  ```

**Dependencias:** DEVOPS-003

**Paralelo com:** DEVOPS-004

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-015: Criar script de setup de desenvolvimento

**Status:** TODO

**Descricao:**
Script para configurar ambiente de desenvolvimento local em < 5 minutos.

**Criterios de Aceite:**
- [ ] Script `scripts/setup_dev.sh`:
  ```bash
  #!/bin/bash
  set -e

  echo "=== BTC Grid Bot - Setup de Desenvolvimento ==="

  # Verificar requisitos
  command -v python3 >/dev/null || { echo "ERRO: Python 3 nao encontrado"; exit 1; }
  command -v docker >/dev/null || { echo "ERRO: Docker nao encontrado"; exit 1; }

  # Verificar versao do Python
  PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    echo "ERRO: Python 3.12+ necessario (encontrado: $PYTHON_VERSION)"
    exit 1
  fi

  # Criar virtualenv
  echo "Criando virtualenv..."
  python3 -m venv .venv
  source .venv/bin/activate

  # Instalar dependencias
  echo "Instalando dependencias..."
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

  # Configurar pre-commit
  echo "Configurando pre-commit..."
  pip install pre-commit
  pre-commit install

  # Copiar .env
  if [ ! -f .env ]; then
    cp .env.stage.example .env
    echo ""
    echo "ATENCAO: Arquivo .env criado a partir de .env.stage.example"
    echo "Configure suas credenciais de DEMO!"
  fi

  # Subir banco de dados local
  echo "Subindo PostgreSQL local..."
  docker-compose -f docker-compose.stage.yml up -d postgres-stage

  # Aguardar banco ficar pronto
  echo "Aguardando PostgreSQL..."
  for i in {1..30}; do
    if docker exec btcbot-postgres-stage pg_isready -U btcbot > /dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # Executar migrations
  echo "Executando migrations..."
  python -m scripts.run_migrations

  echo ""
  echo "=== Setup completo! ==="
  echo ""
  echo "Proximos passos:"
  echo "  1. Ative o virtualenv: source .venv/bin/activate"
  echo "  2. Configure o .env com suas credenciais de DEMO"
  echo "  3. Execute: python main.py"
  ```
- [ ] Tempo de setup < 5 minutos
- [ ] Funciona em macOS e Linux
- [ ] Verifica Python 3.12+
- [ ] Mensagens claras de erro e progresso

**Dependencias:** DEVOPS-002, DEVOPS-014

**Paralelo com:** DEVOPS-008

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-016: Setup inicial no homeserver

**Status:** TODO

**Descricao:**
Verificar e preparar homeserver para rodar o bot (Portainer, Watchtower, diretorios).

**Informacoes do Homeserver:**
- **IP:** `192.168.68.99`
- **SSH:** `ssh usuario@192.168.68.99`
- **Portainer:** `http://192.168.68.99:9000`
- **Watchtower:** Ja configurado e funcional (atualiza outros containers)

**Criterios de Aceite:**
- [ ] Conectar via SSH:
  ```bash
  ssh usuario@192.168.68.99
  ```
- [ ] Verificar Portainer acessivel: `http://192.168.68.99:9000`
- [ ] Verificar Watchtower rodando com configuracao correta:
  ```bash
  docker inspect watchtower | grep -A5 Env
  # Deve ter: WATCHTOWER_POLL_INTERVAL=30, WATCHTOWER_LABEL_ENABLE=true
  ```
- [ ] Verificar conectividade com Docker Hub:
  ```bash
  docker login docker.io
  # Usar credenciais do Docker Hub
  ```
- [ ] Criar estrutura de diretorios:
  ```bash
  sudo mkdir -p /opt/btcbot/{logs-stage,logs-prod,backups/stage,backups/prod,scripts}
  sudo chown -R $USER:$USER /opt/btcbot
  ```
- [ ] Criar arquivos de ambiente:
  - `/opt/btcbot/.env.stage` - credenciais de DEMO
  - `/opt/btcbot/.env.prod` - credenciais de PRODUCAO
- [ ] Copiar scripts de backup/restore para `/opt/btcbot/scripts/`
- [ ] Configurar permissoes de execucao: `chmod +x /opt/btcbot/scripts/*.sh`
- [ ] Documentar:
  - URL de acesso ao Portainer: `http://192.168.68.99:9000`
  - Credenciais (onde encontrar)
  - Como acessar logs de cada ambiente

**Dependencias:** Nenhuma

**Paralelo com:** DEVOPS-001, DEVOPS-003

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DEVOPS-017: Criar documentacao de deploy e operacao

**Status:** TODO

**Descricao:**
Documentar processo completo de deploy e operacao do bot, integrando com GitFlow.

**Criterios de Aceite:**
- [ ] Documento `docs/DEPLOYMENT.md`:
  - Arquitetura de deploy (diagrama com Stage e Prod)
  - Fluxo Stage: Merge -> CD Stage auto -> btcbot:stage -> Watchtower Stage
  - Fluxo Prod: CD Prod manual -> retag -> btcbot:latest -> Watchtower Prod
  - Como fazer deploy para Stage (merge PR para main)
  - Como promover Stage -> Production (workflow_dispatch)
  - Como verificar deploy (Portainer, logs)
  - Como fazer rollback (3 opcoes por ambiente)
  - Referencia ao GitFlow para fluxo de tasks
- [ ] Documento `docs/OPERATIONS.md`:
  - Acesso ao Portainer (URL, login)
  - Visualizar status dos containers (Stage e Prod)
  - Acessar logs em tempo real (por ambiente)
  - Executar comandos no container
  - Acessar banco (psql) - Stage vs Prod
  - Backup manual (por ambiente)
  - Restore de backup (por ambiente)
- [ ] Documento `docs/TROUBLESHOOTING.md`:
  - Watchtower nao atualiza container
  - Container nao inicia / crash loop
  - Healthcheck falhando
  - Erro de conexao com exchange
  - Erro de conexao com banco
  - Problemas de memoria/CPU
  - Rate limit da API
  - Diferenca de comportamento Stage vs Prod
- [ ] Diagrama de arquitetura (Mermaid ou ASCII)

**Dependencias:** DEVOPS-007, DEVOPS-007B, DEVOPS-008, DEVOPS-008B, DEVOPS-009

**Paralelo com:** Qualquer tarefa

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Alta

---

### DEVOPS-018: Documentar processo de promocao Stage -> Production

**Status:** TODO

**Descricao:**
Criar guia detalhado do processo de promocao de uma versao de Stage para Production.

**Criterios de Aceite:**
- [ ] Documento `docs/PROMOTION.md`:
  - Pre-requisitos (task em READY_TO_PROD, testes passaram)
  - Passo a passo do workflow CD Prod
  - Como identificar SHA da imagem em Stage
  - Verificacao pos-deploy
  - Checklist de validacao
- [ ] Integracao com GitFlow (estados READY_TO_PROD -> DONE)
- [ ] Exemplos de comandos de verificacao
- [ ] Referencia ao arquivo tasks_bugfix.md para bugs encontrados

**Dependencias:** DEVOPS-007B, DEVOPS-017

**Paralelo com:** Nenhuma

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Alta

---

### DEVOPS-019: Configurar SSL/TLS para interface web (futuro)

**Status:** TODO

**Descricao:**
Configurar certificados SSL para a interface web quando implementada.

**Criterios de Aceite:**
- [ ] Nginx ou Traefik como reverse proxy
- [ ] Certificado Let's Encrypt
- [ ] Renovacao automatica
- [ ] Redirect HTTP -> HTTPS
- [ ] Headers de seguranca (HSTS, etc)
- [ ] Configurar para ambos ambientes (stage e prod)

**Dependencias:** FE-012 (interface web)

**Paralelo com:** Nenhuma

**Complexidade:** P

**Sprint:** 5

**Prioridade:** Baixa

---

### DEVOPS-020: Documentar migracao para cloud (futuro)

**Status:** TODO

**Descricao:**
Documentar processo de migracao do homeserver para cloud quando necessario.

**Criterios de Aceite:**
- [ ] Documento `docs/CLOUD_MIGRATION.md`:
  - Opcoes de cloud (AWS, GCP, DigitalOcean)
  - Estimativa de custos
  - Servicos equivalentes
  - Checklist de migracao
  - Mudancas necessarias no CI/CD
  - Migracao de dados Stage e Prod

**Dependencias:** Nenhuma

**Paralelo com:** Nenhuma

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Baixa

---

## Grafico de Dependencias

```
Sprint 0 (Infraestrutura Base):

DEVOPS-016 (Homeserver) --------+
                                |
DEVOPS-001 (Dockerfile) --------+--> DEVOPS-002 (compose stage)
                                |           |
DEVOPS-003 (GitHub repo) -------+           +--> DEVOPS-002B (compose prod)
     |                                      |
     +---> DEVOPS-004 (CI) -------> DEVOPS-008 (Stack Stage)
     |           |
     +---> DEVOPS-006 (Secrets)
     |
     +---> DEVOPS-014 (pre-commit)
                |
                v
          DEVOPS-015 (Setup dev)

Sprint 0.5:
DEVOPS-004 + DB-011 ---> DEVOPS-005 (Testes integracao)

Sprint 1 (Deploy Automatizado):
DEVOPS-005 + DEVOPS-006 ---> DEVOPS-007 (CD Stage)
                                   |
                                   +---> DEVOPS-007B (CD Prod)
                                   |
                                   +---> DEVOPS-009 (Watchtower Stage)
                                   |
DEVOPS-011 (Healthcheck) <---------+

Sprint 2 (Production + Monitoramento):
DEVOPS-002B ---> DEVOPS-008B (Stack Prod)
                      |
DEVOPS-007B ----------+---> DEVOPS-009B (Watchtower Prod)
                      |
DEVOPS-017 (Docs) <---+---> DEVOPS-018 (Promocao)
                      |
DEVOPS-010 (Backup) <-+
                      |
DEVOPS-011 ---> DEVOPS-012 (Prometheus) ---> DEVOPS-013 (Loki)

Sprint 5:
DEVOPS-019 (SSL)
DEVOPS-020 (Cloud docs)
```

---

## Ordem de Implementacao Sugerida

### Sprint 0 (Infraestrutura Base)
1. DEVOPS-016 - Verificar homeserver (Portainer, Watchtower)
2. DEVOPS-003 - Criar repositorio GitHub com estrutura GitFlow
3. DEVOPS-001 - Dockerfile com healthcheck
4. DEVOPS-002 - docker-compose.stage.yml
5. DEVOPS-002B - docker-compose.prod.yml
6. DEVOPS-014 - Pre-commit hooks
7. DEVOPS-004 - CI pipeline
8. DEVOPS-006 - GitHub Secrets para Registry
9. DEVOPS-008 - Criar stack Stage no Portainer
10. DEVOPS-015 - Script de setup de desenvolvimento

### Sprint 0.5
11. DEVOPS-005 - Testes de integracao

### Sprint 1 (Deploy Automatizado)
12. DEVOPS-011 - Healthcheck endpoint
13. DEVOPS-007 - CD Stage pipeline (Build + Push btcbot:stage)
14. DEVOPS-007B - CD Prod pipeline (Retag stage -> latest)
15. DEVOPS-009 - Validar integracao Watchtower com Stage

### Sprint 2 (Production + Monitoramento)
16. DEVOPS-008B - Criar stack Production no Portainer
17. DEVOPS-009B - Validar integracao Watchtower com Production
18. DEVOPS-010 - Backup automatico (ambos ambientes)
19. DEVOPS-017 - Documentacao de deploy
20. DEVOPS-018 - Documentacao de promocao Stage -> Prod
21. DEVOPS-012 - Prometheus/Grafana (se disponivel)
22. DEVOPS-013 - Loki (se disponivel)

### Sprint 5 (Futuro)
23. DEVOPS-019 - SSL/TLS
24. DEVOPS-020 - Documentacao cloud

---

## Arquitetura de Deploy

```
+-------------------+     +-------------------+     +------------------+
|    Developer      |     |     GitHub        |     |   Docker Hub     |
|    Workstation    |     |                   |     |   (docker.io)    |
+--------+----------+     +--------+----------+     +--------+---------+
         |                         |                         ^
         | git push                |                         |
         | (feature branch)        |                         |
         v                         |                         |
+-------------------+              |                         |
|  Pull Request     |              |                         |
|  (Code Review)    |              |                         |
+--------+----------+              |                         |
         |                         |                         |
         | merge to main           |                         |
         v                         v                         |
+-------------------+     +-------------------+              |
|     main branch   |---->| CD Stage (auto)   |--------------+
|                   |     | btcbot:stage      |              |
+-------------------+     +-------------------+              |
                                                             |
                          +-------------------+              |
                          | CD Prod (manual)  |--------------+
                          | retag -> latest   |
                          +-------------------+


+------------------------------------------------------------------+
|                 HOMESERVER (192.168.68.99)                        |
|                                                                  |
|  +------------------+         +------------------+               |
|  |   Watchtower     |-------->|   Docker Hub     |               |
|  | (poll 30s)       |  pull   |   (docker.io)    |               |
|  +--------+---------+         +------------------+               |
|           |                                                      |
|           | auto-update                                          |
|           v                                                      |
|  +------------------------+     +------------------------+       |
|  |      STAGE             |     |     PRODUCTION         |       |
|  +------------------------+     +------------------------+       |
|  |                        |     |                        |       |
|  | +------------------+   |     | +------------------+   |       |
|  | |  btcbot-stage    |   |     | |  btcbot-prod     |   |       |
|  | |  :stage          |   |     | |  :latest         |   |       |
|  | |  :3001           |   |     | |  :3000           |   |       |
|  | |  TRADING=demo    |   |     | |  TRADING=live    |   |       |
|  | +--------+---------+   |     | +--------+---------+   |       |
|  |          |             |     |          |             |       |
|  | +--------v---------+   |     | +--------v---------+   |       |
|  | | postgres-stage   |   |     | | postgres-prod    |   |       |
|  | +------------------+   |     | +------------------+   |       |
|  |                        |     |                        |       |
|  +------------------------+     +------------------------+       |
|                                                                  |
|  +------------------+                                            |
|  |   Portainer      |  http://192.168.68.99:9000                 |
|  +------------------+                                            |
|                                                                  |
+------------------------------------------------------------------+

URLs de Acesso:
- Portainer: http://192.168.68.99:9000
- Stage:     http://192.168.68.99:3001/health
- Prod:      http://192.168.68.99:3000/health
- SSH:       ssh usuario@192.168.68.99
```

---

## GitHub Actions Workflows

| Workflow | Arquivo | Trigger | Acao | Tag Gerada |
|----------|---------|---------|------|------------|
| CI | `ci.yml` | Push em qualquer branch | Lint, test, build (sem push) | - |
| Integration | `integration.yml` | PR para main | Testes com PostgreSQL | - |
| CD Stage | `cd-stage.yml` | Merge em main (auto) | Build + push | `btcbot:stage` |
| CD Prod | `cd-prod.yml` | Manual (workflow_dispatch) | Retag stage -> latest | `btcbot:latest` |

---

## Secrets Necessarios no GitHub

| Secret | Descricao | Obrigatorio | Valor |
|--------|-----------|-------------|-------|
| `DOCKER_REGISTRY` | URL do registry | Sim | `docker.io` |
| `DOCKER_USERNAME` | Usuario do Docker Hub | Sim | `<seu_usuario>` |
| `DOCKER_PASSWORD` | Access Token do Docker Hub | Sim | `dckr_pat_xxx...` |
| `DISCORD_WEBHOOK` | Webhook notificacoes | Nao | `https://discord.com/api/webhooks/...` |

**Como obter o Access Token:**
1. Acessar https://hub.docker.com/settings/security
2. Clicar em "New Access Token"
3. Nome: `btcbot-github-actions`
4. Permissoes: Read & Write
5. Copiar e salvar (mostrado apenas uma vez)

---

## Checklist de Seguranca

- [ ] Tokens do registry com escopo minimo (apenas push de imagens)
- [ ] Secrets nunca em codigo, logs ou imagens
- [ ] Imagem Docker com usuario nao-root
- [ ] Redes Docker separadas (stage-network e prod-network)
- [ ] Portas expostas: 3000 (prod), 3001 (stage)
- [ ] PostgreSQL nao exposto externamente (ambos ambientes)
- [ ] Acesso ao Portainer protegido por senha forte
- [ ] Watchtower com label_enable para evitar updates indesejados
- [ ] Backups automaticos de ambos os bancos
- [ ] detect-secrets no pre-commit
- [ ] Credenciais de producao NUNCA em Stage

---

## Referencias

- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md)
- [Tasks de Bugfixes](/tasks/tasks_bugfixes.md)
- [PRD - Requisitos](/PRD.md)
- [Watchtower Documentation](https://containrrr.dev/watchtower/)
- [Portainer Documentation](https://docs.portainer.io/)

---

*Documento atualizado em 26/12/2025 - Versao 1.6 (Adicionado detalhes do homeserver: IP 192.168.68.99, Docker Hub, SSH)*
