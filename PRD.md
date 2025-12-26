# PRD - Product Requirements Document
# BTC Grid Bot

**Versao:** 1.1
**Data:** 22 de Dezembro de 2025
**Status:** Em Desenvolvimento

---

## 1. Sumario Executivo

O **BTC Grid Bot** e um sistema automatizado de trading que implementa a estrategia de Grid Trading para futuros perpetuos de Bitcoin (BTC-USDT) na exchange BingX. O bot combina a tecnica classica de grid trading com o indicador tecnico MACD para otimizar pontos de entrada, criando uma abordagem hibrida que visa maximizar lucros em mercados laterais e de tendencia.

### Principais Diferenciais
- Integracao nativa com MACD para controle inteligente de ciclos
- Suporte a modo Demo (VST - tokens virtuais) e modo Live (USDT real)
- Dashboard interativo em tempo real no terminal
- Sistema de alertas sonoros para eventos importantes
- Arquitetura modular e extensivel

---

## 2. Visao e Objetivos do Produto

### 2.1 Visao
Fornecer uma ferramenta de trading automatizada, segura e eficiente que permita traders de todos os niveis operarem estrategias de grid trading em criptomoedas com controle de risco baseado em indicadores tecnicos.

### 2.2 Objetivos de Negocio
| Objetivo | Metrica de Sucesso |
|----------|-------------------|
| Automacao de trades | Execucao 24/7 sem intervencao manual |
| Gestao de risco | Uso do MACD para evitar entradas em tendencias de baixa |
| Lucratividade | Taxa de acerto positiva em mercados laterais |
| Facilidade de uso | Configuracao via arquivo .env simples |

### 2.3 Objetivos do Usuario
- Operar grid trading sem necessidade de monitoramento constante
- Ter controle visual sobre posicoes e lucros em tempo real
- Poder testar estrategias em modo demo antes de usar capital real
- Configurar parametros de risco de acordo com seu perfil

---

## 3. Usuarios-Alvo e Personas

### 3.1 Persona Primaria: Trader Intermediario
- **Perfil:** Conhecimento basico de analise tecnica e futuros
- **Necessidade:** Automatizar estrategia de grid sem programar
- **Comportamento:** Monitora posicoes periodicamente, ajusta parametros

### 3.2 Persona Secundaria: Trader Avanado
- **Perfil:** Experiencia em trading algoritmico
- **Necessidade:** Ferramenta customizavel para testar estrategias
- **Comportamento:** Modifica codigo, adiciona indicadores

### 3.3 Persona Terciaria: Investidor Conservador
- **Perfil:** Busca renda passiva com baixo risco
- **Necessidade:** Modo demo para aprendizado e alavancagem baixa
- **Comportamento:** Usa configuracoes conservadoras

---

## 4. Analise de Mercado

### 4.1 Posicionamento
O BTC Grid Bot se posiciona como uma solucao open-source para grid trading com MACD, diferenciando-se de solucoes comerciais como:

| Caracteristica | BTC Grid Bot | Deribot | 3Commas |
|---------------|--------------|---------|---------|
| Open Source | Sim | Nao | Nao |
| MACD integrado | Sim | Sim | Parcial |
| Modo Demo | Sim (VST) | Sim | Limitado |
| Interface | Terminal | Web | Web |
| Custo | Gratuito | Pago | Pago |

### 4.2 Comparativo de Funcionalidades
Conforme documentado em `/docs/features_comparison.md`, o bot ja possui as funcionalidades core e tem um roadmap definido para features avancadas.

---

## 5. Arquitetura Tecnica

### 5.1 Visao Geral da Arquitetura

```
btcbot/
|-- main.py                    # Ponto de entrada principal
|-- config.py                  # Configuracoes e carregamento do .env
|-- requirements.txt           # Dependencias Python
|-- .env                       # Variaveis de ambiente (credenciais)
|-- src/
|   |-- client/
|   |   |-- bingx_client.py    # Cliente REST API BingX
|   |   |-- websocket_client.py # Cliente WebSocket para updates
|   |-- grid/
|   |   |-- grid_manager.py    # Orquestrador principal do grid
|   |   |-- grid_calculator.py # Calculos de niveis de preco
|   |   |-- order_tracker.py   # Rastreamento de ordens e posicoes
|   |-- strategy/
|   |   |-- macd_strategy.py   # Logica do indicador MACD
|   |-- ui/
|   |   |-- dashboard.py       # Interface Rich no terminal
|   |   |-- alerts.py          # Sistema de alertas sonoros
|   |   |-- keyboard_handler.py # Controles de teclado
|   |-- utils/
|       |-- logger.py          # Sistema de logging
|       |-- helpers.py         # Funcoes utilitarias
|-- logs/                      # Arquivos de log
|-- tests/                     # Testes automatizados
|-- docs/                      # Documentacao
```

