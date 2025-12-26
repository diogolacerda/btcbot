# Tarefas de Backend - BTC Grid Bot

**Data:** 26 de Dezembro de 2025
**Versao:** 1.1

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

### Sprint 0
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-018 | Sistema de filtros plugaveis | TODO | - |

### Sprint 0.5
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-001 | TradeRepository | TODO | - |
| BE-002 | Integracao persistencia TP | TODO | - |
| BE-003 | Carregar historico startup | TODO | - |
| BE-020 | Testes integracao banco | TODO | - |

### Sprint 1
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-004 | Confirmacao 2 velas | TODO | - |
| BE-005 | Preco inicial ATH | TODO | - |
| BE-006 | Contador hits nivel | TODO | - |

### Sprint 2
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-007 | TP dinamico | TODO | - |
| BE-008 | Protecao margem | TODO | - |
| BE-009 | Pausa tendencia baixa | TODO | - |

### Sprint 3
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-010 | Ordens virtuais | TODO | - |

### Sprint 4
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-011 | RSI | TODO | - |
| BE-012 | Bollinger | TODO | - |
| BE-013 | MA Cross | TODO | - |
| BE-019 | Multi-pares | TODO | - |

### Sprint 5
| Task | Descricao | Status | Responsavel |
|------|-----------|--------|-------------|
| BE-014 | Long + Short | TODO | - |
| BE-015 | Estrategias customizadas | TODO | - |
| BE-016 | Backtest | TODO | - |
| BE-017 | Trailing stop | TODO | - |

---

## Resumo

Este documento contém todas as tarefas de backend Python, incluindo API, logica de negocio, integracoes com exchange e implementacao de indicadores tecnicos.

---

## Legenda

- **Complexidade:** P (Pequena ~0.5 dia), M (Media ~1-2 dias), G (Grande ~3-5 dias)
- **Prioridade:** Alta, Media, Baixa

---

## Tarefas

### BE-001: Implementar camada de repositorio (TradeRepository)

**Status:** TODO

**Descricao:**
Criar classe TradeRepository com asyncpg para persistir e consultar trades no PostgreSQL. Seguir padrao Repository para isolamento da camada de dados.

**Criterios de Aceite:**
- [ ] Classe `TradeRepository` em `src/database/trade_repository.py`
- [ ] Metodo `save_trade(trade: TradeRecord) -> UUID` - salva trade, retorna ID
- [ ] Metodo `get_trades_by_user(user_id, limit, offset) -> List[Trade]`
- [ ] Metodo `get_trades_by_period(user_id, start, end) -> List[Trade]`
- [ ] Metodo `get_stats(user_id) -> UserStats` - retorna agregacoes
- [ ] Metodo `get_stats_by_level(user_id) -> List[LevelStats]`
- [ ] Conexao via pool asyncpg (configuravel via DATABASE_URL)
- [ ] Trade salvo em < 100ms (RNF de performance)
- [ ] Queries com filtro de data em < 200ms
- [ ] Tratamento de erros de conexao com retry
- [ ] Testes unitarios com mock do banco

**Dependencias:** DB-002, DB-011

**Paralelo com:** BE-002, DB-009

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### BE-002: Integrar persistencia no fluxo de TP atingido

**Status:** TODO

**Descricao:**
Modificar o `OrderTracker` para chamar `TradeRepository.save_trade()` quando um Take Profit e atingido.

**Criterios de Aceite:**
- [ ] `OrderTracker` recebe instancia de `TradeRepository` no construtor
- [ ] Ao detectar TP atingido (WebSocket ACCOUNT_UPDATE):
  - Calcular PnL
  - Criar objeto TradeRecord
  - Chamar `save_trade()` de forma assincrona
  - Nao bloquear o loop principal
- [ ] Log de sucesso/erro da persistencia
- [ ] Fallback: se banco indisponivel, logar trade em arquivo JSON
- [ ] Testes de integracao com banco real (Docker)

**Dependencias:** BE-001

**Paralelo com:** BE-003

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### BE-003: Carregar historico de trades do banco no startup

**Status:** TODO

**Descricao:**
Ao iniciar o bot, carregar historico de trades do banco para popular estatisticas do dashboard.

**Criterios de Aceite:**
- [ ] No startup, chamar `TradeRepository.get_recent_trades(limit=100)`
- [ ] Popular `trade_history` do GridManager com trades do banco
- [ ] Calcular estatisticas iniciais (total_pnl, win_rate, etc)
- [ ] Se banco indisponivel, iniciar com historico vazio + warning
- [ ] Configuracao `LOAD_HISTORY_ON_START=true|false`
- [ ] Tempo de carregamento < 2 segundos para 1000 trades

