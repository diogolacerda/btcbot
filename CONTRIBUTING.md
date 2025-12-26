# Guia de Contribuicao - BTC Grid Bot

## Fluxo de Trabalho (GitFlow)

Este projeto segue o fluxo GitFlow adaptado. Consulte [docs/GITFLOW.md](docs/GITFLOW.md) para detalhes completos.

### Branches

| Branch | Proposito |
|--------|-----------|
| `main` | Codigo de producao. Deploys automaticos para Stage. |
| `develop` | Branch de integracao (opcional para features grandes) |
| `feature/*` | Novas funcionalidades |
| `bugfix/*` | Correcoes de bugs |
| `hotfix/*` | Correcoes urgentes de producao |

### Fluxo de uma Task

```
TODO -> IN_PROGRESS -> REVIEW -> ACCEPTANCE_TESTING -> READY_TO_PROD -> DONE
```

1. **Criar branch** a partir de `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/BE-001-trade-repository
   ```

2. **Desenvolver** seguindo os criterios de aceite da task

3. **Commit** com mensagens claras:
   ```bash
   git commit -m "feat(BE-001): implement TradeRepository with CRUD operations"
   ```

4. **Push** e criar PR:
   ```bash
   git push -u origin feature/BE-001-trade-repository
   ```

5. **Code Review** - Aguardar aprovacao

6. **Merge** - Apos aprovacao, merge para main

7. **Deploy automatico** - CD Stage faz deploy automaticamente

8. **Acceptance Testing** - Testar em Stage

9. **Producao** - Apos aprovacao, CD Prod promove para producao

## Setup de Desenvolvimento

### Pre-requisitos

- Python 3.12+
- Docker e Docker Compose
- Git

### Instalacao

```bash
# Clonar repositorio
git clone https://github.com/diogolacerda/btcbot.git
cd btcbot

# Executar script de setup
./scripts/setup_dev.sh

# OU manualmente:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install pre-commit
pre-commit install
```

### Pre-commit Hooks (OBRIGATORIO)

Este projeto usa pre-commit para **BLOQUEAR** commits que nao passam nas verificacoes.
Isso garante paridade com o CI - codigo que nao passa aqui, nao passa la.

```bash
# Instalar hooks (OBRIGATORIO antes de commitar)
pip install pre-commit
pre-commit install

# Executar em todos os arquivos (util para verificar antes de commitar)
pre-commit run --all-files
```

**Hooks configurados (BLOQUEIAM commits):**

| Hook | Funcao | Bloqueia se... |
|------|--------|----------------|
| `ruff` | Linting | Erros de lint encontrados |
| `ruff-format` | Formatacao | Codigo nao formatado |
| `mypy` | Type checking | Erros de tipo encontrados |
| `detect-secrets` | Seguranca | Secrets detectados no codigo |
| `trailing-whitespace` | Limpeza | Espacos em branco no final |
| `end-of-file-fixer` | Limpeza | Arquivo sem newline final |
| `check-yaml` | Validacao | YAML invalido |
| `debug-statements` | Limpeza | print/pdb no codigo |

**IMPORTANTE:** Se o commit for bloqueado, corrija os erros antes de tentar novamente.
Alguns hooks (ruff, trailing-whitespace) corrigem automaticamente - basta `git add` novamente.

## Padroes de Codigo

### Python

- Formatacao: `ruff format`
- Linting: `ruff check`
- Type hints: Obrigatorios para funcoes publicas
- Docstrings: Google style

### Commits

Seguir Conventional Commits:

```
<type>(<scope>): <description>

[optional body]
```

Tipos:
- `feat`: Nova funcionalidade
- `fix`: Correcao de bug
- `docs`: Documentacao
- `refactor`: Refatoracao
- `test`: Testes
- `chore`: Manutencao

Exemplos:
```
feat(BE-001): add TradeRepository with PostgreSQL integration
fix(BUG-001): correct margin calculation on partial fills
docs(DEVOPS-017): add deployment documentation
```

### Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov

# Apenas testes de integracao
pytest -m integration
```

## Pull Requests

### Antes de abrir PR

- [ ] Testes passando localmente
- [ ] Pre-commit hooks passando
- [ ] Task atualizada para IN_PROGRESS
- [ ] Branch atualizada com main

### Template de PR

Use os templates em `.github/PULL_REQUEST_TEMPLATE/`:
- `feature.md` - Para novas funcionalidades
- `bugfix.md` - Para correcoes de bugs
- `hotfix.md` - Para correcoes urgentes

### Code Review

- PRs requerem pelo menos 1 aprovacao
- CI deve passar (lint, tests, build)
- Reviewer deve ser da mesma disciplina (backend, frontend, devops)

## Ambientes

| Ambiente | URL | Branch | Deploy |
|----------|-----|--------|--------|
| Stage | http://192.168.68.99:3001 | main | Automatico |
| Production | http://192.168.68.99:3000 | main | Manual |

## Duvidas

- Consulte a documentacao em `/docs`
- Verifique as tasks em `/tasks`
- Abra uma Issue para discussao
