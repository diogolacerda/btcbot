# Tarefas de Bugfix - BTC Grid Bot

**Data:** 26 de Dezembro de 2025
**Versao:** 1.2

---

## Controle de Progresso

### Legenda de Status (Bugfixes)
| Status | Descricao |
|--------|-----------|
| `TODO` | Bug reportado, aguardando dev |
| `IN_PROGRESS` | Dev trabalhando na correcao |
| `REVIEW` | Aguardando code review |
| `DONE` | Corrigido e testado |

### Bugs Ativos
| Bug ID | Descricao | Severidade | Status | Responsavel |
|--------|-----------|------------|--------|-------------|
| *Nenhum bug ativo* | - | - | - | - |

---

## Sobre Este Arquivo

Este arquivo contem bugs encontrados durante o **Acceptance Testing** em Stage. Quando o Tester encontra um bug, ele deve criar uma nova task neste arquivo seguindo o template abaixo.

**IMPORTANTE:** A task original fica **BLOQUEADA** ate que todos os bugfixes relacionados sejam resolvidos.

**Fluxo de Bugfix:**
```
1. Tester encontra bug em Stage (task em ACCEPTANCE_TESTING)
2. Tester cria task de bugfix NESTE ARQUIVO
3. Task original fica BLOQUEADA (status: BLOCKED_BY_BUG)
4. Dev pega task de bugfix, move para IN_PROGRESS
5. Dev cria branch bugfix/BUG-XXX-descricao
6. Dev corrige, abre PR
7. Reviewer faz code review
8. Merge -> CD Stage automatico
9. Tester retesta em Stage
10. Se OK: bugfix vai para DONE
11. Task original e DESBLOQUEADA e volta para ACCEPTANCE_TESTING
12. Tester retesta task original
13. Se OK: task original vai para READY_TO_PROD
```

**Documentacao Relacionada:**
- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md) - Processo completo de bugfix
- [Tasks de DevOps](/tasks/tasks_devops.md) - Infraestrutura e deploy

---

## Legenda

- **Severidade:** Critica, Alta, Media, Baixa
- **Complexidade:** P (Pequena ~0.5 dia), M (Media ~1-2 dias), G (Grande ~3-5 dias)
- **Status:** TODO, IN_PROGRESS, REVIEW, DONE

---

## Template para Novo Bugfix

Copie o template abaixo para criar uma nova task de bugfix:

```markdown
### BUG-XXX: [Titulo descritivo do bug]

**Data:** DD/MM/YYYY
**Reportado por:** [Nome do Tester]
**Task Original:** [ID da task que estava sendo testada, ex: BE-001]
**Task Original Status:** BLOCKED_BY_BUG
**Ambiente:** Stage (porta 3001)
**Severidade:** [Critica/Alta/Media/Baixa]
**Sprint:** [Numero do sprint atual]

**Descricao do Bug:**
[Descreva o que aconteceu de errado]

**Comportamento Esperado:**
[Descreva o que deveria acontecer]

**Comportamento Atual:**
[Descreva o que esta acontecendo de errado]

**Passos para Reproduzir:**
1. [Passo 1]
2. [Passo 2]
3. [Passo 3]
4. Bug aparece

**Evidencias:**
- [Screenshot, log, video - se aplicavel]
- [Link para logs do container, se aplicavel]

**Criterios de Aceite:**
- [ ] Bug corrigido
- [ ] Teste de regressao adicionado
- [ ] Comportamento esperado funciona
- [ ] Nao introduz novos bugs

**Dependencias:** Nenhuma

**Complexidade:** [P/M/G]

**Status:** TODO

---
```

---

## Bugs Ativos

*Nenhum bug ativo no momento.*

<!-- Exemplo de bug ativo:

### BUG-001: Calculo de PnL incorreto quando trade e parcialmente fechado

**Data:** 22/12/2025
**Reportado por:** Tester
**Task Original:** BE-002
**Task Original Status:** BLOCKED_BY_BUG
**Ambiente:** Stage (porta 3001)
**Severidade:** Alta
**Sprint:** 1

**Descricao do Bug:**
O calculo de PnL esta incorreto quando um trade e parcialmente fechado.

**Comportamento Esperado:**
PnL deve ser calculado proporcionalmente a quantidade fechada.

**Comportamento Atual:**
PnL esta sendo calculado como se o trade inteiro fosse fechado.

**Passos para Reproduzir:**
1. Abrir posicao de 0.01 BTC
2. Fechar parcialmente (0.005 BTC)
3. Verificar PnL no dashboard
4. PnL mostra valor incorreto

**Evidencias:**
- Screenshot do dashboard mostrando PnL errado
- Log: `2025-12-22 10:30:00 - PnL calculated: $50.00 (should be $25.00)`

**Criterios de Aceite:**
- [ ] Bug corrigido
- [ ] Teste de regressao adicionado
- [ ] Comportamento esperado funciona
- [ ] Nao introduz novos bugs

**Dependencias:** Nenhuma

**Complexidade:** M

**Status:** IN_PROGRESS

---

-->

---

## Bugs Resolvidos

### BUG-001: Ordens nao criadas na BingX apesar de log indicar sucesso

**Resolvido em:** 26/12/2025
**Resolvido por:** staff-backend-dev
**Task Original:** DEVOPS-002
**Tempo de resolucao:** < 1 hora

**Causa Raiz:**
1. Log de sucesso era escrito ANTES de verificar resposta da API
2. Dashboard nao validava dados antes de calculos (overflow)
3. WebSocket sem timeout adequado

**Correcoes Aplicadas:**
- `src/client/bingx_client.py` - Validacao de orderId antes de logar sucesso
- `src/ui/dashboard.py` - Protecao contra overflow em calculos
- `src/client/websocket_client.py` - Timeout e reconexao melhorados