**Dependencias:** BE-001, BE-002

**Paralelo com:** FE-001

**Complexidade:** P

**Sprint:** 0.5

**Prioridade:** Alta

---

### BE-004: Implementar confirmacao de 2 velas (RF19)

**Status:** TODO

**Descricao:**
Modificar `MACDStrategy` para so mudar de estado apos 2 velas consecutivas confirmarem a direcao.

**Criterios de Aceite:**
- [ ] Novo parametro `MACD_CONFIRMATION_CANDLES=2` no .env
- [ ] Estado so muda de PAUSE->INACTIVE apos 2 velas com histograma negativo
- [ ] Estado so muda de INACTIVE->ACTIVATE apos 2 velas com histograma subindo
- [ ] Contador interno de velas de confirmacao
- [ ] Log quando confirmacao e atingida
- [ ] Testes unitarios com cenarios de falso sinal

**Dependencias:** Nenhuma (funcionalidade existente)

**Paralelo com:** BE-005, BE-006

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Media

---

### BE-005: Implementar preco inicial baseado em ATH (RF10)

**Status:** TODO

**Descricao:**
Permitir configurar o grid para comecar X% abaixo do All Time High em vez do preco atual.

**Criterios de Aceite:**
- [ ] Novo parametro `GRID_START_MODE=current|ath` no .env
- [ ] Novo parametro `ATH_PERCENT_BELOW=10` - % abaixo do ATH
- [ ] Buscar ATH da API BingX ou CoinGecko
- [ ] Cache de ATH por 24 horas (atualiza 1x/dia)
- [ ] Persistir ATH no banco (DB-006)
- [ ] Log do ATH utilizado e preco inicial calculado
- [ ] Fallback para preco atual se ATH indisponivel
- [ ] Testes com mock de API

**Dependencias:** DB-006

**Paralelo com:** BE-004, BE-006

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Alta

---

### BE-006: Implementar contador de hits por nivel (RF11)

**Status:** TODO

**Descricao:**
Rastrear quantas vezes cada faixa de preco do grid gerou lucro.

**Criterios de Aceite:**
- [ ] Classe `GridLevelTracker` em `src/grid/level_tracker.py`
- [ ] Ao registrar trade, incrementar hit_count do nivel
- [ ] Metodo `get_level_for_price(price) -> int`
- [ ] Metodo `increment_hit(level, pnl)`
- [ ] Metodo `get_stats_by_level() -> List[LevelStats]`
- [ ] Persistir no banco (DB-005) a cada N trades ou shutdown
- [ ] Carregar historico do banco no startup
- [ ] Exibir top 5 niveis no dashboard

**Dependencias:** DB-005, BE-001

**Paralelo com:** BE-004, BE-005

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Alta

---

### BE-007: Implementar atualizacao dinamica do TP (RF09)

**Status:** TODO

**Descricao:**
Apos 8 horas, aumentar TP de 0.3% para 0.5% + taxas para cobrir custos.

**Criterios de Aceite:**
- [ ] Novo parametro `TP_UPDATE_AFTER_HOURS=8` no .env
- [ ] Novo parametro `TP_UPDATED_PERCENT=0.5`
- [ ] Novo parametro `TP_INCLUDE_FEES=true` (adiciona 0.1% de taxas)
- [ ] Rastrear tempo de abertura de cada posicao
- [ ] Task assincrona que verifica posicoes antigas a cada 1h
- [ ] Atualizar ordem TP na exchange (cancelar antiga, criar nova)
- [ ] Log de atualizacoes de TP
- [ ] Nao atualizar se preco atual ja esta proximo do TP

**Dependencias:** Nenhuma

**Paralelo com:** BE-008

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Alta

---

### BE-008: Implementar protecao de margem automatica (RF13)

**Status:** TODO

**Descricao:**
Monitorar margem e injetar automaticamente se liquidacao estiver proxima.

**Criterios de Aceite:**
- [ ] Novo parametro `MARGIN_PROTECTION_ENABLED=true`
- [ ] Novo parametro `MARGIN_SAFETY_PERCENT=20` - % de distancia da liquidacao
- [ ] Novo parametro `MARGIN_INJECTION_PERCENT=10` - % do saldo a injetar
- [ ] Monitorar `liquidation_price` das posicoes via API
- [ ] Se preco atual < liquidation_price * (1 + safety%), injetar
- [ ] Usar endpoint de ajuste de margem da BingX
- [ ] Registrar evento no banco (DB-007)
- [ ] Alerta sonoro quando protecao ativa
- [ ] Limite maximo de injecoes por hora (evitar loop)
- [ ] Log detalhado de cada injecao