### 5.2 Diagrama de Componentes

```
+-------------------+     +------------------+     +------------------+
|   BingX Exchange  |<--->|   BingXClient    |<--->|   GridManager    |
|  (REST + WS API)  |     | (HTTP + Cache)   |     | (Orquestrador)   |
+-------------------+     +------------------+     +------------------+
                                   ^                       |
                                   |                       v
                          +------------------+     +------------------+
                          | WebSocketClient  |     | MACDStrategy     |
                          | (Order Updates)  |     | (Indicador)      |
                          +------------------+     +------------------+
                                                           |
                                                           v
+------------------+     +------------------+     +------------------+
|   Dashboard      |<--->|   OrderTracker   |<--->| GridCalculator   |
|   (Rich UI)      |     | (Estado Local)   |     | (Niveis)         |
+------------------+     +------------------+     +------------------+
```

### 5.3 Stack Tecnologico

| Camada | Tecnologia | Versao |
|--------|-----------|--------|
| Linguagem | Python | 3.12+ |
| HTTP Client | httpx | >= 0.25.0 |
| WebSocket | websockets | >= 12.0 |
| Analise Tecnica | pandas-ta | >= 0.3.14b |
| Dataframes | pandas | >= 2.0.0 |
| Interface | rich | >= 13.0.0 |
| Configuracao | python-dotenv | >= 1.0.0 |
| Banco de Dados | PostgreSQL | >= 15.0 |
| DB Client (async) | asyncpg | >= 0.29.0 |

### 5.4 Integracao com BingX

O bot utiliza a API v2 de Perpetual Swaps da BingX:

**Endpoints REST:**
- `GET /openApi/swap/v2/quote/price` - Preco atual
- `GET /openApi/swap/v2/quote/klines` - Candles para MACD
- `GET /openApi/swap/v2/user/balance` - Saldo da conta
- `GET /openApi/swap/v2/user/positions` - Posicoes abertas
- `GET /openApi/swap/v2/trade/openOrders` - Ordens pendentes
- `POST /openApi/swap/v2/trade/order` - Criar ordem
- `DELETE /openApi/swap/v2/trade/order` - Cancelar ordem
- `POST /openApi/swap/v2/trade/leverage` - Configurar alavancagem

**WebSocket:**
- Market WebSocket: `wss://open-api-ws.bingx.com/market`
- Account WebSocket: Requer `listenKey` para atualizacoes de ordens

---

## 6. Requisitos Funcionais

### 6.1 Funcionalidades Implementadas

#### RF01 - Grid Trading Basico
| ID | Requisito | Status |
|----|-----------|--------|
| RF01.1 | Criar ordens LIMIT de compra em niveis de preco definidos | Implementado |
| RF01.2 | Calcular Take Profit automatico para cada ordem | Implementado |
| RF01.3 | Espacamento fixo (em USD) ou percentual entre niveis | Implementado |
| RF01.4 | Limitar ordens a um range abaixo do preco atual | Implementado |
| RF01.5 | Configurar numero maximo de ordens no grid | Implementado |

#### RF02 - Estrategia MACD
| ID | Requisito | Status |
|----|-----------|--------|
| RF02.1 | Calcular MACD com periodos configuraveis (fast/slow/signal) | Implementado |
| RF02.2 | Estados do grid baseados no histograma MACD | Implementado |
| RF02.3 | ACTIVATE: histograma subindo com MACD negativo | Implementado |
| RF02.4 | ACTIVE: histograma positivo e subindo | Implementado |
| RF02.5 | PAUSE: histograma positivo descendo com MACD positivo | Implementado |
| RF02.6 | INACTIVE: histograma negativo e descendo | Implementado |
| RF02.7 | Timeframe configuravel (1m, 5m, 15m, 1h, 4h, 1d) | Implementado |

