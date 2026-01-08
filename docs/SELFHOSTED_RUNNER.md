# Self-Hosted Runner Configuration

**Última atualização:** 2026-01-08
**Versão Runner:** v2.321.0
**Total de Runners:** 9
**Status:** ✅ Produção

## Visão Geral

GitHub Actions Self-Hosted Runners configurados no homeserver (192.168.68.99) para executar workflows de CI/CD localmente, alcançando performance superior e custo zero.

## Especificações do Homeserver

| Item | Valor |
|------|-------|
| **IP Local** | 192.168.68.99 |
| **OS** | Ubuntu 24.04.3 LTS |
| **CPU** | Intel Core i5-4590 @ 3.30GHz (4 cores) |
| **RAM** | 17GB total (~15GB disponível) |
| **Docker** | 27.5.1 |
| **Python** | 3.12.12 |
| **Node.js** | 20.19.6 |
| **npm** | 10.8.2 |

## Configuração dos Runners

### Estrutura

```
/home/github-runner/
├── actions-runner/          # Runner 1 (homeserver-runner)
├── actions-runner-2/        # Runner 2
├── actions-runner-3/        # Runner 3
├── actions-runner-4/        # Runner 4
├── actions-runner-5/        # Runner 5
├── actions-runner-6/        # Runner 6
├── actions-runner-7/        # Runner 7
├── actions-runner-8/        # Runner 8
└── actions-runner-9/        # Runner 9
```

### Detalhes de Cada Runner

| Runner | Path | Service Name | Labels |
|--------|------|--------------|--------|
| homeserver-runner | `/home/github-runner/actions-runner` | `actions.runner.diogolacerda-btcbot.homeserver-runner` | self-hosted, linux, docker |
| homeserver-runner-2 | `/home/github-runner/actions-runner-2` | `actions.runner.diogolacerda-btcbot.homeserver-runner-2` | self-hosted, linux, docker |
| homeserver-runner-3 | `/home/github-runner/actions-runner-3` | `actions.runner.diogolacerda-btcbot.homeserver-runner-3` | self-hosted, linux, docker |
| homeserver-runner-4 | `/home/github-runner/actions-runner-4` | `actions.runner.diogolacerda-btcbot.homeserver-runner-4` | self-hosted, linux, docker |
| homeserver-runner-5 | `/home/github-runner/actions-runner-5` | `actions.runner.diogolacerda-btcbot.homeserver-runner-5` | self-hosted, linux, docker |
| homeserver-runner-6 | `/home/github-runner/actions-runner-6` | `actions.runner.diogolacerda-btcbot.homeserver-runner-6` | self-hosted, linux, docker |
| homeserver-runner-7 | `/home/github-runner/actions-runner-7` | `actions.runner.diogolacerda-btcbot.homeserver-runner-7` | self-hosted, linux, docker |
| homeserver-runner-8 | `/home/github-runner/actions-runner-8` | `actions.runner.diogolacerda-btcbot.homeserver-runner-8` | self-hosted, linux, docker |
| homeserver-runner-9 | `/home/github-runner/actions-runner-9` | `actions.runner.diogolacerda-btcbot.homeserver-runner-9` | self-hosted, linux, docker |

### Usuário e Permissões

- **User:** `github-runner`
- **Groups:** `github-runner`, `docker`
- **Home:** `/home/github-runner`
- **Shell:** `/bin/bash`

## Workflows Suportados

| Workflow | Uso Self-Hosted | Performance | Status |
|----------|-----------------|-------------|--------|
| **CI** | ✅ 9 runners | **65s** (< 1 min) | ✅ Produção |
| **CD Stage (Backend)** | ✅ | **77-120s** (2 min) | ✅ Produção |
| **CD Stage Frontend** | ✅ | **72s** | ✅ Produção |

### Comparação com GitHub Cloud Runners

