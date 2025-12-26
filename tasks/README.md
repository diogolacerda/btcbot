# BTC Grid Bot - Decomposicao de Tarefas

**Data:** 26 de Dezembro de 2025
**Versao:** 1.5
**Baseado em:** PRD v1.1
**Infraestrutura:** Homeserver + Portainer + Watchtower + Docker Registry

---

## Visao Geral

Este diretorio contem a decomposicao completa das tarefas do roadmap do BTC Grid Bot, organizadas por especialidade.

**Contexto de Infraestrutura:**
- Homeserver com **Portainer** para gerenciamento de containers
- **Watchtower** para auto-update (check a cada 30 segundos)
- **Docker Registry** para armazenamento de imagens (Hub, GHCR ou privado)
- **GitHub Actions** para CI e CD
- **Dois ambientes:** Stage (demo, porta 3001) e Production (live, porta 3000)

**Documentacao Relacionada:**
- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md) - Processo completo de desenvolvimento, code review e deploy

## Arquivos

| Arquivo | Descricao | Total de Tarefas |
|---------|-----------|------------------|
| `PROGRESS.md` | **Visao consolidada do progresso (ATUALIZAR SEMPRE)** | - |
| `tasks_database.md` | Tarefas de banco de dados (schema, migrations, queries) | 11 tarefas |
| `tasks_backend.md` | Tarefas de backend Python (API, logica de negocio) | 20 tarefas |
| `tasks_frontend.md` | Tarefas de frontend/UI (dashboard, visualizacoes) | 15 tarefas |
| `tasks_devops.md` | Tarefas de DevOps (Docker, CI/CD, Portainer, Watchtower) | 20 tarefas |
| `tasks_bugfixes.md` | Bugs encontrados durante Acceptance Testing | Dinamico |

**Total: 66 tarefas (+ bugfixes)**

---

## Ambientes

| Ambiente | Imagem | Porta | TRADING_MODE | Deploy |
|----------|--------|-------|--------------|--------|
| **Stage** | `btcbot:stage` | 3001 | `demo` | Automatico (CD Stage) |
| **Production** | `btcbot:latest` | 3000 | `live` | Manual (CD Prod) |

---

## Arquitetura de Deploy

```
+-------------------+     +-------------------+     +------------------+
|    Developer      |     |     GitHub        |     | Docker Registry  |
|    Workstation    |     |                   |     | (Hub/GHCR/Priv)  |
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
|                   |     | btcbot:stage      |
+-------------------+     +-------------------+

                          +-------------------+
                          | CD Prod (manual)  |
                          | retag -> latest   |--------------+
                          +-------------------+              |
                                                             v

+------------------------------------------------------------------+
|                         HOMESERVER                                |
|                                                                  |
|  +------------------+         +------------------+               |
|  |   Watchtower     |-------->| Docker Registry  |               |
|  | (poll 30s)       |  pull   |                  |               |
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
|  | |  port 3001       |   |     | |  port 3000       |   |       |
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
|  |   Portainer      |  UI para gerenciamento                     |
|  +------------------+                                            |
|                                                                  |
+------------------------------------------------------------------+

Fluxo de Deploy:
1. Developer faz merge para main
2. CD Stage: build e push btcbot:stage (automatico)
3. Watchtower Stage detecta e atualiza container (30s)
4. Tester valida em Stage (porta 3001)
   - Se bug: Task -> BLOCKED_BY_BUG, cria task em tasks_bugfixes.md
   - Se OK: aprova para producao
5. CD Prod: retag stage -> latest (manual)
6. Watchtower Prod detecta e atualiza container
7. Validacao final em Production (porta 3000)
```

---

## Distribuicao por Sprint

| Sprint | Database | Backend | Frontend | DevOps | Total |
|--------|----------|---------|----------|--------|-------|
| 0 | 1 | 1 | 0 | 11 | **13** |
| 0.5 | 4 | 4 | 1 | 1 | **10** |
| 1 | 2 | 3 | 4 | 4 | **13** |
| 2 | 1 | 3 | 2 | 6 | **12** |
| 3 | 1 | 1 | 1 | 0 | **3** |
| 4 | 0 | 4 | 2 | 0 | **6** |
| 5 | 2 | 4 | 5 | 2 | **13** |

---

## Distribuicao por Prioridade

### Prioridade Alta (30 tarefas)
Funcionalidades criticas para o MVP e operacao basica.

