from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import re

from .products import format_selected_products


@dataclass(frozen=True)
class WorkspaceResult:
    root: Path
    manifest_path: Path
    created_files: tuple[Path, ...]


def sanitize_folder_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "-", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "cliente"


def _write_if_missing(path: Path, content: str) -> Path:
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    return path


def create_client_workspace(
    base_dir: Path,
    company_name: str,
    contact_name: str | None = None,
    selected_products: list[str] | None = None,
) -> WorkspaceResult:
    base_dir = base_dir.expanduser()
    root = base_dir / sanitize_folder_name(company_name)
    root.mkdir(parents=True, exist_ok=True)

    folders = (
        root / "01_briefing",
        root / "02_anexos",
        root / "03_proposta",
        root / "04_envios",
        root / "05_referencias",
        root / "06_produtos",
    )
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []

    created_files.append(
        _write_if_missing(
            root / "00_LEIA_MEU_FLUXO.txt",
            (
                f"Workspace comercial da FutureMedia para: {company_name}\n\n"
                "Fluxo recomendado:\n"
                "1. Preencha o briefing.\n"
                "2. Coloque anexos em 02_anexos.\n"
                "3. Revise os produtos selecionados.\n"
                "4. Gere a proposta na interface.\n"
                "5. Salve a versao final em 03_proposta.\n"
                "6. Registre os envios em 04_envios.\n"
            ),
        )
    )
    created_files.append(
        _write_if_missing(
            root / "01_dados_do_cliente.txt",
            (
                f"Empresa: {company_name}\n"
                f"Contato: {contact_name or ''}\n"
                "Email: \n"
                "Telefone: \n"
                "Cidade: \n"
                "Segmento: \n"
                "Observacoes:\n"
            ),
        )
    )
    created_files.append(
        _write_if_missing(
            root / "02_briefing.txt",
            (
                "Objetivo da proposta:\n"
                "Contexto do cliente:\n"
                "Evento/campanha:\n"
                "Prazo:\n"
                "Formato de entrega:\n"
                "Pontos de atencao:\n"
            ),
        )
    )
    created_files.append(
        _write_if_missing(
            root / "06_produtos_escolhidos.txt",
            (
                "Produtos selecionados para esta proposta:\n"
                f"{format_selected_products(selected_products)}\n"
            ),
        )
    )
    created_files.append(
        _write_if_missing(
            root / "03_proposta" / "proposta-base.md",
            (
                f"# Proposta comercial - {company_name}\n\n"
                "## 1. Saudacao\n\n"
                "## 2. Entendimento da demanda\n\n"
                "## 3. Solucao recomendada\n\n"
                "## 4. Beneficios para o cliente\n\n"
                "## 5. Escopo e entregas\n\n"
                "## 6. Proximos passos\n\n"
                "## 7. Encerramento\n"
            ),
        )
    )

    manifest_path = root / "cliente.json"
    manifest = {
        "company_name": company_name,
        "contact_name": contact_name,
        "selected_products": selected_products or [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return WorkspaceResult(root=root, manifest_path=manifest_path, created_files=tuple(created_files))

