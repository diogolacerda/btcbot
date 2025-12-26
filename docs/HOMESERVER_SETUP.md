# Setup Inicial do Homeserver - BTC Grid Bot

**Task:** DEVOPS-016
**Data:** 26 de Dezembro de 2025
**Versao:** 1.0

Este documento descreve o processo de setup inicial do homeserver para executar o BTC Grid Bot em ambientes Stage e Production.

---

## Informacoes do Homeserver

| Item | Valor |
|------|-------|
| **IP Local** | `192.168.68.99` |
| **Acesso SSH** | `ssh usuario@192.168.68.99` |
| **Portainer** | `http://192.168.68.99:9000` |
| **Stage URL** | `http://192.168.68.99:3001` |
| **Production URL** | `http://192.168.68.99:3000` |
| **Registry** | Docker Hub (`docker.io`) |

---

## Pre-requisitos

Antes de iniciar, verifique que o homeserver possui:

- [ ] Docker instalado e rodando
- [ ] Docker Compose disponivel
- [ ] Portainer rodando na porta 9000
- [ ] Watchtower configurado e rodando
- [ ] Acesso a internet para Docker Hub

---

## Passo 1: Conectar ao Homeserver

```bash
ssh usuario@192.168.68.99
```

---

## Passo 2: Verificar Docker

```bash
# Verificar versao do Docker
docker --version

# Verificar se Docker daemon esta rodando
docker info

# Verificar Docker Compose
docker compose version
```

**Resultado esperado:** Docker 20.10+ instalado e rodando.

---

## Passo 3: Verificar Portainer

```bash
# Verificar se Portainer esta rodando
docker ps --filter "name=portainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Resultado esperado:**
```
NAMES       STATUS          PORTS
portainer   Up X days       0.0.0.0:9000->9000/tcp
```

**Teste de acesso:** Abra `http://192.168.68.99:9000` no navegador.

Se Portainer nao estiver rodando:
```bash
docker run -d \
  --name=portainer \
  --restart=always \
  -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

---

## Passo 4: Verificar Watchtower

```bash
# Verificar se Watchtower esta rodando
docker ps --filter "name=watchtower" --format "table {{.Names}}\t{{.Status}}"

# Verificar configuracao do Watchtower
docker inspect watchtower --format '{{range .Config.Env}}{{println .}}{{end}}' | grep WATCHTOWER
```

**Resultado esperado:**
```
WATCHTOWER_POLL_INTERVAL=30
WATCHTOWER_CLEANUP=true
WATCHTOWER_LABEL_ENABLE=true
```

**Importante:** `WATCHTOWER_LABEL_ENABLE=true` e obrigatorio para que apenas containers com label especifica sejam atualizados automaticamente.

Se Watchtower nao estiver rodando ou configurado incorretamente:
```bash
# Parar Watchtower existente (se houver)
docker stop watchtower && docker rm watchtower

# Iniciar Watchtower com configuracao correta
docker run -d \
  --name watchtower \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e WATCHTOWER_POLL_INTERVAL=30 \
  -e WATCHTOWER_CLEANUP=true \
  -e WATCHTOWER_LABEL_ENABLE=true \
  containrrr/watchtower
```

---

## Passo 5: Verificar Conectividade com Docker Hub

```bash
# Testar pull de imagem
docker pull hello-world
docker rmi hello-world

# Verificar se esta logado no Docker Hub
docker info | grep Username
```

Se nao estiver logado:
```bash
docker login docker.io
# Inserir usuario e senha/token do Docker Hub
```

**Nota:** Recomendamos usar um Access Token ao inves de senha. Crie em: https://hub.docker.com/settings/security

---

## Passo 6: Criar Estrutura de Diretorios

```bash
# Criar diretorio base
sudo mkdir -p /opt/btcbot

# Criar subdiretorios
sudo mkdir -p /opt/btcbot/{logs-stage,logs-prod,backups/stage,backups/prod,scripts}

# Definir ownership para seu usuario
sudo chown -R $USER:$USER /opt/btcbot