#### RF03 - Gerenciamento de Ordens
| ID | Requisito | Status |
|----|-----------|--------|
| RF03.1 | Rastrear ordens pendentes em memoria | Implementado |
| RF03.2 | Detectar ordens executadas via WebSocket | Implementado |
| RF03.3 | Detectar Take Profit atingido | Implementado |
| RF03.4 | Cancelar ordens pendentes ao entrar em INACTIVE | Implementado |
| RF03.5 | Preservar ordens TP quando bot e encerrado | Implementado |
| RF03.6 | Sincronizar estado local com exchange | Implementado |

#### RF04 - Interface do Usuario
| ID | Requisito | Status |
|----|-----------|--------|
| RF04.1 | Dashboard em tempo real com Rich library | Implementado |
| RF04.2 | Exibir preco atual, estado MACD, histograma | Implementado |
| RF04.3 | Tabela de posicoes abertas com PnL | Implementado |
| RF04.4 | Historico de trades completados | Implementado |
| RF04.5 | Resumo de estatisticas (trades, lucro, win rate) | Implementado |
| RF04.6 | Controles de teclado (A=ativar, D=desativar, Q=sair) | Implementado |

#### RF05 - Alertas e Notificacoes
| ID | Requisito | Status |
|----|-----------|--------|
| RF05.1 | Alertas sonoros para ordem executada | Implementado |
| RF05.2 | Alertas sonoros para TP atingido | Implementado |
| RF05.3 | Alertas sonoros para mudanca de estado do grid | Implementado |
| RF05.4 | Suporte multiplataforma (macOS, Linux, Windows) | Implementado |

#### RF06 - Modo Demo
| ID | Requisito | Status |
|----|-----------|--------|
| RF06.1 | Suporte a API VST (Virtual Standard Token) da BingX | Implementado |
| RF06.2 | Troca entre modo demo/live via configuracao | Implementado |
| RF06.3 | Indicacao visual clara do modo atual | Implementado |

#### RF07 - Logging
| ID | Requisito | Status |
|----|-----------|--------|
| RF07.1 | Log separado para trades | Implementado |
| RF07.2 | Log separado para ordens | Implementado |
| RF07.3 | Log separado para erros | Implementado |
| RF07.4 | Log separado para MACD | Implementado |
| RF07.5 | Log principal do sistema | Implementado |

### 6.2 Funcionalidades Planejadas (Roadmap)

#### Prioridade Alta
| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| RF08 | Persistencia em Banco de Dados | Armazenar historico de trades em PostgreSQL |
| RF09 | Atualizacao dinamica do TP | Apos 8h, mudar TP de 0.3% para 0.5% + taxas |
| RF10 | Preco inicial baseado em ATH | Comecar X% abaixo da maxima historica |
| RF11 | Contador de hits por nivel | Quantas vezes cada faixa gerou lucro |
| RF12 | Ordens virtuais (gatilhos) | Ordens nao vao para exchange ate preco bater |
| RF13 | Protecao de margem automatica | Injetar margem se liquidacao proxima |
| RF14 | Pausar em tendencia de baixa | Usar MA/MACD para detectar queda |

#### Prioridade Media
| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| RF15 | RSI como indicador | Comprar quando sobrevendido |
| RF16 | Bandas de Bollinger | Usar para entradas |
| RF17 | Cruzamento de MAs | MA 7/21 para indicar tendencia |
| RF18 | Long + Short simultaneo | Aproveitar lateralidade |
| RF19 | Confirmacao de 2 velas | So mudar estado apos confirmacao |
| RF20 | Estrategias customizadas | Combinar 2+ indicadores |

#### Prioridade Baixa
| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| RF21 | Interface Web | Dashboard web em vez de terminal |
| RF22 | Multiplas estrategias salvas | Salvar e alternar configuracoes |
| RF23 | Backtest de estrategias | Simular nos ultimos X anos |
| RF24 | Trailing stop | Travar lucro quando mercado sobe |

---

### 6.3 RF08 - Persistencia em Banco de Dados (Detalhamento)

#### Contexto