| ID | Tarefa | Sprint |
|----|--------|--------|
| DB-001 | PostgreSQL Docker | 0 |
| DB-002 | Schema tabela trades | 0.5 |
| DB-004 | Ordens virtuais | 3 |
| DB-005 | Hits por nivel | 1 |
| DB-006 | ATH history | 1 |
| DB-007 | Eventos de margem | 2 |
| DB-009 | Queries agregacao | 0.5 |
| DB-010 | Row-Level Security | 0.5 |
| DB-011 | Sistema migrations | 0.5 |
| BE-001 | TradeRepository | 0.5 |
| BE-002 | Integracao TP | 0.5 |
| BE-003 | Carregar historico | 0.5 |
| BE-005 | Preco ATH | 1 |
| BE-006 | Contador hits | 1 |
| BE-008 | Protecao margem | 2 |
| BE-010 | Ordens virtuais | 3 |
| BE-018 | Sistema filtros | 0 |
| BE-020 | Testes integracao | 0.5 |
| FE-001 | Dashboard banco | 0.5 |
| DEVOPS-001 | Dockerfile | 0 |
| DEVOPS-002 | docker-compose.stage | 0 |
| DEVOPS-002B | docker-compose.prod | 0 |
| DEVOPS-003 | GitHub repo | 0 |
| DEVOPS-004 | CI pipeline | 0 |
| DEVOPS-006 | GitHub Secrets | 0 |
| DEVOPS-007 | CD Stage pipeline | 1 |
| DEVOPS-007B | CD Prod pipeline | 1 |
| DEVOPS-008 | Stack Stage Portainer | 0 |
| DEVOPS-009 | Watchtower Stage | 1 |

### Prioridade Media (26 tarefas)
Melhorias e funcionalidades importantes mas nao criticas.

### Prioridade Baixa (14 tarefas)
Nice-to-have e funcionalidades avancadas.

---

## GitHub Actions Workflows

| Workflow | Arquivo | Trigger | Acao | Tag |
|----------|---------|---------|------|-----|
| CI | `ci.yml` | Push em qualquer branch | Lint, test, build | - |
| Integration | `integration.yml` | PR para main | Testes com PostgreSQL | - |
| CD Stage | `cd-stage.yml` | Merge em main (auto) | Build + push | `btcbot:stage` |
| CD Prod | `cd-prod.yml` | Manual (workflow_dispatch) | Retag stage -> latest | `btcbot:latest` |

---

## Secrets Necessarios no GitHub

| Secret | Descricao | Obrigatorio |
|--------|-----------|-------------|
| `DOCKER_REGISTRY` | URL do registry (ghcr.io, docker.io, etc) | Sim |
| `DOCKER_USERNAME` | Usuario do registry | Sim |
| `DOCKER_PASSWORD` | Token/senha do registry | Sim |
| `DISCORD_WEBHOOK` | Webhook para notificacoes | Nao |

---

## Caminho Critico

O caminho critico para ter o sistema basico funcionando:

1. **Sprint 0 (Infraestrutura)**
   - DEVOPS-016: Verificar Portainer e Watchtower no homeserver
   - DEVOPS-003: Criar repositorio GitHub
   - DEVOPS-001: Dockerfile com healthcheck
   - DB-001: PostgreSQL Docker
   - DEVOPS-002: docker-compose.stage.yml
   - DEVOPS-002B: docker-compose.prod.yml
   - DEVOPS-004: CI pipeline (GitHub Actions)
   - DEVOPS-006: Configurar GitHub Secrets (Registry)
   - DEVOPS-008: Criar stack Stage no Portainer
   - BE-018: Sistema de filtros plugaveis

2. **Sprint 0.5 (Persistencia)**
   - DEVOPS-005: Testes de integracao (GitHub Actions)
   - DB-002: Schema tabela trades
   - DB-011: Sistema de migrations
   - BE-001: TradeRepository
   - BE-002: Integrar persistencia no TP
   - BE-003: Carregar historico
   - FE-001: Dashboard com dados do banco

3. **Sprint 1 (Deploy Automatizado)**
   - DEVOPS-011: Healthcheck endpoint
   - DEVOPS-007: CD Stage pipeline (Build + Push)
   - DEVOPS-007B: CD Prod pipeline (Retag)
   - DEVOPS-009: Validar Watchtower Stage
   - BE-005: Preco ATH
   - BE-006: Contador hits

---

## Tarefas que Podem Rodar em Paralelo

### Sprint 0
```
Paralelo 1: DEVOPS-016 + DEVOPS-001 + DEVOPS-003
Paralelo 2: DEVOPS-002 + DEVOPS-002B + DEVOPS-014 + DB-001 (apos DEVOPS-001)
Paralelo 3: DEVOPS-004 + DEVOPS-006 (apos DEVOPS-003)
Paralelo 4: DEVOPS-008 + DEVOPS-015 (apos DEVOPS-002)
Paralelo 5: BE-018 (independente)
```