| Métrica | Cloud Runners | Self-Hosted (9 runners) | Melhoria |
|---------|---------------|-------------------------|----------|
| **CI Time** | ~240s (4 min) | **65s** | **73% mais rápido** ⚡ |
| **CD Time** | ~324s (5.4 min) | **77-120s** | **63-76% mais rápido** ⚡ |
| **Custo/mês** | ~$100 | **$0** | **100% economia** 💰 |
| **Queue time** | Variável | **~0s** (9 runners) | Eliminado ✅ |

## Performance e Otimizações

### Otimizações Aplicadas

1. **9 Runners Paralelos**
   - Eliminação de queue overhead
   - Máximo paralelismo para os 9 jobs do CI

2. **Local Pip Cache**
   - Pip cache em `~/.cache/pip` (persistente)
   - Eliminou 53s de download do GitHub Actions cache
   - Setup Python: 127s → 42s

3. **pytest-xdist**
   - Testes paralelos com `-n auto`
   - Tests: 90s → 64s (29% mais rápido)

4. **Parallel Execution**
   - `ruff check . & ruff format . & wait`
   - `npm run lint & npx tsc --noEmit & wait`

5. **Docker Cache Otimizado**
   - Registry cache: `type=registry,ref=diogorlm/btcbot:stage`
   - Local cache: `type=local,src=/tmp/.buildx-cache`
   - Inline cache: `type=inline`
   - Docker Build: 254s → 69s (73% mais rápido)

### Jobs Separados vs Consolidados

✅ **Estratégia Atual: Jobs Separados**

Mantemos 9 jobs separados (lint, typecheck, test, build, etc.) ao invés de consolidar porque:
- Com 9 runners, todos executam em paralelo
- Total time = MAX(jobs) não SUM(jobs)
- Setup overhead é paralelo, não sequencial

❌ **Tentado e Descartado: Job Consolidation**

Tentamos consolidar em 3 jobs mas performance piorou:
- Setup sequencial (checkout + python + deps) para cada job consolidado
- Perda de paralelismo
- 65s → 165s (159% mais lento)

## Comandos Úteis

### Status e Monitoramento

```bash
# Verificar status de todos os runners
ssh diogo@192.168.68.99 "sudo systemctl list-units 'actions.runner*' --no-pager"

# Verificar apenas runners ativos
ssh diogo@192.168.68.99 "sudo systemctl list-units 'actions.runner*' --no-pager | grep 'active running'"

# Ver logs de um runner específico
ssh diogo@192.168.68.99 "sudo journalctl -u actions.runner.diogolacerda-btcbot.homeserver-runner -f"

# Ver logs de todos os runners
ssh diogo@192.168.68.99 "sudo journalctl -u 'actions.runner*' -f"

# Verificar recursos do sistema
ssh diogo@192.168.68.99 "free -h"        # RAM
ssh diogo@192.168.68.99 "df -h"          # Disco
ssh diogo@192.168.68.99 "uptime"         # Load average
ssh diogo@192.168.68.99 "docker ps"      # Containers rodando
```

### Gerenciamento de Runners

```bash
# Reiniciar runner específico
ssh diogo@192.168.68.99 "sudo systemctl restart actions.runner.diogolacerda-btcbot.homeserver-runner-2"

# Reiniciar todos os runners
ssh diogo@192.168.68.99 "sudo systemctl restart 'actions.runner*'"

# Parar todos os runners
ssh diogo@192.168.68.99 "sudo systemctl stop 'actions.runner*'"

# Iniciar todos os runners
ssh diogo@192.168.68.99 "sudo systemctl start 'actions.runner*'"

# Verificar status de runner específico
ssh diogo@192.168.68.99 "sudo systemctl status actions.runner.diogolacerda-btcbot.homeserver-runner"
```

### Verificação de Cache

