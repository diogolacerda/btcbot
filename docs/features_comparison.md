# Comparação de Funcionalidades: Nosso Bot vs Deribot

## Funcionalidades que JÁ TEMOS ✅

| Funcionalidade | Nosso Bot | Deribot |
|----------------|-----------|---------|
| Grid Trading com MACD | ✅ | ✅ |
| Timeframe configurável | ✅ 1m, 5m, 15m, 1h, 4h, 1d | ✅ |
| Intervalo de preço (spacing) | ✅ Fixo ou $ | ✅ A cada $50 |
| Take Profit por ordem | ✅ % configurável | ✅ 0.3% ou 0.5% |
| Recompra na mesma faixa | ✅ REACTIVATION_MODE | ✅ |
| Quantidade de ordens máx | ✅ MAX_ORDERS | ✅ Até 1000 |
| Valor por ordem (USDT) | ✅ ORDER_SIZE_USDT | ✅ |
| Sinal do histograma | ✅ Cruzamento do zero | ✅ |
| Modo Demo/Live | ✅ VST vs USDT | ✅ |
| Leverage configurável | ✅ | ✅ |
| Dashboard em tempo real | ✅ Terminal Rich | ✅ Web |
| Alertas sonoros | ✅ | ✅ |
| Ativação manual do ciclo | ✅ Tecla A | - |

---

## Funcionalidades que NÃO TEMOS ❌

### 🔴 Prioridade Alta (Impacto Direto no Lucro/Segurança)

| # | Funcionalidade | Descrição |
|---|----------------|-----------|
| 1 | Atualização dinâmica do TP | Após 8h, muda TP de 0.3% para 0.5% + taxas acumuladas |
| 2 | Preço inicial baseado em ATH | Começar X% abaixo da máxima histórica |
| 3 | Contador de hits por nível | Quantas vezes cada faixa gerou lucro |
| 4 | Ordens virtuais (gatilhos) | Ordens não vão para exchange até preço bater (limite 200 TPs) |
| 5 | Proteção de margem automática | Se chegar a X% de liquidação, injeta margem para distanciar |
| 6 | Pausar em tendência de baixa | Só abrir ordens quando MACD/MA indicar tendência de alta |

### 🟡 Prioridade Média (Mais Estratégias/Indicadores)

| # | Funcionalidade | Descrição |
|---|----------------|-----------|
| 7 | RSI como indicador | Comprar quando sobrevendido |
| 8 | Bandas de Bollinger | Usar para entradas |
| 9 | Cruzamento de Médias Móveis | MA 7/21 para indicar tendência |
| 10 | Long + Short simultâneo | Aproveitar lateralidade nos dois lados |
| 11 | Confirmação de 2 velas | Só mudar estado após confirmação |
| 12 | Estratégias customizadas | Combinar 2+ indicadores como gatilho |

### 🟢 Prioridade Baixa (Nice to Have)

| # | Funcionalidade | Descrição |
|---|----------------|-----------|
| 13 | Interface Web | Dashboard web em vez de terminal |
| 14 | Histórico completo de ordens | Ver todas ordens virtuais, pendentes, executadas |
| 15 | Múltiplas estratégias salvas | Salvar e alternar entre configurações |
| 16 | Short em faixas | Shortar quando sobrecomprado |
| 17 | Calculadora de gestão de risco | Calcular tamanho de mão, alavancagem sugerida |
| 18 | Backtest de estratégias | Simular estratégia nos últimos X anos |
| 19 | Stop gain (trailing) | Travar lucro quando mercado sobe |

---

## Roadmap Atualizado

### Sprint 1 - Quick Wins
- Confirmação de 2 velas
- Preço inicial baseado em ATH
- Contador de hits por nível

### Sprint 2 - Proteção e Gestão
- Atualização dinâmica do TP (8h + taxas)
- Proteção de margem automática
- Pausar em tendência de baixa (MACD)

### Sprint 3 - Ordens Virtuais
- Sistema de gatilhos virtuais
- Histórico completo de ordens

### Sprint 4 - Indicadores
- Cruzamento de Médias Móveis
- RSI
- Bandas de Bollinger

### Sprint 5 - Avançado
- Estratégias customizadas (combinar indicadores)
- Backtest de estratégias
- Long + Short simultâneo
- Interface Web (opcional)

---

## Requisitos Não-Funcionais

### 🏗️ Infraestrutura

| # | Requisito | Descrição |
|---|-----------|-----------|
| 1 | Docker container | App roda em container para deploy fácil em qualquer servidor |
| 2 | GitHub + Gitflow | Repositório com branches: main, develop, feature/*, hotfix/* |

### ⚙️ Arquitetura

| # | Requisito | Descrição |
|---|-----------|-----------|
| 3 | Filtros dinâmicos | Habilitar/desabilitar regras em runtime (MACD, RSI, MAs, etc) |
| 4 | Modo sem filtro | Se todos filtros desabilitados, abre ordens em todas as faixas |
| 5 | Hot reload de config | Mudar configurações sem reiniciar o bot |
| 6 | Alavancagem por estado | Configurar leverage diferente para cada estado do MACD |

### 📊 Alavancagem Dinâmica por Estado

| Estado | Condição | Leverage Sugerido |
|--------|----------|-------------------|
| ACTIVATE | Linha < 0, hist vermelho→claro | 2x (conservador) |
| ACTIVE | Hist verde, linha cruzou zero | 5-10x (agressivo) |
| PAUSE | Hist verde escuro→claro | Manter ou reduzir |
| INACTIVE | Hist vermelho escuro | Não abrir novas |

---

## Sprint 0 - Infraestrutura (Fazer Primeiro!)

1. Criar repositório GitHub
2. Configurar gitflow (main, develop)
3. Criar Dockerfile + docker-compose.yml
4. Refatorar estratégias para sistema de filtros plugáveis