<!-- Exemplo de bug resolvido:

### BUG-000: [Titulo do bug resolvido]

**Resolvido em:** DD/MM/YYYY
**Resolvido por:** [Nome do Dev]
**Task Original:** [ID]
**PR:** #XXX
**Tempo de resolucao:** X dias

---

-->

---

## Estatisticas

| Metrica | Valor |
|---------|-------|
| Total de bugs reportados | 1 |
| Bugs ativos | 0 |
| Bugs resolvidos | 1 |
| Tempo medio de resolucao | < 1 hora |

---

## Processo Detalhado

### 1. Tester Encontra Bug

Durante o Acceptance Testing em Stage (porta 3001), o Tester encontra um comportamento inesperado.

**Acoes do Tester:**
1. Documentar o bug com evidencias (screenshots, logs)
2. Criar nova task neste arquivo usando o template
3. Atribuir ID sequencial (BUG-001, BUG-002, etc)
4. Definir severidade:
   - **Critica:** Sistema inutilizavel, perda de dados, afeta trading
   - **Alta:** Funcionalidade principal nao funciona
   - **Media:** Funcionalidade secundaria com problemas
   - **Baixa:** Problema estetico ou menor
5. **IMPORTANTE:** Marcar a task original como `BLOCKED_BY_BUG`
6. Notificar o Dev responsavel pela task original

### 2. Task Original Fica Bloqueada

Enquanto houver bugfixes abertos relacionados a uma task:

- Task original tem status: `BLOCKED_BY_BUG`
- Task original NAO pode ir para `READY_TO_PROD`
- Task original NAO pode ir para `DONE`
- Apenas quando TODOS os bugfixes forem resolvidos, a task e desbloqueada

**Estados validos para task bloqueada:**
```
ACCEPTANCE_TESTING --> BLOCKED_BY_BUG --> ACCEPTANCE_TESTING --> READY_TO_PROD
                             ^                    |
                             |                    |
                        (bugfix criado)    (bugfix resolvido)
```

### 3. Dev Corrige o Bug

**Acoes do Dev:**
1. Mover task de bugfix para `IN_PROGRESS`
2. Criar branch a partir de main:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b bugfix/BUG-001-descricao-curta
   ```
3. Implementar correcao
4. Adicionar teste de regressao (OBRIGATORIO)
5. Abrir PR para main usando template de bugfix
6. Mover task para `REVIEW`

### 4. Code Review

**Acoes do Reviewer:**
1. Verificar se correcao resolve o bug
2. Verificar se teste de regressao esta adequado
3. Verificar se nao introduz novos problemas
4. Aprovar ou solicitar mudancas

**Prioridade:** Bugfixes tem prioridade no code review sobre features.

### 5. Merge e Reteste

**Apos merge:**
1. CD Stage automatico faz build e push de `btcbot:stage`
2. Watchtower atualiza container em Stage (porta 3001)
3. Tester retesta o cenario do bug
4. Se corrigido:
   - Mover bugfix para `DONE`
   - Mover para secao "Bugs Resolvidos"
   - **DESBLOQUEAR task original** (voltar para `ACCEPTANCE_TESTING`)
5. Tester retesta task original
6. Se OK: task original vai para `READY_TO_PROD`

### 6. Promocao para Production

Quando a task original for promovida para Production (CD Prod manual):
- Bugfixes ja estao incluidos (mesma imagem `btcbot:stage` -> `btcbot:latest`)
- Todos os bugfixes relacionados devem estar em `DONE`

---

## Severidade e SLA

| Severidade | Descricao | SLA de Resolucao |
|------------|-----------|------------------|
| **Critica** | Sistema inutilizavel, perda de dados, afeta trading | 4 horas |
| **Alta** | Funcionalidade principal nao funciona | 1 dia |
| **Media** | Funcionalidade secundaria com problemas | 3 dias |
| **Baixa** | Problema estetico ou menor | 1 semana |

---

## Boas Praticas

1. **Descricao Clara:** Quanto mais detalhes, mais rapido o Dev consegue corrigir
2. **Evidencias:** Screenshots e logs ajudam muito
3. **Passos para Reproduzir:** Devem ser precisos e reproduziveis
4. **Teste de Regressao:** Todo bugfix DEVE ter teste automatizado
5. **Comunicacao:** Notificar o Dev responsavel imediatamente
6. **Prioridade:** Bugs criticos tem prioridade sobre features
7. **Bloqueio:** Sempre marcar a task original como BLOCKED_BY_BUG

---

## Nomenclatura de Branches

| Tipo | Padrao | Exemplo |
|------|--------|---------|
| Bugfix | `bugfix/BUG-XXX-<descricao>` | `bugfix/BUG-001-fix-pnl-calculation` |

---

## Checklist para Tester

Antes de criar um bugfix, verifique:

- [ ] O bug e reproduzivel?
- [ ] O bug nao e um problema de configuracao?
- [ ] O bug acontece em Stage (porta 3001)?
- [ ] O comportamento esperado esta claro?
- [ ] Tenho evidencias suficientes?
- [ ] Defini a severidade corretamente?
- [ ] Referenciei a task original?
- [ ] Marquei a task original como BLOCKED_BY_BUG?

---

## Referencias

- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md)
- [Tasks de DevOps](/tasks/tasks_devops.md)
- [Tasks de Backend](/tasks/tasks_backend.md)
- [Tasks de Frontend](/tasks/tasks_frontend.md)
- [Tasks de Database](/tasks/tasks_database.md)
- [README das Tasks](/tasks/README.md)

---

*Documento atualizado em 26/12/2025 - Versao 1.2 (Adicionado tabela de controle de progresso)*