# Verificar estrutura criada
ls -la /opt/btcbot/
```

**Estrutura esperada:**
```
/opt/btcbot/
├── logs-stage/      # Logs do ambiente Stage
├── logs-prod/       # Logs do ambiente Production
├── backups/
│   ├── stage/       # Backups do banco Stage
│   └── prod/        # Backups do banco Production
└── scripts/         # Scripts de backup/restore
```

---

## Passo 7: Criar Arquivos de Ambiente

### 7.1 Ambiente Stage (.env.stage)

```bash
cat > /opt/btcbot/.env.stage << 'EOF'
# BTC Grid Bot - Stage Environment
# IMPORTANTE: Usar apenas credenciais de DEMO/VST

# Docker Hub
DOCKER_USERNAME=seu_usuario_dockerhub

# PostgreSQL
POSTGRES_USER=btcbot
POSTGRES_PASSWORD=ALTERE_SENHA_STAGE_AQUI
POSTGRES_DB=btcbot_stage

# BingX API (DEMO APENAS)
BINGX_API_KEY=sua_api_key_demo
BINGX_SECRET_KEY=sua_secret_key_demo

# Trading Mode - OBRIGATORIO ser demo em Stage
TRADING_MODE=demo

# Trading Settings
SYMBOL=BTC-USDT
LEVERAGE=10

# Grid Settings
GRID_SPACING_TYPE=fixed
GRID_SPACING_VALUE=100
GRID_RANGE_PERCENT=5
TAKE_PROFIT_PERCENT=1.0
ORDER_SIZE_USDT=100
MAX_ORDERS=10

# MACD Settings
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
MACD_TIMEFRAME=1h

# Reactivation Mode
REACTIVATION_MODE=immediate

# Health Check
HEALTH_PORT=8080
EOF

# Proteger arquivo (somente owner pode ler/escrever)
chmod 600 /opt/btcbot/.env.stage
```

### 7.2 Ambiente Production (.env.prod)

```bash
cat > /opt/btcbot/.env.prod << 'EOF'
# BTC Grid Bot - Production Environment
# ATENCAO: Este ambiente usa DINHEIRO REAL!

# Docker Hub
DOCKER_USERNAME=seu_usuario_dockerhub

# PostgreSQL
POSTGRES_USER=btcbot
POSTGRES_PASSWORD=ALTERE_SENHA_PROD_AQUI
POSTGRES_DB=btcbot_prod

# BingX API (PRODUCAO - DINHEIRO REAL)
BINGX_API_KEY=sua_api_key_producao
BINGX_SECRET_KEY=sua_secret_key_producao

# Trading Mode - live para producao real
TRADING_MODE=live

# Trading Settings
SYMBOL=BTC-USDT
LEVERAGE=10

# Grid Settings
GRID_SPACING_TYPE=fixed
GRID_SPACING_VALUE=100
GRID_RANGE_PERCENT=5
TAKE_PROFIT_PERCENT=1.0
ORDER_SIZE_USDT=100
MAX_ORDERS=10

# MACD Settings
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
MACD_TIMEFRAME=1h

# Reactivation Mode
REACTIVATION_MODE=immediate

# Health Check
HEALTH_PORT=8080
EOF

# Proteger arquivo
chmod 600 /opt/btcbot/.env.prod
```

**IMPORTANTE:** Edite os arquivos e substitua:
- `ALTERE_SENHA_STAGE_AQUI` e `ALTERE_SENHA_PROD_AQUI` por senhas fortes e diferentes
- `sua_api_key_*` e `sua_secret_key_*` pelas credenciais reais da BingX
- `seu_usuario_dockerhub` pelo seu usuario do Docker Hub

---

## Passo 8: Copiar Scripts de Backup/Restore

Os scripts de backup e restore devem ser copiados do repositorio para o homeserver.

### Opcao A: Copiar do repositorio local (execute na sua maquina de desenvolvimento)

```bash
# Na sua maquina de desenvolvimento
scp scripts/backup_db.sh scripts/restore_db.sh usuario@192.168.68.99:/opt/btcbot/scripts/
```

### Opcao B: Clonar repositorio no homeserver

```bash
# No homeserver
cd /tmp
git clone https://github.com/OWNER/btcbot.git
cp /tmp/btcbot/scripts/backup_db.sh /opt/btcbot/scripts/
cp /tmp/btcbot/scripts/restore_db.sh /opt/btcbot/scripts/
rm -rf /tmp/btcbot
```

Apos copiar, configurar permissoes:

```bash
# No homeserver
chmod +x /opt/btcbot/scripts/*.sh

# Verificar
ls -la /opt/btcbot/scripts/
```

---

## Passo 9: Configurar Backup Automatico (Opcional)

Configure cron jobs para backup automatico dos bancos de dados.

```bash
# Editar crontab
crontab -e

# Adicionar as seguintes linhas:

# Stage: backup diario as 3:00 AM
0 3 * * * /opt/btcbot/scripts/backup_db.sh stage >> /opt/btcbot/logs-stage/backup.log 2>&1

# Production: backup a cada 6 horas
0 */6 * * * /opt/btcbot/scripts/backup_db.sh prod >> /opt/btcbot/logs-prod/backup.log 2>&1
```

Verificar cron jobs configurados:
```bash
crontab -l | grep btcbot
```

---

## Passo 10: Verificacao Final

Execute os seguintes comandos para verificar que tudo esta configurado:

```bash
echo "=== Verificacao do Setup ==="