O sistema necessita armazenar o historico de trades executados para consultas, relatorios e dashboards. Atualmente os dados existem apenas em memoria e logs de texto.

**Requisitos levantados:**
- Volume: 200+ trades/dia por conta
- Retencao: Ilimitada (historico completo)
- Multi-tenant: Multiplos usuarios com dados isolados
- Consultas: Agregacoes (PnL, win rate), filtros por periodo
- Atualizacao: Tempo real para dashboards
- Dados: Trades executados (entry, exit, pnl)

#### Decisao: PostgreSQL

Analise comparativa realizada entre PostgreSQL e MongoDB:

| Criterio | PostgreSQL | MongoDB | Vencedor |
|----------|-----------|---------|----------|
| Estrutura dos dados | Trades sao tabulares, schema fixo | Flexibilidade desnecessaria | PostgreSQL |
| Agregacoes (PnL, win rate) | SQL nativo, conciso | Pipeline verboso | PostgreSQL |
| Consultas analiticas | Window functions, CTEs | Limitado | PostgreSQL |
| Performance 200+ trades/dia | Trivial | Trivial | Empate |
| Multi-tenancy | Row-Level Security nativo | Via codigo | PostgreSQL |
| Hospedagem cloud | Supabase, Neon | Atlas | Empate |
| Ecossistema Python | asyncpg, SQLAlchemy | motor, Beanie | Empate |

**Justificativa**: Dados de trading (entry_price, exit_price, pnl, timestamps) sao naturalmente tabulares e previsiveis. SQL e a linguagem ideal para agregacoes e relatorios. PostgreSQL oferece RLS para isolamento multi-tenant nativo.

#### Requisitos Funcionais

| ID | Requisito | Criterio de Aceite |
|----|-----------|-------------------|
| RF08.1 | Persistir trades executados | Trade salvo em < 100ms apos TP atingido |
| RF08.2 | Consultar trades por periodo | Query com filtro de data em < 200ms |
| RF08.3 | Calcular agregacoes | PnL total, win rate, media por trade |
| RF08.4 | Isolar dados por usuario | Usuario so ve seus proprios trades |
| RF08.5 | Suportar conta demo e live | Campo account_type diferencia os modos |

#### Schema do Banco de Dados

```sql
-- Tabela de trades executados
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    account_type VARCHAR(10) NOT NULL DEFAULT 'demo',
    symbol VARCHAR(20) NOT NULL DEFAULT 'BTC-USDT',
    side VARCHAR(10) NOT NULL DEFAULT 'LONG',
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    pnl DECIMAL(20, 8) NOT NULL,
    pnl_percent DECIMAL(10, 4) NOT NULL,
    grid_level INTEGER,
    entry_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices para consultas frequentes
CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_user_closed ON trades(user_id, closed_at DESC);
CREATE INDEX idx_trades_user_account ON trades(user_id, account_type);
```

#### Consultas Tipicas

```sql
-- Estatisticas do usuario
SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl
FROM trades
WHERE user_id = $1;

-- Trades dos ultimos 30 dias
SELECT * FROM trades
WHERE user_id = $1 AND closed_at >= NOW() - INTERVAL '30 days'
ORDER BY closed_at DESC;
```

#### Estrategia de Deploy

| Fase | Ambiente | Solucao |
|------|----------|---------|
| Desenvolvimento | Local | PostgreSQL via Docker |
| Producao inicial | Homeserver | PostgreSQL via Docker Compose |
| Producao cloud | Cloud | Supabase ou Neon (tier gratuito) |

---

## 7. Requisitos Nao-Funcionais

### 7.1 Performance
| ID | Requisito | Especificacao |
|----|-----------|---------------|
| RNF01 | Latencia de atualizacao | Dashboard atualiza a cada 5 segundos |
| RNF02 | Cache de API | Klines: 60s, Balance: 30s, Orders: 15s |
| RNF03 | Rate limiting | Maximo 10 ordens por ciclo de atualizacao |
| RNF04 | Backoff em erros | 8 minutos de pausa apos rate limit |

### 7.2 Disponibilidade
| ID | Requisito | Especificacao |
|----|-----------|---------------|
| RNF05 | Reconexao automatica | WebSocket reconecta com backoff exponencial |
| RNF06 | Renovacao de listenKey | A cada 20 minutos automaticamente |
| RNF07 | Recuperacao de estado | Carrega posicoes existentes ao iniciar |

