# Filter System

Sistema de filtros plugáveis para controle de entrada de ordens no grid trading.

## Visão Geral

O sistema de filtros permite ativar/desativar indicadores técnicos dinamicamente via API HTTP, sem necessidade de reiniciar o bot.

**Comportamento:**
- Filtros habilitados por padrão no startup
- Estado volátil (não persiste entre restarts)
- Quando **todos** filtros desativados: bot cria ordens apenas baseado em preço e MAX_ORDERS
- Quando **qualquer** filtro ativo: ordem só é criada se TODOS os filtros ativos aprovarem

## Arquitetura

### Componentes

1. **Filter (Base Class)** - Interface abstrata para filtros
2. **FilterRegistry (Singleton)** - Gerenciador centralizado de filtros
3. **MACDFilter** - Filtro baseado na estratégia MACD existente
4. **HealthServer Endpoints** - API HTTP para controle via REST

### Fluxo de Decisão

```
GridManager.update()
  ↓
MACDStrategy.get_state() → calcula estado atual
  ↓
MACDFilter.set_current_state() → atualiza filtro
  ↓
FilterRegistry.should_allow_trade()
  ├─ Nenhum filtro ativo? → TRUE (permite)
  ├─ Todos filtros ativos permitem? → TRUE
  └─ Qualquer filtro bloqueia? → FALSE
  ↓
GridManager._create_grid_orders() ou skip
```

## API HTTP

### Endpoint: GET /filters

Retorna estado de todos os filtros.

**Response (200 OK):**
```json
{
  "filters": {
    "macd": {
      "enabled": true,
      "description": "MACD Crossover Strategy",
      "details": {
        "current_state": "activate",
        "cycle_activated": true,
        "state_description": "🟢 ATIVANDO - Vermelho claro + MACD negativo"
      }
    }
  },
  "all_enabled": true,
  "any_enabled": true,
  "total_count": 1,
  "enabled_count": 1
}
```

### Endpoint: POST /filters/{filter_name}

Ativa ou desativa um filtro específico.

**Request Body:**
```json
{
  "enabled": false
}
```

**Response (200 OK):**
```json
{
  "filter": "macd",
  "enabled": false,
  "message": "Filter macd disabled",
  "details": {
    "current_state": "activate",
    "cycle_activated": true
  }
}
```

**Erros:**
- `404 Not Found` - Filtro não encontrado
- `400 Bad Request` - JSON inválido ou campo 'enabled' ausente

### Endpoint: POST /filters/disable-all

Desativa todos os filtros de uma vez.

**Response (200 OK):**
```json
{
  "message": "All filters disabled",
  "filters": ["macd"]
}
```

### Endpoint: POST /filters/enable-all

Reativa todos os filtros (volta ao estado default).

**Response (200 OK):**
```json
{
  "message": "All filters enabled",
  "filters": ["macd"]
}
```

## Uso via curl

```bash
# Ver filtros ativos
curl http://localhost:8080/filters

# Desativar MACD
curl -X POST http://localhost:8080/filters/macd \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Desativar todos (bot cria ordens sem validação de indicador)
curl -X POST http://localhost:8080/filters/disable-all

# Reativar todos (volta ao default)
curl -X POST http://localhost:8080/filters/enable-all
```

## Logs

O sistema registra logs quando filtros são ativados/desativados:

```
INFO - FilterRegistry initialized
INFO - Filter registered: macd - MACD Crossover Strategy
INFO - Filter disabled: macd
INFO - All filters disabled
INFO - Nenhum filtro ativo - criando ordens apenas com base no preço e MAX_ORDERS
INFO - Filter enabled: macd
```

## Criar Novo Filtro

Para adicionar um novo indicador técnico:

1. **Criar classe herdando Filter:**

```python
from src.filters.base import Filter, FilterState

class RSIFilter(Filter):
    def __init__(self, period: int = 14):
        super().__init__(
            name="rsi",
            description="RSI Oversold/Overbought"
        )
        self.period = period
        self.current_rsi = 0.0

    def should_allow_trade(self) -> bool:
        if not self.enabled:
            return True

        # Bloqueia se RSI > 70 (sobrecomprado)
        return self.current_rsi < 70

    def get_state(self) -> FilterState:
        return FilterState(
            enabled=self.enabled,
            description=self.description,
            details={"rsi": self.current_rsi}
        )
```

2. **Registrar no GridManager:**

```python
# Em grid_manager.py
self._rsi_filter = RSIFilter()
self._filter_registry.register(self._rsi_filter)
```

3. **Atualizar estado no update loop:**

```python
# Calcular RSI
rsi_value = calculate_rsi(klines)
self._rsi_filter.current_rsi = rsi_value
```

4. **Adicionar aos exports:**

```python
# Em src/filters/__init__.py
from src.filters.rsi_filter import RSIFilter

__all__ = ["Filter", "FilterRegistry", "MACDFilter", "RSIFilter"]
```

## Persistência (Futura)

**Atual:** Estado volátil - filtros voltam ao padrão (enabled=true) no restart.

**BE-023:** Implementará persistência em banco PostgreSQL para manter estado entre restarts.

## Testes

```bash
# Testes unitários (25 testes)
pytest tests/test_filters.py -v

# Testes de API (11 testes)
pytest tests/test_filters_api.py -v

# Todos os testes de filtros
pytest tests/test_filters*.py -v
```

**Cobertura:**
- Classe base Filter
- FilterRegistry (singleton, registro, enable/disable)
- MACDFilter (integração com MACDStrategy)
- Endpoints HTTP (GET, POST, error handling)
- Workflows completos (disable one, disable all, enable all)
- Persistência volátil (reset on restart)

## Referências

- **Task:** BE-022
- **Dependências:** Nenhuma
- **Próxima:** BE-023 (persistência em DB)
- **Arquivos:**
  - `src/filters/base.py` - Interface Filter
  - `src/filters/registry.py` - FilterRegistry singleton
  - `src/filters/macd_filter.py` - Implementação MACD
  - `src/health/health_server.py` - Endpoints HTTP
  - `src/grid/grid_manager.py` - Integração
  - `tests/test_filters.py` - Testes unitários
  - `tests/test_filters_api.py` - Testes de API
