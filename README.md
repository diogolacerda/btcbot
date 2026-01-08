# BTC Grid Bot

[![CI](https://github.com/diogolacerda/btcbot/actions/workflows/ci.yml/badge.svg)](https://github.com/diogolacerda/btcbot/actions/workflows/ci.yml)

Bot de trading automatizado usando estrategia de Grid para BTC-USDT na BingX.

> 🚀 CI/CD powered by 9 self-hosted runners on homeserver (optimized for <1min CI)

## Requisitos

- Python 3.12+
- Docker (para deploy)

## Instalacao

```bash
# Clonar repositorio
git clone https://github.com/diogolacerda/btcbot.git
cd btcbot

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Para desenvolvimento
pip install -r requirements-dev.txt
```

## Configuracao

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

## Execucao

```bash
# Local
python main.py

# Docker
docker build -t btcbot .
docker run --env-file .env btcbot
```

## Desenvolvimento

```bash
# Lint e formatacao
ruff check .
ruff format .

# Type check
mypy .

# Testes
pytest
```

## Documentacao

- [GitFlow](docs/GITFLOW.md) - Fluxo de trabalho
- [Homeserver Setup](docs/HOMESERVER_SETUP.md) - Configuracao do servidor
- [Secrets](docs/SECRETS.md) - Configuracao de secrets

## Licenca

Projeto privado - Todos os direitos reservados.