### 7.3 Seguranca
| ID | Requisito | Especificacao |
|----|-----------|---------------|
| RNF08 | Credenciais | Armazenadas em .env (nao commitado) |
| RNF09 | Assinatura HMAC | SHA256 em todas requisicoes autenticadas |
| RNF10 | Modo demo padrao | TRADING_MODE=demo por padrao |

### 7.4 Usabilidade
| ID | Requisito | Especificacao |
|----|-----------|---------------|
| RNF11 | Configuracao simples | Todas opcoes via .env |
| RNF12 | Feedback visual | Cores e estados claros no dashboard |
| RNF13 | Documentacao | .env.example com todas opcoes comentadas |

### 7.5 Manutenibilidade
| ID | Requisito | Especificacao |
|----|-----------|---------------|
| RNF14 | Modularidade | Componentes independentes e testables |
| RNF15 | Logging | Logs separados por dominio |
| RNF16 | Typing | Type hints em todo o codigo |

---

## 8. Fluxos de Usuario

### 8.1 Fluxo Principal: Operacao Normal

```
1. Usuario configura .env com credenciais e parametros
2. Usuario executa: python main.py
3. Sistema valida credenciais
4. Sistema testa conexao com BingX
5. Sistema exibe configuracao atual
6. Usuario confirma inicio do bot
7. Sistema configura alavancagem
8. Sistema carrega posicoes existentes
9. Sistema inicia WebSocket para updates
10. Loop principal:
    a. Busca preco atual
    b. Busca klines para MACD
    c. Calcula estado do grid
    d. Se estado permite, cria ordens
    e. Sincroniza com exchange
    f. Atualiza dashboard
    g. Aguarda 5 segundos
11. Usuario pressiona Q para sair
12. Sistema cancela ordens LIMIT (preserva TPs)
13. Sistema encerra WebSocket
```

### 8.2 Fluxo: Ativacao Manual de Ciclo

```
1. Bot esta em estado WAIT ou PAUSE
2. Usuario pressiona tecla A
3. Sistema verifica se nao esta em INACTIVE
4. Se permitido:
   a. Flag cycle_activated = True
   b. Emite alerta sonoro
   c. Comeca criar ordens no proximo update
5. Se nao permitido:
   a. Log de warning
   b. Nenhuma acao tomada
```

### 8.3 Fluxo: Take Profit Atingido

```
1. WebSocket recebe evento ACCOUNT_UPDATE
2. Sistema detecta posicao fechada (quantity = 0)
3. Para cada ordem FILLED no tracker:
   a. Calcula PnL
   b. Registra trade no historico
   c. Remove do tracker
   d. Emite alerta sonoro
4. Dashboard atualiza estatisticas
```

---

## 9. Modelo de Dados

### 9.1 Configuracao (Config)

```python
@dataclass
class Config:
    bingx: BingXConfig       # API credentials
    trading: TradingConfig   # Symbol, leverage, order size
    grid: GridConfig         # Spacing, range, TP
    macd: MACDConfig         # Fast, slow, signal, timeframe
    reactivation_mode: ReactivationMode
```

### 9.2 Estado do Grid (GridStatus)

```python
@dataclass
class GridStatus:
    state: GridState         # ACTIVATE, ACTIVE, PAUSE, INACTIVE, WAIT
    current_price: float     # Preco atual BTC
    pending_orders: int      # Ordens pendentes
    open_positions: int      # Posicoes abertas
    total_trades: int        # Total de trades fechados
    total_pnl: float         # PnL acumulado
    macd_line: float         # Valor atual MACD
    histogram: float         # Valor atual histograma
    cycle_activated: bool    # Ciclo foi ativado
    margin_error: bool       # Erro de margem
    rate_limited: bool       # Rate limit ativo
```

### 9.3 Ordem Rastreada (TrackedOrder)

```python
@dataclass
class TrackedOrder:
    order_id: str
    entry_price: float
    tp_price: float
    quantity: float
    status: OrderStatus      # PENDING, FILLED, TP_HIT, CANCELLED
    created_at: datetime
    filled_at: datetime | None
    closed_at: datetime | None
    pnl: float | None
```