echo -e "\n1. Docker:"
docker --version && echo "OK" || echo "FALHOU"

echo -e "\n2. Portainer:"
docker ps --filter "name=portainer" --format "{{.Names}}: {{.Status}}" || echo "NAO ENCONTRADO"

echo -e "\n3. Watchtower:"
docker ps --filter "name=watchtower" --format "{{.Names}}: {{.Status}}" || echo "NAO ENCONTRADO"

echo -e "\n4. Estrutura de diretorios:"
ls -la /opt/btcbot/

echo -e "\n5. Arquivos de ambiente:"
ls -la /opt/btcbot/.env.* 2>/dev/null || echo "NAO ENCONTRADOS"

echo -e "\n6. Scripts:"
ls -la /opt/btcbot/scripts/*.sh 2>/dev/null || echo "NAO ENCONTRADOS"

echo -e "\n7. Docker Hub login:"
docker info 2>/dev/null | grep Username || echo "NAO LOGADO"
```

---

## Checklist de Verificacao

Antes de prosseguir para as proximas tasks (DEVOPS-002, DEVOPS-008), confirme:

- [ ] Docker instalado e rodando
- [ ] Portainer acessivel em `http://192.168.68.99:9000`
- [ ] Watchtower rodando com `WATCHTOWER_LABEL_ENABLE=true`
- [ ] Logado no Docker Hub (`docker login`)
- [ ] Diretorio `/opt/btcbot/` criado com estrutura correta
- [ ] Arquivo `/opt/btcbot/.env.stage` criado e configurado
- [ ] Arquivo `/opt/btcbot/.env.prod` criado e configurado
- [ ] Scripts de backup/restore copiados e com permissao de execucao
- [ ] Cron jobs de backup configurados (opcional)

---

## Proximos Passos

Apos completar este setup:

1. **DEVOPS-002:** Criar `docker-compose.stage.yml`
2. **DEVOPS-002B:** Criar `docker-compose.prod.yml`
3. **DEVOPS-008:** Configurar stack Stage no Portainer
4. **DEVOPS-008B:** Configurar stack Production no Portainer

---

## Troubleshooting

### Docker nao inicia
```bash
sudo systemctl status docker
sudo systemctl start docker
```

### Permissao negada no Docker
```bash
sudo usermod -aG docker $USER
# Fazer logout e login novamente
```

### Watchtower nao atualiza containers
Verificar se o container tem a label correta:
```bash
docker inspect <container_name> | grep -A5 Labels
# Deve conter: "com.centurylinklabs.watchtower.enable": "true"
```

### Nao consegue conectar ao Docker Hub
```bash
# Verificar DNS
nslookup hub.docker.com

# Verificar conectividade
curl -I https://hub.docker.com
```

---

## Referencias

- [Documentacao Portainer](https://docs.portainer.io/)
- [Documentacao Watchtower](https://containrrr.dev/watchtower/)
- [Docker Hub Access Tokens](https://hub.docker.com/settings/security)
- [GitFlow - Fluxo de Trabalho](/docs/GITFLOW.md)

---

*Documento criado em 26/12/2025 - DEVOPS-016*
