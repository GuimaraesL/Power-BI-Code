---
name: powerbi-code-intelligence
description: >-
  Installs, synchronizes, and configures automated CI/CD intelligence, PR change reviewer,
  integrity tests, and Power BI development standards from the central source of truth
  (GuimaraesL/Power-BI-Code) into any Power BI repository (.pbip / TMDL / PBIR).
  Use when the user asks to adopt the PBIP CI reviewer, replicate the PR summary workflow,
  install Power BI automation, or sync capabilities from the forked Power-BI-Code repo.
---

# Power BI Code Intelligence & CI Automation Skill

Esta skill capacita o agente a portar, instalar e configurar toda a esteira de inteligência, automação CI/CD e auditoria contínua de projetos Power BI (`.pbip`, TMDL, PBIR) a partir do repositório canônico mantido como **Fonte de Verdade**.

---

## 1. Fonte Canônica de Verdade

> [!IMPORTANT]
> **Repositório Central:** [`https://github.com/GuimaraesL/Power-BI-Code`](https://github.com/GuimaraesL/Power-BI-Code) (Branch: `main`)
>
> Este repositório é a **fonte oficial e centralizada de verdade** para todos os fluxos de revisão de código, automações de PR, templates e diretrizes de desenvolvimento Power BI.
>
> Qualquer novo repositório corporativo ou pessoal que utilize arquivos PBIP deve adotar este fluxo copiando os artefatos diretamente desta fonte de verdade.

---

## 2. Artefatos Gerenciados pela Fonte de Verdade

A esteira de inteligência é composta por 3 pilares fundamentais:

| Artefato | Caminho Canônico | Finalidade |
| :--- | :--- | :--- |
| **Workflow do GitHub Actions** | `.github/workflows/pbip-summary.yml` | Intercepta Pull Requests com alterações em arquivos `.json`, `.tmdl`, `.m`, `.pbip`, orquestra o revisor e publica/atualiza um comentário fixo (*sticky comment*) no PR com formatação em português. |
| **Motor de Auditoria Python** | `.github/scripts/pbip_change_reviewer.py` | Parser especializado em PBIR, TMDL e Power Query M. Detecta movimentação e redimensionamento de visuais, alterações em medidas DAX (com visualização *Antes/Depois*), partições e fórmulas, gerando Markdown sem ruídos. |
| **Suíte de Integridade PBIP** | `tests/test_pbip_integrity.py` | Bateria de testes automatizados com `pytest` fiscalizando crases triplas DAX balanceadas, ausência de conflitos de merge Git, unicidade de medidas, proibição de `dataType` explícito em medidas e integridade de links relativos no PBIR. |

---

## 3. Diagnóstico do Repositório Alvo

Antes de instalar o fluxo, avalie se o repositório atende aos pré-requisitos de um projeto Power BI moderno:

1. **Estrutura de Pastas PBIP:**
   - Presença de arquivo `*.pbip` na raiz.
   - Pasta `*.Report/` contendo `definition.pbir` e diretório `definition/pages/`.
   - Pasta `*.SemanticModel/` contendo `definition/model.tmdl` e `definition/tables/`.
2. **Ambiente Python:**
   - Python 3.10 ou superior instalado localmente.
   - Pacotes de desenvolvimento instalados: `pytest`, `ruff`.

---

## 4. Procedimento de Instalação e Aplicação

### Método 1: Instalação Automatizada via Script Helper (Recomendado)

A skill fornece um utilitário de instalação de um comando que conecta diretamente à fonte de verdade no GitHub e sincroniza todos os arquivos necessários:

```bash
# Execução na raiz do repositório Power BI de destino
python "C:/Users/GuimaraesL/.gemini/config/skills/powerbi-code-intelligence/scripts/install_toolkit.py" --target . --force
```

Opções disponíveis no script:
- `--target` / `-t`: Diretório do projeto (padrão: `.`).
- `--repo` / `-r`: Repositório fonte de verdade (padrão: `GuimaraesL/Power-BI-Code`).
- `--branch` / `-b`: Branch fonte (padrão: `main`).
- `--force` / `-f`: Sobrescreve arquivos existentes com a versão mais recente da fonte de verdade.
- `--dry-run`: Simula as operações sem gravar no disco.

---

### Método 2: Instalação Manual via GitHub CLI (`gh`)

Caso deseje sincronizar os arquivos manualmente via terminal:

```bash
# 1. Criar as pastas de destino
mkdir -p .github/workflows .github/scripts tests

# 2. Baixar o workflow do GitHub Actions
gh api repos/GuimaraesL/Power-BI-Code/contents/.github/workflows/pbip-summary.yml \
  -q .content | base64 -d > .github/workflows/pbip-summary.yml

# 3. Baixar o script revisor PBIP
gh api repos/GuimaraesL/Power-BI-Code/contents/.github/scripts/pbip_change_reviewer.py \
  -q .content | base64 -d > .github/scripts/pbip_change_reviewer.py

# 4. Baixar a suíte de testes de integridade
gh api repos/GuimaraesL/Power-BI-Code/contents/tests/test_pbip_integrity.py \
  -q .content | base64 -d > tests/test_pbip_integrity.py
```

---

## 5. Configuração Mandatória de Permissões no GitHub

Para que o GitHub Actions consiga postar e atualizar automaticamente o resumo de alterações no PR:

1. No repositório remoto do GitHub, navegue até:
   **Settings** $\rightarrow$ **Actions** $\rightarrow$ **General**.
2. Na seção **Workflow permissions**, selecione:
   - `Read and write permissions`
   - Marque a caixa `Allow GitHub Actions to create and approve pull requests`.
3. Clique em **Save**.

> [!NOTE]
> O workflow já possui permissões granulares declaradas no YAML:
> ```yaml
> permissions:
>   contents: read
>   pull-requests: write
> ```
> A habilitação nas configurações do repositório garante que a token `GITHUB_TOKEN` possua a delegação necessária para a API de PRs.

---

## 6. Procedimento de Validação Local

Sempre execute a validação local antes de realizar o commit das alterações:

### 6.1. Validar a Ajuda e Argumentos do Revisor
```bash
python .github/scripts/pbip_change_reviewer.py --help
```
*Critério de Sucesso:* Exibe as opções `--old`, `--new`, `--output`, `--repo-url`, `--head-sha` e `--pr-number` com mensagens em português.

### 6.2. Teste Simulado de Execução
```bash
python .github/scripts/pbip_change_reviewer.py --old "meu_projeto.Report" --new "meu_projeto.Report" --output "summary_test.md"
```
*Critério de Sucesso:* Gera o arquivo `summary_test.md` com o cabeçalho `# Resumo de Alterações PBIP`.

### 6.3. Execução da Suíte de Integridade
```bash
pytest tests/test_pbip_integrity.py -v
```
*Critério de Sucesso:* Todos os testes passam aprovados (vínculo relativo PBIR, integridade sintática TMDL, balanceamento de crases triplas e ausência de dataType explícito em medidas).

### 6.4. Análise Estática de Código
```bash
ruff check tests/
```
*Critério de Sucesso:* Zero erros de linter.

---

## 7. Ciclo de Vida e Atualização da Fonte de Verdade

Para manter a integridade do ecossistema corporativo:

```text
[Upstream Oficial: odetma/Power-BI-Code]
                │
                ▼ (Sync Fork / Git Fetch)
[Fonte de Verdade: GuimaraesL/Power-BI-Code] (Centraliza melhorias e tradução PT-BR)
                │
                ├──► [Projeto Isolacao Motores]
                ├──► [Projeto Custos de Manutenção]
                └──► [Demais Repositórios PBIP]
```

1. **Atualização a partir do Upstream:**
   Periodicamente, sincronize o fork `GuimaraesL/Power-BI-Code` com a branch `main` do upstream `odetma/Power-BI-Code` usando `gh repo sync GuimaraesL/Power-BI-Code`.
2. **Propagação de Melhorias Locais:**
   Sempre que uma nova regra de negócio, validação semântica ou melhoria no revisor for criada em um projeto local, envie um PR ou commit para a fonte de verdade (`GuimaraesL/Power-BI-Code`), garantindo que todos os futuros projetos herdem a inteligência atualizada.