### 9.4 Registro de Trade (TradeRecord)

```python
@dataclass
class TradeRecord:
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    entry_time: datetime
    exit_time: datetime
```

---

## 10. Parametros de Configuracao

### 10.1 Credenciais BingX
| Variavel | Descricao | Exemplo |
|----------|-----------|---------|
| BINGX_API_KEY | Chave API da BingX | abc123... |
| BINGX_SECRET_KEY | Chave secreta da BingX | xyz789... |

### 10.2 Modo de Trading
| Variavel | Descricao | Valores |
|----------|-----------|---------|
| TRADING_MODE | Modo de operacao | demo, live |
| SYMBOL | Par de trading | BTC-USDT |
| LEVERAGE | Alavancagem | 1-125 |
| ORDER_SIZE_USDT | Valor por ordem em USDT | 100 |

### 10.3 Grid
| Variavel | Descricao | Valores |
|----------|-----------|---------|
| GRID_SPACING_TYPE | Tipo de espacamento | fixed, percent |
| GRID_SPACING_VALUE | Valor do espacamento | 100 ($) ou 0.1 (%) |
| GRID_RANGE_PERCENT | Range abaixo do preco | 5 (%) |
| TAKE_PROFIT_PERCENT | TP por ordem | 1.0 (%) |
| MAX_ORDERS | Maximo de ordens | 10 |

### 10.4 MACD
| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| MACD_FAST | Periodo rapido | 12 |
| MACD_SLOW | Periodo lento | 26 |
| MACD_SIGNAL | Periodo sinal | 9 |
| MACD_TIMEFRAME | Timeframe | 1h |

### 10.5 Comportamento
| Variavel | Descricao | Valores |
|----------|-----------|---------|
| REACTIVATION_MODE | Modo reativacao | immediate, full_cycle |

### 10.6 Banco de Dados
| Variavel | Descricao | Exemplo |
|----------|-----------|---------|
| DATABASE_URL | Connection string PostgreSQL | postgresql://user:pass@localhost:5432/btcbot |  <!-- pragma: allowlist secret -->
| DB_POOL_SIZE | Tamanho do pool de conexoes | 5 |

---

## 11. Timeline e Milestones

### Sprint 0 - Infraestrutura (Planejado)
- [ ] Criar repositorio GitHub
- [ ] Configurar gitflow (main, develop)
- [ ] Criar Dockerfile + docker-compose.yml
- [ ] Refatorar estrategias para sistema de filtros plugaveis

### Sprint 0.5 - Persistencia de Dados (Planejado)
- [ ] Configurar PostgreSQL via Docker Compose
- [ ] Criar schema da tabela trades
- [ ] Implementar camada de repositorio (TradeRepository)
- [ ] Integrar persistencia no fluxo de TP atingido
- [ ] Atualizar dashboard para carregar historico do banco
- [ ] Documentar configuracao do banco no README

### Sprint 1 - Quick Wins (Planejado)
- [ ] Confirmacao de 2 velas
- [ ] Preco inicial baseado em ATH
- [ ] Contador de hits por nivel

### Sprint 2 - Protecao e Gestao (Planejado)
- [ ] Atualizacao dinamica do TP (8h + taxas)
- [ ] Protecao de margem automatica
- [ ] Pausar em tendencia de baixa

### Sprint 3 - Ordens Virtuais (Planejado)
- [ ] Sistema de gatilhos virtuais
- [ ] Historico completo de ordens

### Sprint 4 - Indicadores (Planejado)
- [ ] Cruzamento de Medias Moveis
- [ ] RSI
- [ ] Bandas de Bollinger

### Sprint 5 - Avancado (Planejado)
- [ ] Estrategias customizadas
- [ ] Backtest
- [ ] Long + Short simultaneo
- [ ] Interface Web (opcional)

---

## 12. Riscos e Mitigacoes

### 12.1 Riscos Tecnicos
| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Desconexao WebSocket | Alta | Medio | Reconexao automatica com backoff |
| Rate limit da API | Media | Alto | Backoff de 8 minutos, cache agressivo |
| Erro de margem | Media | Alto | Pausa de 5 minutos, alerta visual |
| ListenKey expirado | Alta | Baixo | Renovacao automatica a cada 20 min |