**Dependencias:** DB-007

**Paralelo com:** BE-007

**Complexidade:** G

**Sprint:** 2

**Prioridade:** Alta

---

### BE-009: Implementar pausa em tendencia de baixa (RF14)

**Status:** TODO

**Descricao:**
Usar indicadores adicionais (MA/MACD) para detectar tendencia de baixa e pausar criacao de ordens.

**Criterios de Aceite:**
- [ ] Novo parametro `TREND_DETECTION_ENABLED=true`
- [ ] Novo parametro `TREND_MA_PERIOD=50` - MA para tendencia
- [ ] Logica: se preco < MA50 E MACD negativo, estado = TREND_PAUSE
- [ ] Novo estado `TREND_PAUSE` (diferente de PAUSE normal)
- [ ] Nao criar novas ordens em TREND_PAUSE
- [ ] Manter posicoes existentes (nao cancelar TPs)
- [ ] Retomar quando preco > MA50 OU MACD positivo
- [ ] Log de entrada/saida de TREND_PAUSE
- [ ] Exibir indicador de tendencia no dashboard

**Dependencias:** Nenhuma

**Paralelo com:** BE-007, BE-008

**Complexidade:** M

**Sprint:** 2

**Prioridade:** Alta

---

### BE-010: Implementar sistema de ordens virtuais (RF12)

**Status:** TODO

**Descricao:**
Criar ordens que nao vao para exchange ate o preco atingir o nivel (gatilhos).

**Criterios de Aceite:**
- [ ] Novo parametro `VIRTUAL_ORDERS_ENABLED=true`
- [ ] Classe `VirtualOrderManager` em `src/grid/virtual_orders.py`
- [ ] Ordens criadas como WAITING no banco (DB-004)
- [ ] Monitorar preco em tempo real
- [ ] Quando preco <= trigger_price, enviar ordem real
- [ ] Atualizar status para TRIGGERED no banco
- [ ] Metodo `check_triggers(current_price)` chamado a cada update
- [ ] Cancelar ordens virtuais quando estado = INACTIVE
- [ ] Dashboard mostra ordens virtuais separadas das reais
- [ ] Fallback: se banco indisponivel, criar ordens reais

**Dependencias:** DB-004

**Paralelo com:** Nenhuma

**Complexidade:** G

**Sprint:** 3

**Prioridade:** Alta

---

### BE-011: Implementar RSI como indicador (RF15)

**Status:** TODO

**Descricao:**
Adicionar RSI ao sistema de estrategias para comprar quando sobrevendido.

**Criterios de Aceite:**
- [ ] Classe `RSIStrategy` em `src/strategy/rsi_strategy.py`
- [ ] Parametros: `RSI_PERIOD=14`, `RSI_OVERSOLD=30`, `RSI_OVERBOUGHT=70`
- [ ] Calcular RSI usando pandas-ta
- [ ] Metodo `should_buy() -> bool` (RSI < oversold)
- [ ] Metodo `should_sell() -> bool` (RSI > overbought)
- [ ] Integrar com sistema de filtros plugaveis
- [ ] Testes unitarios com dados historicos

**Dependencias:** BE-020 (sistema de filtros)

**Paralelo com:** BE-012, BE-013

**Complexidade:** M

**Sprint:** 4

**Prioridade:** Media

---

### BE-012: Implementar Bandas de Bollinger (RF16)

**Status:** TODO

**Descricao:**
Adicionar Bandas de Bollinger para sinalizar entradas.

**Criterios de Aceite:**
- [ ] Classe `BollingerStrategy` em `src/strategy/bollinger_strategy.py`
- [ ] Parametros: `BB_PERIOD=20`, `BB_STD=2`
- [ ] Calcular bandas usando pandas-ta
- [ ] Metodo `should_buy() -> bool` (preco < banda inferior)
- [ ] Metodo `should_sell() -> bool` (preco > banda superior)
- [ ] Exibir bandas no dashboard (opcional)
- [ ] Testes unitarios

**Dependencias:** BE-020 (sistema de filtros)

**Paralelo com:** BE-011, BE-013

**Complexidade:** M

**Sprint:** 4

**Prioridade:** Media

---

### BE-013: Implementar cruzamento de MAs (RF17)

**Status:** TODO

**Descricao:**
Usar cruzamento de medias moveis (MA 7/21) para indicar tendencia.

