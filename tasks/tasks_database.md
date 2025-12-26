# Tarefas de Banco de Dados - BTC Grid Bot

**Data:** 22 de Dezembro de 2025
**Versao:** 1.0

---

## Resumo

Este documento contém todas as tarefas relacionadas a banco de dados, incluindo schema, migrations, queries e configuracoes do PostgreSQL.

---

## Legenda

- **Complexidade:** P (Pequena ~0.5 dia), M (Media ~1-2 dias), G (Grande ~3-5 dias)
- **Prioridade:** Alta, Media, Baixa
- **Status:** Pendente, Em Progresso, Concluido

---

## Tarefas

### DB-001: Configurar PostgreSQL com Docker Compose

**Descricao:**
Criar arquivo docker-compose.yml com servico PostgreSQL 15+ configurado para desenvolvimento local. Incluir volume persistente para dados e configuracoes de rede.

**Criterios de Aceite:**
- [ ] Arquivo `docker-compose.yml` criado na raiz do projeto
- [ ] PostgreSQL 15+ configurado como servico
- [ ] Volume persistente para dados (`pgdata`)
- [ ] Porta 5432 exposta para conexao local
- [ ] Variaveis de ambiente para POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- [ ] Healthcheck configurado para garantir que o banco esta pronto
- [ ] Comando `docker-compose up -d` inicia o banco sem erros

**Dependencias:** Nenhuma

**Paralelo com:** DEVOPS-001, DEVOPS-002

**Complexidade:** P

**Sprint:** 0

**Prioridade:** Alta

---

### DB-002: Criar schema inicial da tabela trades

**Descricao:**
Criar script SQL de migration para a tabela `trades` conforme especificado no PRD (secao 6.3). Incluir todos os campos necessarios, indices e constraints.

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/001_create_trades_table.sql`
- [ ] Tabela `trades` com todos os campos:
  - id (UUID, PK, auto-gerado)
  - user_id (VARCHAR 100, NOT NULL)
  - account_type (VARCHAR 10, DEFAULT 'demo')
  - symbol (VARCHAR 20, DEFAULT 'BTC-USDT')
  - side (VARCHAR 10, DEFAULT 'LONG')
  - entry_price (DECIMAL 20,8, NOT NULL)
  - exit_price (DECIMAL 20,8, NOT NULL)
  - quantity (DECIMAL 20,8, NOT NULL)
  - pnl (DECIMAL 20,8, NOT NULL)
  - pnl_percent (DECIMAL 10,4, NOT NULL)
  - grid_level (INTEGER, nullable)
  - entry_at (TIMESTAMPTZ, NOT NULL)
  - closed_at (TIMESTAMPTZ, NOT NULL)
  - created_at (TIMESTAMPTZ, DEFAULT NOW())
- [ ] Indice `idx_trades_user` em user_id
- [ ] Indice `idx_trades_user_closed` em (user_id, closed_at DESC)
- [ ] Indice `idx_trades_user_account` em (user_id, account_type)
- [ ] Script executa sem erros no PostgreSQL

**Dependencias:** DB-001

**Paralelo com:** BE-001

**Complexidade:** P

**Sprint:** 0.5

**Prioridade:** Alta

---

### DB-003: Criar tabela de configuracoes de usuario

**Descricao:**
Criar tabela para armazenar configuracoes persistentes de cada usuario (estrategias salvas - RF22). Permite salvar e alternar entre diferentes configuracoes de trading.

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/002_create_user_configs_table.sql`
- [ ] Tabela `user_configs` com campos:
  - id (UUID, PK)
  - user_id (VARCHAR 100, NOT NULL)
  - name (VARCHAR 100, NOT NULL) - nome da configuracao
  - config_json (JSONB, NOT NULL) - configuracoes serializadas
  - is_active (BOOLEAN, DEFAULT false)
  - created_at (TIMESTAMPTZ)
  - updated_at (TIMESTAMPTZ)
- [ ] Constraint UNIQUE em (user_id, name)
- [ ] Indice em user_id

**Dependencias:** DB-002

**Paralelo com:** DB-004

**Complexidade:** P

**Sprint:** 5

**Prioridade:** Baixa

---

### DB-004: Criar tabela de historico de ordens virtuais

