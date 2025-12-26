# Tarefas de Frontend/UI - BTC Grid Bot

**Data:** 22 de Dezembro de 2025
**Versao:** 1.0

---

## Resumo

Este documento contém todas as tarefas relacionadas a interface do usuario, incluindo dashboard terminal (Rich), controles de teclado, visualizacoes e futura interface web.

---

## Legenda

- **Complexidade:** P (Pequena ~0.5 dia), M (Media ~1-2 dias), G (Grande ~3-5 dias)
- **Prioridade:** Alta, Media, Baixa
- **Status:** Pendente, Em Progresso, Concluido

---

## Tarefas

### FE-001: Atualizar dashboard para exibir dados do banco

**Descricao:**
Modificar o dashboard Rich para carregar e exibir estatisticas vindas do PostgreSQL em vez de apenas memoria.

**Criterios de Aceite:**
- [ ] Dashboard carrega historico de trades do banco no startup
- [ ] Secao "Estatisticas" mostra dados agregados do banco:
  - Total de trades (all-time)
  - Win rate
  - PnL total
  - PnL medio por trade
- [ ] Indicador visual se dados sao do banco ou memoria
- [ ] Se banco indisponivel, mostrar warning e usar dados locais
- [ ] Atualizacao a cada 30 segundos (nao a cada refresh)

**Dependencias:** BE-001, BE-003

**Paralelo com:** FE-002

**Complexidade:** M

**Sprint:** 0.5

**Prioridade:** Alta

---

### FE-002: Adicionar secao de hits por nivel no dashboard

**Descricao:**
Nova secao no dashboard mostrando os niveis de grid mais lucrativos.

**Criterios de Aceite:**
- [ ] Nova tabela "Top Niveis" no dashboard
- [ ] Colunas: Nivel, Range de Preco, Hits, PnL Total, PnL Medio
- [ ] Exibir top 5 niveis ordenados por PnL ou hits
- [ ] Opcao de ordenacao via tecla (H = hits, P = pnl)
- [ ] Cores: verde para niveis lucrativos, vermelho para negativos
- [ ] Atualiza quando novo trade e registrado

**Dependencias:** BE-006

**Paralelo com:** FE-001

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Alta

---

### FE-003: Adicionar indicador de tendencia no dashboard

**Descricao:**
Exibir indicador visual de tendencia baseado em MA/MACD para RF14.

**Criterios de Aceite:**
- [ ] Nova secao "Tendencia" no dashboard
- [ ] Exibir:
  - Preco atual vs MA50
  - Direcao da tendencia (BULLISH/BEARISH/NEUTRAL)
  - Icone de seta (cima/baixo/lado)
- [ ] Cores: verde bullish, vermelho bearish, amarelo neutral
- [ ] Se estado = TREND_PAUSE, destacar com borda
- [ ] Tooltip explicando o indicador

**Dependencias:** BE-009

**Paralelo com:** FE-004

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Alta

---

### FE-004: Adicionar secao de ordens virtuais no dashboard

**Descricao:**
Exibir ordens virtuais (gatilhos) separadas das ordens reais.

**Criterios de Aceite:**
- [ ] Nova tabela "Ordens Virtuais" no dashboard
- [ ] Colunas: Nivel, Preco Gatilho, Quantidade, Status, Tempo Esperando
- [ ] Status: WAITING (amarelo), TRIGGERED (verde)
- [ ] Contador total de ordens virtuais vs reais
- [ ] Destacar ordens proximas do preco atual (< 1%)
- [ ] Atualiza em tempo real quando gatilho dispara

**Dependencias:** BE-010

**Paralelo com:** FE-003

**Complexidade:** M

**Sprint:** 3

**Prioridade:** Alta

---

### FE-005: Adicionar indicadores tecnicos no dashboard

**Descricao:**
Exibir valores dos indicadores tecnicos adicionais (RSI, Bollinger, MA).

**Criterios de Aceite:**
- [ ] Nova secao "Indicadores" no dashboard
- [ ] Exibir para cada indicador ativo:
  - Nome do indicador
  - Valor atual
  - Sinal (BUY/SELL/HOLD)
- [ ] RSI: valor numerico + barra visual (0-100)
- [ ] Bollinger: preco vs bandas (acima/dentro/abaixo)
- [ ] MA Cross: MA7 vs MA21 + sinal de cruzamento
- [ ] Cores conforme sinal (verde BUY, vermelho SELL)
- [ ] Indicador aparece apenas se habilitado no .env

**Dependencias:** BE-011, BE-012, BE-013

**Paralelo com:** FE-006

**Complexidade:** M

**Sprint:** 4

**Prioridade:** Media

---

### FE-006: Exibir posicoes Long e Short no dashboard

**Descricao:**
Adaptar dashboard para mostrar posicoes long e short separadamente.

**Criterios de Aceite:**
- [ ] Se `GRID_MODE=both`, exibir duas tabelas de posicoes
- [ ] Tabela "Posicoes LONG" com posicoes de compra
- [ ] Tabela "Posicoes SHORT" com posicoes de venda
- [ ] PnL agregado e separado por tipo
- [ ] Cores diferentes para long (verde) e short (vermelho)
- [ ] Contador de posicoes por tipo