### Sprint 0.5
```
Equipe 1: DB-002, DB-009, DB-010, DB-011
Equipe 2: BE-001, BE-002, BE-003, BE-020
Equipe 3: FE-001, DEVOPS-005
```

### Sprint 1
```
Equipe 1: DB-005, DB-006
Equipe 2: BE-004, BE-005, BE-006
Equipe 3: FE-002, FE-009, FE-010, FE-011
Equipe 4: DEVOPS-011, DEVOPS-007, DEVOPS-007B, DEVOPS-009
```

### Sprint 2
```
Equipe 1: DB-007
Equipe 2: BE-007, BE-008, BE-009
Equipe 3: FE-003, FE-015
Equipe 4: DEVOPS-008B, DEVOPS-009B, DEVOPS-010, DEVOPS-017, DEVOPS-018
```

---

## Estimativa de Esforco

### Por Sprint (em dias de trabalho)

| Sprint | P | M | G | Dias Estimados |
|--------|---|---|---|----------------|
| 0 | 6 | 5 | 0 | 10 |
| 0.5 | 3 | 6 | 0 | 10.5 |
| 1 | 3 | 6 | 0 | 10.5 |
| 2 | 2 | 7 | 1 | 14.5 |
| 3 | 1 | 2 | 0 | 3.5 |
| 4 | 1 | 5 | 0 | 8 |
| 5 | 2 | 5 | 3 | 22 |

**Total Estimado: ~79 dias de trabalho**

### Legenda de Complexidade
- **P (Pequena):** ~0.5 dia
- **M (Media):** ~1.5 dias
- **G (Grande):** ~4 dias

---

## Atualizacao do PROGRESS.md (Para Agentes)

O arquivo `PROGRESS.md` e o ponto central de acompanhamento do projeto. **Todo agente que trabalhar em uma task DEVE atualizar este arquivo.**

### Quando Atualizar

| Momento | Acao |
|---------|------|
| Iniciar task | Mudar status para `🔄 IN_PROGRESS` |
| Enviar para review | Mudar status para `👀 REVIEW` |
| Iniciar testes | Mudar status para `🧪 ACCEPTANCE_TESTING` |
| Bug encontrado | Mudar status para `🐛 BLOCKED_BY_BUG` |
| Aprovado para prod | Mudar status para `✅ READY_TO_PROD` |
| Concluir task | Mudar status para `✔️ DONE` |

### Secoes a Atualizar

#### 1. Resumo Executivo (Topo do arquivo)
```markdown
| Metrica | Valor |
|---------|-------|
| **Total de Tasks** | 66 |
| **Concluidas (DONE)** | X |      <-- Incrementar quando DONE
| **Em Progresso** | Y |            <-- Ajustar conforme status
| **Pendentes (TODO)** | Z |        <-- Decrementar quando sair de TODO
| **Progresso Geral** | X.X% |      <-- Calcular: (DONE / Total) * 100
```

#### 2. Tabela do Sprint Correspondente
Localizar a task na tabela do sprint e atualizar o status:
```markdown
| DEVOPS-003 | DevOps | Repositorio GitHub | ✔️ DONE | Claude |
```

**Icones de Status:**
- `⬜ TODO`
- `🔄 IN_PROGRESS`
- `👀 REVIEW`
- `🧪 ACCEPTANCE_TESTING`
- `🐛 BLOCKED_BY_BUG`
- `✅ READY_TO_PROD`
- `✔️ DONE`

#### 3. Progresso do Sprint
Atualizar o contador no inicio da secao do sprint:
```markdown
**Progresso:** 1/14 (7%)   <-- Incrementar quando task for DONE
```

#### 4. Progresso por Area
Atualizar a tabela de progresso por area (DevOps, Database, Backend, Frontend):
```markdown
| Area | Total | Done | Em Progresso | Pendente | % |
|------|-------|------|--------------|----------|---|
| DevOps | 20 | 1 | 0 | 19 | 5% |
```

#### 5. Historico de Atualizacoes
Adicionar entrada no topo da tabela:
```markdown
| Data | Descricao |
|------|-----------|
| DD/MM/YYYY | TASK-ID concluida - Descricao breve |
```

### Arquivos a Atualizar (Sempre em Par)

Ao mudar status de uma task, atualizar **AMBOS** os arquivos:

