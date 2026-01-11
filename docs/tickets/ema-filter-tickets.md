# EMA Filter - Tickets

## Fase 1: Infraestrutura Backend EMA Filter

### Título
`feat(filters): add EMA filter backend infrastructure`

### Descrição

Implementar a infraestrutura backend para o filtro EMA (Exponential Moving Average), que será usado em conjunto com o MACD para criar o setup Impulse System do Alexander Elder.

O EMA filter permite:
- Configurar o período da EMA (ex: 13)
- Definir o timeframe do cálculo
- Decidir o comportamento quando a EMA está subindo ou descendo
- Ativar/desativar independentemente do MACD filter

### Contexto

Este filtro faz parte de uma refatoração maior do sistema de gatilhos:
- A regra atual "ambas linhas MACD e Signal < 0" será substituída pela direção da EMA
- O estado WAIT será removido (Fase 3)
- MACD e EMA funcionarão como filtros independentes no FilterRegistry

### Critérios de Aceite

- [ ] Modelo `EMAFilterConfig` criado com campos: `enabled`, `period`, `timeframe`, `allow_on_rising`, `allow_on_falling`
- [ ] Migração Alembic para tabela `ema_filter_configs`
- [ ] Relacionamento one-to-one com `Strategy` (via `strategy_id`)
- [ ] `EMAFilterConfigRepository` com métodos CRUD
- [ ] Schemas Pydantic: `EMAFilterConfigResponse`, `EMAFilterConfigUpdateRequest`
- [ ] Endpoints API:
  - `GET /api/v1/strategies/{id}/ema-filter`
  - `PATCH /api/v1/strategies/{id}/ema-filter`
- [ ] Classe `EMAFilter` implementando interface `Filter`
- [ ] Método `update(klines)` que calcula EMA e determina direção
- [ ] Método `should_protect_orders()` que retorna `True` se EMA subindo
- [ ] Testes unitários com cobertura adequada
- [ ] `ruff check`, `ruff format`, `mypy` passando
- [ ] `pytest` passando

### Especificação Técnica

#### Modelo de Dados

