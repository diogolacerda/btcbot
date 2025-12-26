# Configuracao de Branch Protection - GitHub

Este documento descreve como configurar a protecao de branches no repositorio GitHub.

## Branch: main

A branch `main` e a branch principal do projeto e deve ser protegida.

### Configuracao Atual

> **Nota:** Para projetos solo ou com agentes de IA usando a mesma conta GitHub,
> a aprovacao formal de PR nao funciona (nao pode aprovar proprio PR).
> Usamos um fluxo alternativo baseado em **review via comentario + label**.

### Passos para Configurar

1. Acesse: https://github.com/diogolacerda/btcbot/settings/branches

2. Clique em **Add branch protection rule**

3. Em **Branch name pattern**, digite: `main`

4. Configure as seguintes opcoes:

#### Protecao de Pull Requests

- [x] **Require a pull request before merging**
  - [ ] ~~Require approvals~~ (desabilitado - usamos review via comentario)
  - [ ] ~~Dismiss stale pull request approvals~~ (nao aplicavel)
  - [ ] Require review from Code Owners (opcional)

#### Status Checks

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Status checks obrigatorios (adicionar apos CI estar configurado):
    - `lint`
    - `typecheck`
    - `test`
    - `build`

#### Outras Protecoes

- [x] **Do not allow bypassing the above settings**
- [ ] **Require signed commits** (opcional, recomendado para producao)
- [ ] **Require linear history** (opcional)
- [x] **Restrict who can push to matching branches** (apenas via PR)

---

## Fluxo de Review com Agentes

Como todos os agentes usam a mesma conta GitHub, usamos um fluxo alternativo:

### 1. Agente Implementador cria o PR

```bash
# Agente DevOps cria branch e PR
git checkout -b feature/DEVOPS-004-ci-pipeline
# ... faz as mudancas ...
git push -u origin feature/DEVOPS-004-ci-pipeline
gh pr create --title "feat: CI pipeline" --body "..."
```

### 2. Agente Revisor faz review via comentario

```bash
# Outro agente DevOps revisa e adiciona comentario + label
gh pr comment <numero> --body "## Review por staff-devops agent

### Checklist
- [x] Codigo segue padroes do projeto
- [x] Sem problemas de seguranca
- [x] Documentacao atualizada

### Resultado: APROVADO

O PR esta pronto para merge."

# Adiciona label de aprovado
gh pr edit <numero> --add-label "approved"
```

### 3. Agente Implementador faz merge

```bash
# Apos ver o label "approved", faz o merge
gh pr merge <numero> --merge --delete-branch
```

### Labels para Review

| Label | Descricao |
|-------|-----------|
| `approved` | Revisado e aprovado por outro agente |
| `needs-review` | Aguardando revisao |
| `changes-requested` | Revisor solicitou mudancas |

### Fluxo Visual

```
Agente A (implementa)     Agente B (revisa)      Agente A (merge)
        |                        |                      |
        | cria PR                |                      |
        |----------------------->|                      |
        |                        | review + comment     |
        |                        | + label "approved"   |
        |<-----------------------|                      |
        |                                               |
        |---------------------------------------------->|
        |                                  merge + deploy
```

5. Clique em **Create** ou **Save changes**

## Branch: develop (Opcional)

Se usar branch develop para integracao:

1. Em **Branch name pattern**, digite: `develop`

2. Configure protecoes similares a main, mas menos restritivas:
   - Require pull request: Sim
   - Require approvals: 1
   - Require status checks: lint, test

## Verificacao

Apos configurar, verifique:

1. Tente fazer push direto para main:
   ```bash
   git push origin main
   # Deve falhar com erro de protecao
   ```

2. Crie uma branch e PR:
   ```bash
   git checkout -b test/branch-protection
   echo "test" > test.txt
   git add test.txt
   git commit -m "test: verify branch protection"
   git push -u origin test/branch-protection
   gh pr create --title "Test branch protection" --body "Testing"
   ```

3. Verifique que o PR requer:
   - Aprovacao de reviewer
   - CI passando (apos DEVOPS-004)

4. Delete a branch de teste:
   ```bash
   gh pr close --delete-branch
   ```

## Bypass para Emergencias

Em situacoes de emergencia, administradores podem:

1. Temporariamente desabilitar protecao
2. Fazer push/merge
3. Reabilitar protecao imediatamente

**ATENCAO:** Documente qualquer bypass em uma Issue.

## Referencias

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [About Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