```bash
# Verificar cache pip
ssh diogo@192.168.68.99 "du -sh /home/github-runner/.cache/pip"

# Limpar cache pip (se necessário)
ssh diogo@192.168.68.99 "rm -rf /home/github-runner/.cache/pip/*"

# Verificar cache Docker buildx
ssh diogo@192.168.68.99 "du -sh /tmp/.buildx-cache*"

# Limpar cache Docker (se necessário)
ssh diogo@192.168.68.99 "docker builder prune -a"
```

## Troubleshooting

### Problema: Runner Offline

**Sintomas:**
- Dashboard GitHub mostra runner offline
- Workflows ficam em queue

**Solução:**
```bash
# 1. Verificar se service está rodando
ssh diogo@192.168.68.99 "sudo systemctl status actions.runner.diogolacerda-btcbot.homeserver-runner"

# 2. Se stopped, iniciar
ssh diogo@192.168.68.99 "sudo systemctl start actions.runner.diogolacerda-btcbot.homeserver-runner"

# 3. Verificar logs
ssh diogo@192.168.68.99 "sudo journalctl -u actions.runner.diogolacerda-btcbot.homeserver-runner -n 50"
```

### Problema: Buildx Connection Errors

**Sintomas:**
```
ERROR: failed to solve: Unavailable: closing transport due to: connection error
```

**Causa:**
- Parâmetros `install: true` e `driver-opts: network=host` no setup-buildx-action são incompatíveis com self-hosted runners

**Solução:**
- Usar configuração padrão do buildx sem parâmetros extras:
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

### Problema: GitHub Actions Cache Lento

**Sintomas:**
- Setup Python leva 50-100s
- Download em 2-3 MBs/sec do GitHub Actions cache

**Solução:**
- Remover `cache: 'pip'` do setup-python
- Usar cache local pip automático em `~/.cache/pip`
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    # Removido: cache: 'pip'
```

### Problema: RAM Insuficiente

**Sintomas:**
- Runners crashando
- OOM (Out of Memory) em logs

**Diagnóstico:**
```bash
ssh diogo@192.168.68.99 "free -h"
ssh diogo@192.168.68.99 "ps aux --sort=-%mem | head -20"
```

**Solução:**
- Reduzir número de runners simultâneos
- Adicionar swap se necessário
- Monitorar com `htop`

### Problema: Disk Space Full

**Diagnóstico:**
```bash
ssh diogo@192.168.68.99 "df -h"
ssh diogo@192.168.68.99 "du -sh /home/github-runner/*"
```

**Solução:**
```bash
# Limpar Docker
ssh diogo@192.168.68.99 "docker system prune -a -f"

# Limpar cache buildx
ssh diogo@192.168.68.99 "rm -rf /tmp/.buildx-cache*"

# Limpar logs antigos
ssh diogo@192.168.68.99 "sudo journalctl --vacuum-time=7d"
```

## Adicionando Novos Runners

Para adicionar mais runners (ex: runner-10):

```bash
# 1. Gerar token no GitHub
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/diogolacerda/btcbot/actions/runners/registration-token \
  --jq '.token'

# 2. No homeserver, criar diretório e baixar runner
ssh diogo@192.168.68.99
sudo mkdir -p /home/github-runner/actions-runner-10
sudo chown -R github-runner:github-runner /home/github-runner/actions-runner-10

sudo -u github-runner bash -c 'cd /home/github-runner/actions-runner-10 && \
  curl -o actions-runner-linux-x64-2.321.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz && \
  tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz'

# 3. Configurar runner (substituir <TOKEN>)
sudo -u github-runner bash -c 'cd /home/github-runner/actions-runner-10 && \
  ./config.sh --url https://github.com/diogolacerda/btcbot \
  --token <TOKEN> \
  --name homeserver-runner-10 \
  --labels self-hosted,linux,docker \
  --work _work'

# 4. Instalar e iniciar service
cd /home/github-runner/actions-runner-10
sudo ./svc.sh install github-runner
sudo ./svc.sh start