**Criterios de Aceite:**
- [ ] Classe `MACrossStrategy` em `src/strategy/ma_cross_strategy.py`
- [ ] Parametros: `MA_FAST=7`, `MA_SLOW=21`, `MA_TYPE=EMA|SMA`
- [ ] Calcular MAs usando pandas-ta
- [ ] Metodo `get_trend() -> str` (BULLISH, BEARISH, NEUTRAL)
- [ ] Golden Cross: MA7 cruza MA21 para cima = BULLISH
- [ ] Death Cross: MA7 cruza MA21 para baixo = BEARISH
- [ ] Integrar com sistema de filtros
- [ ] Testes unitarios

**Dependencias:** BE-020 (sistema de filtros)

**Paralelo com:** BE-011, BE-012

**Complexidade:** M

**Sprint:** 4

**Prioridade:** Media

---

### BE-014: Implementar Long + Short simultaneo (RF18)

**Status:** TODO

**Descricao:**
Permitir operar grid de compra E venda ao mesmo tempo para mercados laterais.

**Criterios de Aceite:**
- [ ] Novo parametro `GRID_MODE=long|short|both`
- [ ] Quando `both`, criar grid de compra abaixo do preco E grid de venda acima
- [ ] Gerenciar posicoes long e short separadamente
- [ ] TP independente para cada lado
- [ ] PnL calculado separadamente e agregado
- [ ] Dashboard mostra posicoes long e short
- [ ] Nao permitir no mesmo nivel (evitar self-trade)
- [ ] Testes de integracao

**Dependencias:** Nenhuma

**Paralelo com:** Nenhuma (complexo)

**Complexidade:** G

**Sprint:** 5

**Prioridade:** Media

---

### BE-015: Implementar estrategias customizadas (RF20)

**Status:** TODO

**Descricao:**
Permitir combinar 2+ indicadores em uma estrategia personalizada.

**Criterios de Aceite:**
- [ ] Classe `CustomStrategy` em `src/strategy/custom_strategy.py`
- [ ] Carregar configuracao de estrategia do banco (DB-003)
- [ ] Suportar operadores: AND, OR, NOT
- [ ] Exemplo: "MACD bullish AND RSI oversold"
- [ ] Parser de regras em formato JSON
- [ ] Validacao de regras no startup
- [ ] Testes com estrategias de exemplo

**Dependencias:** BE-011, BE-012, BE-013, DB-003

**Paralelo com:** Nenhuma

**Complexidade:** G

**Sprint:** 5

**Prioridade:** Media

---

### BE-016: Implementar backtest de estrategias (RF23)

**Status:** TODO

**Descricao:**
Simular estrategia nos dados historicos para avaliar performance.

**Criterios de Aceite:**
- [ ] Classe `Backtester` em `src/backtest/backtester.py`
- [ ] Parametros: start_date, end_date, strategy, initial_balance
- [ ] Buscar dados historicos da API BingX (klines)
- [ ] Simular execucao do grid com estrategia escolhida
- [ ] Calcular metricas: win_rate, total_pnl, max_drawdown, sharpe
- [ ] Salvar resultado no banco (DB-008)
- [ ] Comando CLI: `python main.py backtest --days=365`
- [ ] Exportar resultado para CSV (opcional)
- [ ] Nao fazer trades reais durante backtest

**Dependencias:** DB-008, BE-011, BE-012, BE-013

**Paralelo com:** Nenhuma

**Complexidade:** G

**Sprint:** 5

**Prioridade:** Baixa

---

### BE-017: Implementar trailing stop (RF24)

**Status:** TODO

**Descricao:**
Travar lucro quando mercado sobe, movendo o stop junto com o preco.

**Criterios de Aceite:**
- [ ] Novo parametro `TRAILING_STOP_ENABLED=false`
- [ ] Novo parametro `TRAILING_STOP_PERCENT=0.5` - % de distancia
- [ ] Quando preco sobe, mover stop para `preco * (1 - trailing%)`
- [ ] Stop so move para cima, nunca para baixo
- [ ] Atualizar ordem stop na exchange
- [ ] Log de cada movimento do trailing stop
- [ ] Testes com cenarios de volatilidade

**Dependencias:** Nenhuma

**Paralelo com:** BE-014

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Baixa

---

### BE-018: Refatorar para sistema de filtros plugaveis

**Status:** TODO

**Descricao:**
Refatorar arquitetura de estrategias para permitir adicionar novos indicadores como plugins.