**Descricao:**
Criar tabela para armazenar ordens virtuais (gatilhos - RF12). Ordens que nao vao para exchange ate o preco bater no nivel.

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/003_create_virtual_orders_table.sql`
- [ ] Tabela `virtual_orders` com campos:
  - id (UUID, PK)
  - user_id (VARCHAR 100, NOT NULL)
  - account_type (VARCHAR 10)
  - symbol (VARCHAR 20)
  - trigger_price (DECIMAL 20,8, NOT NULL)
  - quantity (DECIMAL 20,8, NOT NULL)
  - tp_percent (DECIMAL 10,4)
  - grid_level (INTEGER)
  - status (VARCHAR 20) - WAITING, TRIGGERED, CANCELLED
  - created_at (TIMESTAMPTZ)
  - triggered_at (TIMESTAMPTZ, nullable)
  - exchange_order_id (VARCHAR 100, nullable)
- [ ] Indice em (user_id, status)
- [ ] Indice em trigger_price para busca eficiente

**Dependencias:** DB-002

**Paralelo com:** DB-003

**Complexidade:** M

**Sprint:** 3

**Prioridade:** Alta

---

### DB-005: Criar tabela de contagem de hits por nivel

**Descricao:**
Criar tabela para rastrear quantas vezes cada faixa/nivel do grid gerou lucro (RF11).

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/004_create_grid_level_stats_table.sql`
- [ ] Tabela `grid_level_stats` com campos:
  - id (UUID, PK)
  - user_id (VARCHAR 100, NOT NULL)
  - account_type (VARCHAR 10)
  - grid_level (INTEGER, NOT NULL)
  - price_range_start (DECIMAL 20,8)
  - price_range_end (DECIMAL 20,8)
  - hit_count (INTEGER, DEFAULT 0)
  - total_pnl (DECIMAL 20,8, DEFAULT 0)
  - avg_pnl (DECIMAL 20,8, DEFAULT 0)
  - last_hit_at (TIMESTAMPTZ)
  - updated_at (TIMESTAMPTZ)
- [ ] Constraint UNIQUE em (user_id, account_type, grid_level)
- [ ] Indice em user_id

**Dependencias:** DB-002

**Paralelo com:** DB-003, DB-004

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Alta

---

### DB-006: Criar tabela de historico de ATH (All Time High)

**Descricao:**
Criar tabela para armazenar historico de ATH por simbolo, usado para calcular preco inicial (RF10).

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/005_create_ath_history_table.sql`
- [ ] Tabela `ath_history` com campos:
  - id (UUID, PK)
  - symbol (VARCHAR 20, NOT NULL)
  - ath_price (DECIMAL 20,8, NOT NULL)
  - recorded_at (TIMESTAMPTZ, NOT NULL)
  - source (VARCHAR 50) - origem do dado (API, manual)
- [ ] Indice em (symbol, recorded_at DESC)
- [ ] Constraint UNIQUE em (symbol, recorded_at)

**Dependencias:** DB-002

**Paralelo com:** DB-003, DB-004, DB-005

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Alta

---

### DB-007: Criar tabela de logs de protecao de margem

**Descricao:**
Criar tabela para registrar eventos de injecao automatica de margem (RF13).

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/006_create_margin_events_table.sql`
- [ ] Tabela `margin_events` com campos:
  - id (UUID, PK)
  - user_id (VARCHAR 100, NOT NULL)
  - account_type (VARCHAR 10)
  - event_type (VARCHAR 20) - INJECTION, WARNING, LIQUIDATION_CLOSE
  - margin_before (DECIMAL 20,8)
  - margin_after (DECIMAL 20,8)
  - amount_injected (DECIMAL 20,8)
  - liquidation_price (DECIMAL 20,8)
  - current_price (DECIMAL 20,8)
  - created_at (TIMESTAMPTZ)
- [ ] Indice em (user_id, created_at DESC)

**Dependencias:** DB-002

**Paralelo com:** DB-003, DB-004, DB-005, DB-006

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Alta

---

### DB-008: Criar tabela de resultados de backtest

