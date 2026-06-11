from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AppConfig
from .files import search_documents
from .products import get_product
from .whatsapp import normalize_phone_number


@dataclass(frozen=True)
class ValidationItem:
    level: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    root: Path
    items: list[ValidationItem] = field(default_factory=list)


def _check_ollama(config: AppConfig) -> ValidationItem:
    try:
        request = Request(f"{config.ollama_base_url}/api/tags", method="GET")
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ConnectionError) as exc:
        return ValidationItem(
            level="erro",
            message=f"Ollama nao respondeu em {config.ollama_base_url}: {exc}",
        )

    models = data.get("models") or []
    model_names = {str(model.get("name", "")).split(":", 1)[0] for model in models}
    if config.ollama_model not in model_names and not any(
        str(model.get("name", "")).startswith(config.ollama_model) for model in models
    ):
        return ValidationItem(
            level="erro",
            message=f"Ollama esta rodando, mas o modelo '{config.ollama_model}' nao foi encontrado.",
        )

    return ValidationItem(level="ok", message=f"Ollama esta pronto com o modelo '{config.ollama_model}'.")


def validate_flow(
    config: AppConfig,
    root: str | Path | None,
    recipient_name: str | None = None,
    query: str | None = None,
    recipient_email: str | None = None,
    phone: str | None = None,
    selected_products: list[str] | None = None,
) -> ValidationReport:
    active_root = Path(root).expanduser() if root else config.files_root
    items: list[ValidationItem] = []

    if not active_root.exists():
        items.append(ValidationItem(level="erro", message=f"A pasta base nao existe: {active_root}"))
        return ValidationReport(ok=False, root=active_root, items=items)

    items.append(ValidationItem(level="ok", message=f"Pasta base encontrada: {active_root}"))

    if query:
        hits = search_documents(active_root, query=query, limit=5)
        if hits:
            items.append(ValidationItem(level="ok", message=f"Busca encontrou {len(hits)} documento(s) relevantes."))
        else:
            items.append(
                ValidationItem(
                    level="aviso",
                    message="Nenhum documento relevante foi encontrado para a busca informada.",
                )
            )
    else:
        items.append(ValidationItem(level="aviso", message="Nenhum tema de busca foi informado."))

    provider = (config.llm_provider or "").strip().lower()
    if provider == "ollama":
        items.append(_check_ollama(config))
    elif provider == "openai":
        if config.openai_api_key:
            items.append(ValidationItem(level="ok", message="Chave da OpenAI configurada."))
        else:
            items.append(ValidationItem(level="erro", message="LLM_PROVIDER=openai, mas OPENAI_API_KEY nao foi configurada."))
    else:
        items.append(ValidationItem(level="aviso", message=f"Provedor LLM atual: {provider or 'nao definido'}"))

    if recipient_name:
        items.append(ValidationItem(level="ok", message=f"Destinatario informado: {recipient_name}"))
    else:
        items.append(ValidationItem(level="aviso", message="Nome do destinatario nao foi preenchido."))

    if recipient_email:
        items.append(ValidationItem(level="ok", message=f"Email informado: {recipient_email}"))
    else:
        items.append(ValidationItem(level="aviso", message="Email nao informado."))

    if phone:
        normalized = normalize_phone_number(phone, config.default_country_code)
        if normalized:
            items.append(ValidationItem(level="ok", message=f"WhatsApp/telefone validado: {normalized}"))
        else:
            items.append(ValidationItem(level="erro", message="Telefone do WhatsApp nao parece valido."))
    else:
        items.append(ValidationItem(level="aviso", message="Telefone nao informado."))

    if selected_products:
        valid_products = [item for item in selected_products if get_product(item)]
        if valid_products:
            items.append(ValidationItem(level="ok", message=f"{len(valid_products)} produto(s) selecionado(s)."))
        else:
            items.append(ValidationItem(level="aviso", message="Produtos selecionados nao foram reconhecidos no catalogo."))
    else:
        items.append(ValidationItem(level="aviso", message="Nenhum produto foi selecionado."))

    ok = not any(item.level == "erro" for item in items)
    return ValidationReport(ok=ok, root=active_root, items=items)