1. **`tasks/PROGRESS.md`** - Visao consolidada
2. **`tasks/tasks_<area>.md`** - Arquivo detalhado da area (devops, database, backend, frontend)

### Exemplo Completo de Atualizacao

Ao marcar `DEVOPS-004` como `IN_PROGRESS`:

**1. Em `tasks/tasks_devops.md`:**
```markdown
| DEVOPS-004 | GitHub Actions - CI | IN_PROGRESS | Claude |
```

**2. Em `tasks/PROGRESS.md`:**
- Resumo Executivo: `Em Progresso: 0 -> 1`
- Sprint 0: `| DEVOPS-004 | DevOps | GitHub Actions - CI | 🔄 IN_PROGRESS | Claude |`

### Commits de Atualizacao

Ao atualizar status, usar formato:
```
docs: Update TASK-ID status to STATUS

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Branch Protection

Se a branch `main` estiver protegida:
1. Criar branch: `docs/task-id-status`
2. Fazer commit
3. Criar PR
4. Merge (ou solicitar review se necessario)

---

## Fluxo de Desenvolvimento

> **Documentacao completa:** [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md)

### Estados das Tasks

```
TODO -> IN_PROGRESS -> REVIEW -> ACCEPTANCE_TESTING -> READY_TO_PROD -> DONE
                                        |
                                   (Se bug encontrado)
                                        |
                                        v
                               +------------------+
                               | BLOCKED_BY_BUG   |
                               +--------+---------+
                                        |
                                        v
                               Criar task em tasks_bugfixes.md
                                        |
                                        | Dev corrige bugfix
                                        v
                               Bugfix DONE -> Task desbloqueada
                                        |
                                        v
                               ACCEPTANCE_TESTING (reteste)
```

### Resumo do Fluxo

```
1. Dev pega task TODO, move para IN_PROGRESS
2. Cria branch feature/TASK_ID-descricao a partir de main
3. Desenvolve e faz push do PR
4. Move task para REVIEW
5. Reviewer faz code review
   - Sugere mudancas ou aprova
6. Dev resolve comentarios
7. Reviewer aprova PR
8. Dev faz merge para main
   -> CD Stage automatico: build + push btcbot:stage
   -> Watchtower Stage atualiza container
9. Move task para ACCEPTANCE_TESTING
10. Tester valida em Stage (porta 3001)
    - Se bugs:
      a. Move task para BLOCKED_BY_BUG
      b. Cria task em tasks_bugfixes.md
      c. Dev corrige bugfix (branch -> PR -> review -> merge)
      d. Bugfix vai para DONE
      e. Task original volta para ACCEPTANCE_TESTING
      f. Tester retesta
    - Se OK: move para READY_TO_PROD
11. Dev executa CD Prod manualmente
    -> Retag btcbot:stage -> btcbot:latest
    -> Watchtower Prod atualiza container