**Criterios de Aceite:**
- [ ] Interface base `StrategyFilter` em `src/strategy/base.py`
- [ ] Metodos abstratos: `should_allow_trade() -> bool`, `get_state() -> dict`
- [ ] `MACDStrategy` herda de `StrategyFilter`
- [ ] Classe `StrategyOrchestrator` que combina multiplos filtros
- [ ] Configuracao de filtros via .env ou arquivo YAML
- [ ] Registro de filtros com decorator `@register_filter`
- [ ] Documentacao de como criar novo filtro

**Dependencias:** Nenhuma

**Paralelo com:** DB-001 (Sprint 0)

**Complexidade:** M

**Sprint:** 0

**Prioridade:** Alta

---

### BE-019: Adicionar suporte a multiplos pares de trading

**Status:** TODO

**Descricao:**
Permitir rodar o bot para diferentes pares alem de BTC-USDT.

**Criterios de Aceite:**
- [ ] Parametro `SYMBOLS=BTC-USDT,ETH-USDT` (lista)
- [ ] GridManager por simbolo
- [ ] WebSocket com subscricoes multiplas
- [ ] Dashboard com abas ou secoes por simbolo
- [ ] Estatisticas agregadas e por simbolo
- [ ] Limite de pares simultaneos (3 por padrao)

**Dependencias:** Nenhuma

**Paralelo com:** Pode ser feito apos Sprint 2

**Complexidade:** G

**Sprint:** 4

**Prioridade:** Media

---

### BE-020: Implementar testes de integracao com banco

**Status:** TODO

**Descricao:**
Criar suite de testes que usa banco PostgreSQL real via Docker.

**Criterios de Aceite:**
- [ ] Fixture pytest que sobe container PostgreSQL
- [ ] Testes para TradeRepository (CRUD completo)
- [ ] Testes para queries de agregacao
- [ ] Testes de performance (< 200ms)
- [ ] Cleanup automatico apos testes
- [ ] CI executa testes de integracao

**Dependencias:** DB-001, BE-001

**Paralelo com:** BE-003

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

## Grafico de Dependencias

```
Sprint 0:
BE-018 (Sistema de filtros) ----+
                                |
Sprint 0.5:                     |
DB-002 ---> BE-001 ---> BE-002 ---> BE-003
            (Repo)      (TP)        (Load)
              |
              +---> BE-020 (Testes integracao)

Sprint 1:
DB-005 ---> BE-006 (Hits por nivel)
DB-006 ---> BE-005 (ATH)
            BE-004 (2 velas)

Sprint 2:
DB-007 ---> BE-008 (Protecao margem)
            BE-007 (TP dinamico)
            BE-009 (Tendencia baixa)

Sprint 3:
DB-004 ---> BE-010 (Ordens virtuais)

Sprint 4:
BE-018 ---> BE-011 (RSI)
        |-> BE-012 (Bollinger)
        |-> BE-013 (MA Cross)
            BE-019 (Multi-pares)

Sprint 5:
BE-011/12/13 ---> BE-015 (Estrategias custom)
BE-011/12/13 ---> BE-016 (Backtest)
                  BE-014 (Long+Short)
                  BE-017 (Trailing stop)
```

---

## Ordem de Implementacao Sugerida

### Sprint 0
1. BE-018 - Sistema de filtros plugaveis

### Sprint 0.5
2. BE-001 - TradeRepository
3. BE-002 - Integracao persistencia no TP
4. BE-003 - Carregar historico no startup
5. BE-020 - Testes de integracao

### Sprint 1
6. BE-004 - Confirmacao de 2 velas
7. BE-005 - Preco inicial ATH
8. BE-006 - Contador de hits

### Sprint 2
9. BE-007 - TP dinamico
10. BE-008 - Protecao de margem
11. BE-009 - Pausa em tendencia de baixa

### Sprint 3
12. BE-010 - Ordens virtuais

### Sprint 4
13. BE-011 - RSI
14. BE-012 - Bollinger
15. BE-013 - MA Cross
16. BE-019 - Multi-pares

### Sprint 5
17. BE-014 - Long + Short
18. BE-015 - Estrategias customizadas
19. BE-016 - Backtest
20. BE-017 - Trailing stop

---

## Consideracoes Tecnicas

### Async/Await
- Todo acesso ao banco deve ser assincrono (asyncpg)
- Nao bloquear o loop principal de trading

### Error Handling
- Todas operacoes de banco tem retry com backoff
- Fallback para arquivo JSON se banco indisponivel

### Performance
- Cache de dados frequentes (ATH, configs)
- Pool de conexoes otimizado

### Testes
- Cada modulo deve ter > 80% de cobertura
- Testes de integracao com Docker

---

*Documento atualizado em 26/12/2025 - Versao 1.1 (Adicionado controle de status GitFlow)*