```python
class EMAFilterConfig(Base):
    __tablename__ = "ema_filter_configs"

    id: Mapped[UUID]
    strategy_id: Mapped[UUID]  # FK unique para strategies
    enabled: Mapped[bool] = True
    period: Mapped[int] = 13
    timeframe: Mapped[str] = "1h"
    allow_on_rising: Mapped[bool] = True
    allow_on_falling: Mapped[bool] = False
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

#### Classe EMAFilter

```python
class EMADirection(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    FLAT = "flat"

class EMAFilter(Filter):
    def __init__(self, period: int = 13, ...)
    def update(self, klines: list) -> None
    def should_allow_trade(self) -> bool
    def should_protect_orders(self) -> bool
    def get_state(self) -> FilterState
    async def load_config_from_db(self, strategy_id: UUID) -> None
```

#### Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/strategies/{id}/ema-filter` | Retorna config atual |
| PATCH | `/api/v1/strategies/{id}/ema-filter` | Atualiza config |

### Arquivos a Criar

```
src/database/models/ema_filter_config.py
src/database/repositories/ema_filter_config_repository.py
src/filters/ema_filter.py
tests/test_ema_filter.py
tests/test_ema_filter_config_repository.py
alembic/versions/xxxx_add_ema_filter_config.py
```

### Arquivos a Modificar

```
src/database/models/__init__.py          # Export EMAFilterConfig
src/database/models/strategy.py          # Add relationship
src/database/repositories/__init__.py    # Export repository
src/api/schemas/strategy.py              # Add EMA schemas
src/api/routes/strategy.py               # Add endpoints
src/filters/__init__.py                  # Export EMAFilter
```

### Não Inclui (próximas fases)

- Integração com GridManager (Fase 4)
- Componente frontend EMAFilterSection (Fase 2)
- Remoção do estado WAIT (Fase 3)
- Broadcast WebSocket (Fase 4)

### Labels

`enhancement`, `backend`, `filters`

---

## Fase 2: Frontend EMA Filter

### Título
`feat(frontend): add EMA filter configuration section`

### Descrição

Implementar o componente frontend para configuração do filtro EMA, seguindo o mesmo padrão do `MACDFilterSection`. O componente será exibido na página de edição de estratégia e permitirá configurar os parâmetros do EMA filter.

### Contexto

Este ticket depende da Fase 1 (backend) estar concluída para os endpoints API funcionarem. O componente segue o padrão existente:
- Seção colapsável
- Toggle de ativar/desativar
- Campos de configuração
- Botões Save/Reset independentes

### Critérios de Aceite

- [ ] Types `EMAFilterConfigResponse` e `EMAFilterConfigUpdateRequest` em `api.ts`
- [ ] Hook `useEMAFilterConfig(strategyId)` para fetch da config
- [ ] Hook `useUpdateEMAFilterConfig(strategyId)` para mutation
- [ ] Componente `EMAFilterSection.tsx` com:
  - Toggle enabled/disabled
  - Input numérico para period (1-200, default 13)
  - Select para timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
  - Checkbox "Allow trades when EMA rising"
  - Checkbox "Allow trades when EMA falling"
  - Botões Save/Reset
- [ ] Validação: period deve ser >= 1 e <= 200
- [ ] Loading states enquanto salva
- [ ] Toast de sucesso/erro ao salvar
- [ ] Integração no `StrategyEditPage.tsx`
- [ ] Responsivo (mobile-friendly)

### Especificação Técnica

#### Types

```typescript
// frontend/src/types/api.ts

export interface EMAFilterConfigResponse {
  id: string
  strategyId: string
  enabled: boolean
  period: number
  timeframe: MACDTimeframe  // Reutiliza enum existente
  allowOnRising: boolean
  allowOnFalling: boolean
  createdAt: string
  updatedAt: string
}

export interface EMAFilterConfigUpdateRequest {
  enabled?: boolean
  period?: number
  timeframe?: MACDTimeframe
  allowOnRising?: boolean
  allowOnFalling?: boolean
}
```

#### Hooks

```typescript
// frontend/src/hooks/useStrategies.ts

export function useEMAFilterConfig(strategyId: string)
export function useUpdateEMAFilterConfig(strategyId: string)
```

#### Componente

```typescript
// frontend/src/components/Strategy/EMAFilterSection.tsx

interface EMAFilterSectionProps {
  strategyId: string
}

export function EMAFilterSection({ strategyId }: EMAFilterSectionProps)
```

### UI Design

```
┌─────────────────────────────────────────────────────────────┐
│ ▼ EMA Filter                                     [Toggle]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Period                    Timeframe                        │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │       13         │      │ 1h                    ▼  │    │
│  └──────────────────┘      └──────────────────────────┘    │
│  EMA period (1-200)                                         │
│                                                             │
│  Trading Behavior                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Allow trades when EMA is rising                   │   │
│  │ ☐ Allow trades when EMA is falling                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  Configure when the bot can create new orders              │
│                                                             │
│                              [Reset]    [Save Changes]      │
└─────────────────────────────────────────────────────────────┘
```

**Estados visuais:**
- Seção colapsada por padrão (consistente com MACD)
- Toggle desabilitado → campos em disabled/opacity reduzida
- Botão Save desabilitado se não houver mudanças
- Loading spinner no botão durante save

### Arquivos a Criar

```
frontend/src/components/Strategy/EMAFilterSection.tsx
```

### Arquivos a Modificar

```
frontend/src/types/api.ts                    # Add EMA types
frontend/src/hooks/useStrategies.ts          # Add EMA hooks
frontend/src/pages/StrategyEditPage.tsx      # Add EMAFilterSection
frontend/src/components/Strategy/index.ts    # Export component (se existir)
```

### Dependências

- **Fase 1** (backend) deve estar completa
- Endpoints `GET/PATCH /api/v1/strategies/{id}/ema-filter` funcionando

### Referência de Implementação

Seguir o padrão de `MACDFilterSection.tsx`:
- Mesma estrutura de estado local
- Mesmo padrão de hooks (useQuery/useMutation)
- Mesmo estilo visual (Tailwind/shadcn)
- Mesma lógica de dirty state para Reset

### Não Inclui (próximas fases)

- Exibição da direção atual da EMA no Dashboard (Fase 5)
- Indicador visual de EMA rising/falling em tempo real (Fase 5)

### Labels

`enhancement`, `frontend`, `filters`