### 12.2 Riscos de Negocio
| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Perdas em mercado de baixa | Alta | Alto | MACD cancela ordens em INACTIVE |
| Liquidacao | Baixa | Critico | Modo demo por padrao, alavancagem configuravel |
| Mudanca na API BingX | Baixa | Alto | Arquitetura modular permite adaptacao |

### 12.3 Riscos Operacionais
| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Queda de internet | Media | Medio | TPs ficam na exchange |
| Crash do bot | Baixa | Medio | Preserva TPs ao encerrar |
| Erro de configuracao | Media | Alto | Validacao no startup |

---

## 13. Metricas de Sucesso

### 13.1 KPIs Tecnicos
| Metrica | Meta | Medicao |
|---------|------|---------|
| Uptime do bot | 99% | Logs de erro |
| Latencia de atualizacao | < 5s | Dashboard refresh |
| Taxa de reconexao | 100% | Logs de WebSocket |

### 13.2 KPIs de Trading
| Metrica | Meta | Medicao |
|---------|------|---------|
| Win rate | > 70% | Tracker de trades |
| PnL positivo | Em mercado lateral | Total PnL no dashboard |
| Ordens por dia | Variavel | Logs de ordens |

### 13.3 KPIs de Qualidade
| Metrica | Meta | Medicao |
|---------|------|---------|
| Cobertura de testes | > 80% | pytest coverage |
| Bugs criticos | 0 | Issue tracker |
| Tempo de setup | < 5 min | Documentacao |

---

## 14. Glossario

| Termo | Definicao |
|-------|-----------|
| **Grid Trading** | Estrategia que coloca ordens de compra/venda em intervalos regulares de preco |
| **MACD** | Moving Average Convergence Divergence - indicador de momentum |
| **Histograma** | Diferenca entre linha MACD e linha de sinal |
| **Take Profit (TP)** | Ordem de saida automatica quando preco atinge lucro alvo |
| **VST** | Virtual Standard Token - tokens virtuais para modo demo da BingX |
| **Perpetual Swap** | Contrato futuro sem data de expiracao |
| **Leverage** | Alavancagem - multiplicador de posicao |
| **ListenKey** | Token de autenticacao para WebSocket de conta |

---

## 15. Apendices

### A. Exemplo de Arquivo .env

```bash
# Credenciais
BINGX_API_KEY=sua_chave_aqui
BINGX_SECRET_KEY=sua_secret_aqui

# Modo
TRADING_MODE=demo
SYMBOL=BTC-USDT
LEVERAGE=10

# Grid
GRID_SPACING_TYPE=fixed
GRID_SPACING_VALUE=100
GRID_RANGE_PERCENT=5
TAKE_PROFIT_PERCENT=1.0
ORDER_SIZE_USDT=100
MAX_ORDERS=10

# MACD
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
MACD_TIMEFRAME=1h

# Comportamento
REACTIVATION_MODE=immediate
```

### B. Estados do MACD e Acoes

| Estado | Histograma | MACD | Acao |
|--------|-----------|------|------|
| ACTIVATE | < 0, subindo | < 0 | Iniciar criacao de ordens |
| ACTIVE | > 0, subindo | qualquer | Continuar criando ordens |
| ACTIVE | > 0, descendo | <= 0 | Continuar criando ordens |
| PAUSE | > 0, descendo | > 0 | Parar criacao, manter existentes |
| INACTIVE | < 0, descendo | qualquer | Cancelar ordens pendentes |
| WAIT | < 0, subindo | >= 0 | Aguardar condicoes |

### C. Estrutura de Logs

```
logs/
|-- main.log      # Eventos principais do sistema
|-- orders.log    # Criacao, execucao, cancelamento de ordens
|-- trades.log    # Trades completados com PnL
|-- macd.log      # Mudancas de estado do MACD
|-- errors.log    # Erros e excecoes
```

---

## 16. Historico de Revisoes

| Versao | Data | Autor | Descricao |
|--------|------|-------|-----------|
| 1.0 | 22/12/2025 | Claude Code | Versao inicial do PRD |
| 1.1 | 22/12/2025 | Claude Code | Adicionado RF08 - Persistencia em PostgreSQL |

---

*Documento gerado automaticamente com base na analise do codigo-fonte do projeto BTC Grid Bot.*
