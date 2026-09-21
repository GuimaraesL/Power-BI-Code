#!/usr/bin/env python3
"""
Instalador e Sincronizador de Inteligência PBIP para Repositórios Power BI.

Fonte de Verdade: https://github.com/GuimaraesL/Power-BI-Code

Este script automatiza a cópia e aplicação do fluxo de revisão de alterações PBIP/TMDL/PBIR,
workflows de GitHub Actions e testes de integridade em qualquer repositório Power BI.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

DEFAULT_REPO = "GuimaraesL/Power-BI-Code"
DEFAULT_BRANCH = "main"

# Lista de arquivos gerenciados pela fonte de verdade: (caminho_relativo_origem, caminho_relativo_destino)
MANAGED_FILES: List[Tuple[str, str]] = [
    (
        ".github/workflows/pbip-summary.yml",
        ".github/workflows/pbip-summary.yml",
    ),
    (
        ".github/scripts/pbip_change_reviewer.py",
        ".github/scripts/pbip_change_reviewer.py",
    ),
    (
        "tests/test_pbip_integrity.py",
        "tests/test_pbip_integrity.py",
    ),
]


def log(msg: str) -> None:
    print(f"[powerbi-code-intelligence] {msg}")


def download_file_raw(repo: str, branch: str, file_path: str) -> str:
    """Baixa o conteúdo raw de um arquivo no GitHub."""
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Antigravity-PBIP-Intelligence-Installer"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Falha HTTP ao baixar {url} (Status {exc.code})") from exc
    except Exception as exc:
        raise RuntimeError(f"Erro de conexão ao baixar {url}: {exc}") from exc


def fetch_via_gh_cli(repo: str, branch: str, file_path: str) -> str:
    """Fallback usando a CLI oficial do GitHub (gh api)."""
    cmd = ["gh", "api", f"repos/{repo}/contents/{file_path}?ref={branch}", "-q", ".content"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api falhou para {file_path}: {proc.stderr.strip()}")
    import base64
    return base64.b64decode(proc.stdout.strip()).decode("utf-8")


def get_file_content(repo: str, branch: str, file_path: str) -> str:
    """Tenta baixar via raw HTTP e recorre à CLI gh se necessário."""
    try:
        return download_file_raw(repo, branch, file_path)
    except Exception:
        return fetch_via_gh_cli(repo, branch, file_path)


def detect_pbip_project(target_dir: Path) -> bool:
    """Verifica se o diretório de destino possui características de projeto Power BI."""
    has_pbip = any(target_dir.glob("*.pbip"))
    has_report = any(target_dir.glob("*.Report")) or (target_dir / "definition.pbir").exists()
    has_model = any(target_dir.glob("*.SemanticModel")) or (target_dir / "definition" / "model.tmdl").exists()
    return has_pbip or has_report or has_model


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instala o fluxo de inteligência PBIP a partir da fonte de verdade oficial."
    )
    parser.add_argument(
        "--target",
        "-t",
        default=".",
        help="Diretório raiz do repositório Power BI de destino (default: diretório atual).",
    )
    parser.add_argument(
        "--repo",
        "-r",
        default=DEFAULT_REPO,
        help=f"Repositório fonte de verdade no GitHub (default: {DEFAULT_REPO}).",
    )
    parser.add_argument(
        "--branch",
        "-b",
        default=DEFAULT_BRANCH,
        help=f"Branch fonte de verdade (default: {DEFAULT_BRANCH}).",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Sobrescreve arquivos existentes mesmo se já modificados.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exibe as ações que seriam executadas sem gravar arquivos.",
    )

    args = parser.parse_args()
    target_root = Path(args.target).resolve()

    log(f"Iniciando instalação no repositório: {target_root}")
    log(f"Fonte de verdade: https://github.com/{args.repo} (branch: {args.branch})")

    if not detect_pbip_project(target_root):
        log("AVISO: Não foram detectados arquivos .pbip, .Report ou .SemanticModel na raiz.")
        log("Certifique-se de executar o instalador na raiz do repositório Power BI.")

    success_count = 0
    for src_path, dest_rel in MANAGED_FILES:
        dest_path = target_root / dest_rel
        log(f"Obtendo: {src_path} -> {dest_rel}")

        if dest_path.exists() and not args.force:
            log(f"  [PULADO] Arquivo já existe: {dest_rel} (use --force para sobrescrever)")
            continue

        if args.dry_run:
            log(f"  [DRY-RUN] Baixaria e gravaria em: {dest_path}")
            success_count += 1
            continue

        try:
            content = get_file_content(args.repo, args.branch, src_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")
            log(f"  [CONCLUÍDO] Arquivo gravado com sucesso ({len(content.splitlines())} linhas).")
            success_count += 1
        except Exception as exc:
            log(f"  [ERRO] Falha ao obter {src_path}: {exc}")

    log(f"Operação finalizada: {success_count} arquivo(s) processado(s).")
    log("Próximos passos:")
    log("1. Valide a sintaxe do script: python .github/scripts/pbip_change_reviewer.py --help")
    log("2. Execute a suíte de integridade: pytest tests/test_pbip_integrity.py")
    log("3. Certifique-se de que o GitHub Actions tem permissões de escrita em PRs (Settings -> Actions -> General).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