**Dependencias:** BE-014

**Paralelo com:** FE-005

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Media

---

### FE-007: Adicionar controle de teclado para filtros

**Descricao:**
Novos atalhos de teclado para controlar indicadores em tempo real.

**Criterios de Aceite:**
- [ ] Tecla R: Toggle RSI on/off
- [ ] Tecla B: Toggle Bollinger on/off
- [ ] Tecla M: Toggle MA Cross on/off
- [ ] Tecla T: Alternar modo de tendencia on/off
- [ ] Feedback visual ao pressionar tecla
- [ ] Estado persistido durante a sessao
- [ ] Help atualizado com novos atalhos (tecla ?)

**Dependencias:** BE-011, BE-012, BE-013, BE-009

**Paralelo com:** FE-005

**Complexidade:** P

**Sprint:** 4

**Prioridade:** Media

---

### FE-008: Implementar tela de backtest no terminal

**Descricao:**
Interface para executar e visualizar resultados de backtest no terminal.

**Criterios de Aceite:**
- [ ] Modo backtest separado do modo trading
- [ ] Wizard de configuracao:
  - Data inicio/fim
  - Estrategia a testar
  - Saldo inicial
- [ ] Barra de progresso durante execucao
- [ ] Exibir resultado:
  - Metricas principais (win rate, PnL, drawdown)
  - Lista de trades simulados
  - Grafico ASCII de evolucao do saldo
- [ ] Opcao de exportar para CSV
- [ ] Comando: `python main.py backtest`

**Dependencias:** BE-016

**Paralelo com:** Nenhuma

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Baixa

---

### FE-009: Adicionar grafico ASCII de PnL no dashboard

**Descricao:**
Exibir mini-grafico de evolucao do PnL nas ultimas 24h/7d.

**Criterios de Aceite:**
- [ ] Grafico ASCII usando caracteres Unicode (blocos)
- [ ] Largura: 30 caracteres, altura: 5 linhas
- [ ] Eixo X: tempo (24h ou 7d, configuravel)
- [ ] Eixo Y: PnL acumulado
- [ ] Cores: verde se PnL positivo, vermelho se negativo
- [ ] Tecla G: Toggle grafico on/off (economia de espaco)
- [ ] Atualiza a cada trade completado

**Dependencias:** BE-001 (dados do banco)

**Paralelo com:** FE-001

**Complexidade:** M

**Sprint:** 1

**Prioridade:** Media

---

### FE-010: Melhorar alertas visuais para eventos criticos

**Descricao:**
Aprimorar feedback visual para eventos importantes alem dos alertas sonoros.

**Criterios de Aceite:**
- [ ] Flash na borda do terminal ao executar ordem
- [ ] Cor de fundo muda brevemente em TP atingido (verde)
- [ ] Cor de fundo muda em erro de margem (vermelho)
- [ ] Notificacao toast para mudanca de estado do grid
- [ ] Contador de eventos na ultima hora
- [ ] Configuracao `VISUAL_ALERTS_ENABLED=true`

**Dependencias:** Nenhuma

**Paralelo com:** FE-001, FE-002

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Media

---

### FE-011: Implementar modo compacto do dashboard

**Descricao:**
Versao reduzida do dashboard para terminais pequenos.

**Criterios de Aceite:**
- [ ] Tecla C: Toggle modo compacto
- [ ] Modo compacto mostra apenas:
  - Preco atual
  - Estado do grid
  - PnL total
  - Posicoes abertas (count)
  - Ordens pendentes (count)
- [ ] Auto-detectar tamanho do terminal
- [ ] Se terminal < 80 colunas, usar modo compacto por padrao
- [ ] Transicao suave entre modos

**Dependencias:** Nenhuma

**Paralelo com:** FE-010

**Complexidade:** P

**Sprint:** 1

**Prioridade:** Media

---

### FE-012: Interface Web - Arquitetura base (RF21)

**Descricao:**
Criar arquitetura base para interface web como alternativa ao terminal.

**Criterios de Aceite:**
- [ ] Framework: FastAPI para backend API
- [ ] Frontend: React ou Vue.js (escolher)
- [ ] Estrutura de pastas: `web/backend`, `web/frontend`
- [ ] API REST para dados do bot:
  - GET /api/status - estado atual
  - GET /api/positions - posicoes abertas
  - GET /api/trades - historico de trades
  - GET /api/stats - estatisticas
  - POST /api/control - controles (ativar, pausar)
- [ ] WebSocket para atualizacoes em tempo real
- [ ] Autenticacao basica (API key)
- [ ] Documentacao Swagger/OpenAPI

**Dependencias:** BE-001 (para dados)

**Paralelo com:** Nenhuma (projeto separado)

**Complexidade:** G

**Sprint:** 5

**Prioridade:** Baixa

---

### FE-013: Interface Web - Dashboard principal

**Descricao:**
Implementar dashboard principal da interface web.