12. Move task para DONE
```

### Convencao de Branches

| Tipo | Padrao | Exemplo |
|------|--------|---------|
| Feature | `feature/<TASK_ID>-<descricao>` | `feature/BE-001-trade-repository` |
| Bugfix | `bugfix/<BUG_ID>-<descricao>` | `bugfix/BUG-001-fix-pnl-calc` |
| Hotfix | `hotfix/<TASK_ID>-<descricao>` | `hotfix/BE-001-validacao` |

### Papeis

- **Dev:** Implementa, responde review, faz merge e deploy
- **Reviewer:** Revisa codigo, sugere melhorias, aprova PRs (via comentario + label)
- **Tester:** Valida em Stage, **cria bugs em tasks_bugfixes.md**, **bloqueia task original**, aprova para producao

### Review com Agentes

Para projetos com agentes de IA usando a mesma conta GitHub:

1. **Agente Implementador** cria o PR
2. **Agente Revisor** (mesma disciplina, agente diferente) revisa via comentario
3. Se aprovado: Revisor adiciona label `approved`
4. **Agente Implementador** faz merge apos ver label `approved`

> Ver detalhes em [BRANCH_PROTECTION.md](/docs/BRANCH_PROTECTION.md) e [GITFLOW.md](/docs/GITFLOW.md)

---

## Processo de Bugfix

Quando o Tester encontra um bug durante Acceptance Testing:

1. **Tester bloqueia task original e cria bugfix**
   - Move task original para `BLOCKED_BY_BUG`
   - Cria task em `/tasks/tasks_bugfixes.md`
   - Usa o template do arquivo
   - Atribui ID sequencial (BUG-001, BUG-002, etc)
   - Define severidade (Critica, Alta, Media, Baixa)
   - Referencia a task original

2. **Dev corrige o bug**
   - Cria branch `bugfix/BUG-XXX-descricao`
   - Abre PR, passa por code review
   - Merge -> CD Stage automatico

3. **Tester retesta bugfix em Stage**
   - Se OK: bugfix vai para DONE
   - Task original e **DESBLOQUEADA** (volta para `ACCEPTANCE_TESTING`)
   - Tester retesta task original
   - Se OK: task original vai para `READY_TO_PROD`

**IMPORTANTE:** A task original fica **BLOQUEADA** ate que todos os bugfixes relacionados sejam resolvidos.

Ver detalhes em: [tasks_bugfixes.md](tasks_bugfixes.md)

---

## Proximos Passos Recomendados

1. **Imediato (Sprint 0)**
   - Verificar Portainer e Watchtower no homeserver
   - Criar repositorio GitHub com estrutura
   - Configurar GitHub Secrets para Registry
   - Implementar CI basico
   - Criar Dockerfile com healthcheck
   - Criar docker-compose.stage.yml e docker-compose.prod.yml
   - Criar stacks no Portainer

2. **Curto Prazo (Sprint 0.5)**
   - Implementar persistencia em PostgreSQL
   - Testes de integracao no CI
   - Integrar banco com o bot existente

3. **Medio Prazo (Sprint 1)**
   - CD Stage pipeline (build + push)
   - CD Prod pipeline (retag)
   - Testar fluxo completo com Watchtower
   - Healthcheck endpoint
   - Documentacao de operacao

---

## Riscos Identificados

| Risco | Mitigacao |
|-------|-----------|
| Watchtower nao detecta imagem | Verificar labels, testar manualmente |
| Homeserver offline | Monitoramento via Portainer, alertas |
| Registry indisponivel | Usar registry confiavel (GHCR, Docker Hub) |
| Secrets expostos | GitHub Secrets, detect-secrets no pre-commit |
| Complexidade do sistema de filtros | Spike tecnico antes de comecar |
| Performance do banco com muitos trades | Testes de carga no Sprint 0.5 |
| Bug em producao | Rollback via Portainer ou re-tag |

---

## Clarificacoes Necessarias

Antes de iniciar algumas tarefas, seria util clarificar:

1. **RF08 (Persistencia):** Qual o user_id a ser usado? UUID gerado ou identificador externo?
2. **RF12 (Ordens virtuais):** Limite maximo de ordens virtuais simultaneas?
3. **RF13 (Protecao margem):** De onde vem a margem adicional? Saldo da conta?
4. **RF21 (Interface Web):** Prioridade real? Framework preferido?
5. **Docker Registry:** Docker Hub, GHCR ou registry privado?

---

## Checklist de Seguranca

- [ ] Tokens do registry com escopo minimo necessario
- [ ] Secrets nunca em codigo ou logs
- [ ] Imagem Docker com usuario nao-root
- [ ] Redes Docker separadas (stage-network e prod-network)
- [ ] Portas expostas: 3000 (prod), 3001 (stage)
- [ ] Backup criptografado (opcional)
- [ ] Logs sem informacoes sensiveis
- [ ] Acesso ao Portainer protegido
- [ ] detect-secrets no pre-commit
- [ ] Credenciais de producao NUNCA em Stage

---

## Operacao via Portainer

### Visualizar Status
1. Acessar Portainer UI
2. Ir em Stacks -> btcbot-stage ou btcbot-prod
3. Ver status dos containers

### Ver Logs
1. Clicar no container (btcbot-stage ou btcbot-prod)
2. Ir em Logs
3. Acompanhar em tempo real

### Rollback Manual
1. Ir em Images
2. Encontrar imagem anterior (por SHA)
3. Ir em Containers -> btcbot-* -> Duplicate/Edit
4. Alterar tag da imagem para versao anterior
5. Deploy

> **Procedimento completo de rollback:** Ver [GitFlow - Rollback](/docs/GITFLOW.md#rollback)

### Restart
1. Clicar no container
2. Clicar em Restart

---

## Documentacao

| Documento | Descricao |
|-----------|-----------|
| [GitFlow](/docs/GITFLOW.md) | Fluxo de trabalho, code review, estados das tasks, deploy |
| [PRD](/PRD.md) | Documento de requisitos do produto |
| `tasks_*.md` | Tarefas decompostas por especialidade |
| `tasks_bugfixes.md` | Bugs encontrados durante Acceptance Testing (task original fica BLOCKED_BY_BUG) |

---

*Documentacao atualizada em 26/12/2025 - Versao 1.5 (Instrucoes para atualizacao do PROGRESS.md)*