**Descricao:**
Criar tabela para armazenar resultados de backtests de estrategias (RF23).

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/007_create_backtest_results_table.sql`
- [ ] Tabela `backtest_results` com campos:
  - id (UUID, PK)
  - user_id (VARCHAR 100, NOT NULL)
  - strategy_name (VARCHAR 100)
  - config_json (JSONB) - parametros usados
  - start_date (DATE, NOT NULL)
  - end_date (DATE, NOT NULL)
  - initial_balance (DECIMAL 20,8)
  - final_balance (DECIMAL 20,8)
  - total_trades (INTEGER)
  - win_rate (DECIMAL 10,4)
  - max_drawdown (DECIMAL 10,4)
  - sharpe_ratio (DECIMAL 10,4)
  - trades_json (JSONB) - lista de trades simulados
  - created_at (TIMESTAMPTZ)
- [ ] Indice em (user_id, created_at DESC)

**Dependencias:** DB-002

**Paralelo com:** Nenhuma (depende de outras funcionalidades)

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Baixa

---

### DB-009: Criar queries de agregacao de estatisticas

**Descricao:**
Criar arquivo SQL com queries otimizadas para agregacoes e relatorios (PnL total, win rate, media por trade).

**Criterios de Aceite:**
- [ ] Arquivo `src/database/queries/stats_queries.sql`
- [ ] Query: Estatisticas gerais do usuario (total_trades, wins, win_rate, total_pnl, avg_pnl)
- [ ] Query: Trades por periodo com filtro de data
- [ ] Query: PnL por dia (ultimos 30 dias)
- [ ] Query: Performance por grid_level
- [ ] Query: Comparacao demo vs live
- [ ] Todas queries executam em < 200ms para 10k registros
- [ ] Queries usam os indices criados

**Dependencias:** DB-002, DB-005

**Paralelo com:** BE-002

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### DB-010: Implementar Row-Level Security (RLS)

**Descricao:**
Configurar RLS no PostgreSQL para isolamento de dados multi-tenant (RF08.4).

**Criterios de Aceite:**
- [ ] Script SQL em `migrations/008_enable_rls.sql`
- [ ] RLS habilitado na tabela `trades`
- [ ] Policy para SELECT: usuario so ve seus trades
- [ ] Policy para INSERT: usuario so insere com seu user_id
- [ ] Policy para UPDATE: usuario so atualiza seus trades
- [ ] Policy para DELETE: usuario so deleta seus trades
- [ ] Testes comprovam isolamento entre usuarios

**Dependencias:** DB-002

**Paralelo com:** DB-009

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### DB-011: Criar sistema de migrations automatizado

**Descricao:**
Implementar sistema para executar migrations automaticamente na ordem correta.

**Criterios de Aceite:**
- [ ] Tabela `schema_migrations` para controle de versao
- [ ] Script Python `run_migrations.py` que:
  - Lista migrations pendentes
  - Executa em ordem numerica
  - Registra migrations executadas
  - Suporta rollback (down migrations)
- [ ] Migrations sao idempotentes (IF NOT EXISTS)
- [ ] Log de migrations executadas

**Dependencias:** DB-001, DB-002

**Paralelo com:** BE-001

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

## Grafico de Dependencias

```
DB-001 (PostgreSQL Docker)
    |
    v
DB-002 (Schema trades)
    |
    +---> DB-003 (User configs) [Sprint 5]
    |
    +---> DB-004 (Virtual orders) [Sprint 3]
    |
    +---> DB-005 (Grid level stats) [Sprint 1]
    |
    +---> DB-006 (ATH history) [Sprint 1]
    |
    +---> DB-007 (Margin events) [Sprint 2]
    |
    +---> DB-008 (Backtest results) [Sprint 5]
    |
    +---> DB-009 (Queries agregacao)
    |
    +---> DB-010 (RLS)
    |
    +---> DB-011 (Sistema migrations)
```

---

## Ordem de Implementacao Sugerida

### Sprint 0
1. DB-001 - PostgreSQL Docker Compose

### Sprint 0.5
2. DB-002 - Schema tabela trades
3. DB-011 - Sistema de migrations
4. DB-009 - Queries de agregacao
5. DB-010 - Row-Level Security

### Sprint 1
6. DB-005 - Contagem de hits por nivel
7. DB-006 - Historico de ATH

### Sprint 2
8. DB-007 - Logs de protecao de margem

### Sprint 3
9. DB-004 - Ordens virtuais

### Sprint 5
10. DB-003 - Configuracoes de usuario
11. DB-008 - Resultados de backtest

---

## Consideracoes Tecnicas

### Pool de Conexoes
- Usar asyncpg com pool de conexoes (DB_POOL_SIZE = 5 por padrao)
- Conexoes sao reutilizadas para performance

### Backup
- Configurar pg_dump automatico em producao
- Retencao de 30 dias de backups

### Monitoramento
- Queries lentas devem ser logadas (pg_stat_statements)
- Alertas para conexoes proximas do limite

---

*Documento gerado em 22/12/2025*