**Criterios de Aceite:**
- [ ] Layout responsivo (desktop e mobile)
- [ ] Componentes:
  - Card de preco atual com atualizacao em tempo real
  - Card de estado do grid (com cores)
  - Tabela de posicoes abertas
  - Tabela de ordens pendentes
  - Grafico de PnL (linha)
  - Estatisticas agregadas
- [ ] Dark mode por padrao
- [ ] Refresh automatico via WebSocket
- [ ] Indicador de conexao com bot

**Dependencias:** FE-012

**Paralelo com:** FE-014

**Complexidade:** G

**Sprint:** 5

**Prioridade:** Baixa

---

### FE-014: Interface Web - Controles e configuracao

**Descricao:**
Implementar controles e tela de configuracao na interface web.

**Criterios de Aceite:**
- [ ] Botoes de controle:
  - Ativar ciclo
  - Desativar ciclo
  - Pausar bot
  - Parar bot (com confirmacao)
- [ ] Formulario de configuracao:
  - Parametros de grid (spacing, range, TP)
  - Parametros de MACD
  - Indicadores ativos
- [ ] Salvar configuracao como preset (DB-003)
- [ ] Carregar preset salvo
- [ ] Validacao de inputs
- [ ] Confirmacao para acoes destrutivas

**Dependencias:** FE-012, DB-003

**Paralelo com:** FE-013

**Complexidade:** M

**Sprint:** 5

**Prioridade:** Baixa

---

### FE-015: Adicionar suporte a temas no terminal

**Descricao:**
Permitir customizar cores do dashboard terminal.

**Criterios de Aceite:**
- [ ] Arquivo de configuracao `themes.yaml`
- [ ] Temas pre-definidos: dark, light, matrix, ocean
- [ ] Parametro `DASHBOARD_THEME=dark` no .env
- [ ] Cores configuraveis:
  - Background
  - Text
  - Success (verde)
  - Error (vermelho)
  - Warning (amarelo)
  - Accent
- [ ] Tecla Shift+T: Alternar entre temas

**Dependencias:** Nenhuma

**Paralelo com:** FE-010, FE-011

**Complexidade:** P

**Sprint:** 2

**Prioridade:** Baixa

---

## Grafico de Dependencias

```
Sprint 0.5:
BE-001/BE-003 ---> FE-001 (Dashboard banco)

Sprint 1:
BE-006 ---> FE-002 (Hits por nivel)
            FE-009 (Grafico PnL)
            FE-010 (Alertas visuais)
            FE-011 (Modo compacto)

Sprint 2:
BE-009 ---> FE-003 (Indicador tendencia)
            FE-015 (Temas)

Sprint 3:
BE-010 ---> FE-004 (Ordens virtuais)

Sprint 4:
BE-011/12/13 ---> FE-005 (Indicadores tecnicos)
              |-> FE-007 (Controles teclado)

Sprint 5:
BE-014 ---> FE-006 (Long/Short)
BE-016 ---> FE-008 (Backtest)

            FE-012 (Web base) ---> FE-013 (Web dashboard)
                              |-> FE-014 (Web controles)
```

---

## Ordem de Implementacao Sugerida

### Sprint 0.5
1. FE-001 - Dashboard com dados do banco

### Sprint 1
2. FE-002 - Secao hits por nivel
3. FE-009 - Grafico ASCII de PnL
4. FE-010 - Alertas visuais
5. FE-011 - Modo compacto

### Sprint 2
6. FE-003 - Indicador de tendencia
7. FE-015 - Suporte a temas

### Sprint 3
8. FE-004 - Ordens virtuais no dashboard

### Sprint 4
9. FE-005 - Indicadores tecnicos
10. FE-007 - Controles de teclado para filtros

### Sprint 5
11. FE-006 - Posicoes Long/Short
12. FE-008 - Tela de backtest
13. FE-012 - Interface Web base
14. FE-013 - Web dashboard
15. FE-014 - Web controles

---

## Tarefas Paralelas por Sprint

### Sprint 0.5
- FE-001 pode rodar em paralelo com DB-009, DB-010, DB-011

### Sprint 1
- FE-002, FE-009, FE-010, FE-011 podem rodar em paralelo

### Sprint 2
- FE-003 e FE-015 podem rodar em paralelo

### Sprint 4
- FE-005 e FE-007 podem rodar em paralelo

### Sprint 5
- FE-012, FE-013, FE-014 sao sequenciais
- FE-006 e FE-008 podem rodar em paralelo com web

---

## Consideracoes de UX

### Dashboard Terminal
- Manter interface limpa e nao poluida
- Informacoes mais importantes no topo
- Cores consistentes em todo o sistema
- Feedback imediato para acoes do usuario

### Interface Web
- Mobile-first design
- Carregamento rapido (lazy loading)
- Offline-capable (PWA)
- Acessibilidade (WCAG 2.1)

### Acessibilidade
- Cores com contraste adequado
- Nao depender apenas de cores para informacoes
- Atalhos de teclado para todas as acoes

---

*Documento gerado em 22/12/2025*