# 5. Verificar
sudo systemctl status actions.runner.diogolacerda-btcbot.homeserver-runner-10
```

## Removendo Runners

Para remover um runner:

```bash
# 1. Parar service
ssh diogo@192.168.68.99 "sudo systemctl stop actions.runner.diogolacerda-btcbot.homeserver-runner-X"

# 2. Desinstalar service
ssh diogo@192.168.68.99 "cd /home/github-runner/actions-runner-X && sudo ./svc.sh uninstall"

# 3. Remover configuração no GitHub
ssh diogo@192.168.68.99 "sudo -u github-runner bash -c 'cd /home/github-runner/actions-runner-X && ./config.sh remove'"

# 4. Remover diretório
ssh diogo@192.168.68.99 "sudo rm -rf /home/github-runner/actions-runner-X"
```

## Atualização de Runners

Para atualizar versão do runner:

```bash
# 1. Verificar versão disponível
# https://github.com/actions/runner/releases

# 2. Para cada runner:
RUNNER_NUM=2  # Ajustar para cada runner

ssh diogo@192.168.68.99 "
  sudo systemctl stop actions.runner.diogolacerda-btcbot.homeserver-runner-${RUNNER_NUM}
  cd /home/github-runner/actions-runner-${RUNNER_NUM}
  sudo -u github-runner ./config.sh remove

  # Baixar nova versão
  sudo -u github-runner curl -o actions-runner-linux-x64-2.XXX.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.XXX.0/actions-runner-linux-x64-2.XXX.0.tar.gz
  sudo -u github-runner tar xzf ./actions-runner-linux-x64-2.XXX.0.tar.gz

  # Reconfigurar (gerar novo token)
  sudo -u github-runner ./config.sh --url https://github.com/diogolacerda/btcbot --token <NEW_TOKEN> --name homeserver-runner-${RUNNER_NUM} --labels self-hosted,linux,docker --work _work

  # Reinstalar service
  sudo ./svc.sh install github-runner
  sudo ./svc.sh start
"
```

## Monitoramento e Dashboards

### GitHub Dashboard

- **Runners:** https://github.com/diogolacerda/btcbot/settings/actions/runners
- **Workflows:** https://github.com/diogolacerda/btcbot/actions
- **Insights:** https://github.com/diogolacerda/btcbot/pulse

### Métricas de Performance

Monitorar regularmente:

```bash
# CI time médio (deve estar < 70s)
gh run list --workflow=ci.yml --limit 10 --json createdAt,updatedAt,conclusion

# CD time médio (deve estar < 120s)
gh run list --workflow=cd-stage.yml --limit 10 --json createdAt,updatedAt,conclusion

# Runners online
gh api /repos/diogolacerda/btcbot/actions/runners --jq '.runners[] | select(.status == "online") | .name'
```

## Links Úteis

- [GitHub Actions Self-Hosted Runners Docs](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Runner Releases](https://github.com/actions/runner/releases)
- [Troubleshooting](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/monitoring-and-troubleshooting-self-hosted-runners)
- Homeserver Setup: `docs/HOMESERVER_SETUP.md`
- Git Workflow: `docs/GITFLOW.md`

## Histórico de Mudanças

| Data | Mudança | Impacto |
|------|---------|---------|
| 2026-01-08 | Inicial: 3 runners | CI: 2m 52s |
| 2026-01-08 | Upgrade: 5 runners | CI: 1m 59s |
| 2026-01-08 | Upgrade: 9 runners | CI: 65s (< 1 min) ✅ |
| 2026-01-08 | Local pip cache | Setup Python: 127s → 42s |
| 2026-01-08 | pytest-xdist | Tests: 90s → 64s |
| 2026-01-08 | Revert buildx reuse | CD: Stability restored |

---

**Mantido por:** DevOps Team
**Próxima revisão:** Trimestral ou quando adicionar/remover runners
