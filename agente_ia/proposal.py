from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AppConfig
from .files import build_source_bundle
from .products import format_selected_products, get_product


@dataclass(frozen=True)
class ProposalResult:
    subject: str
    body: str
    source_bundle: str
    output_path: Path


def _fallback_proposal(recipient_name: str, source_bundle: str) -> str:
    return (
        f"Olá, {recipient_name}.\n\n"
        "Segue uma proposta comercial estruturada com base nos materiais analisados.\n\n"
        "1. Entendimento da necessidade\n"
        "- A proposta foi organizada a partir dos documentos disponíveis e do contexto comercial informado.\n\n"
        "2. Solução recomendada\n"
        "- Solução alinhada ao objetivo da campanha, com foco em experiência, engajamento e percepção de marca.\n\n"
        "3. Benefícios esperados\n"
        "- Maior atratividade para o público\n"
        "- Experiência mais memorável\n"
        "- Apoio à geração de leads e relacionamento\n\n"
        "4. Próximos passos\n"
        "- Validar escopo, período, local, logística e condições comerciais.\n\n"
        "Observação:\n"
        "Esta versão foi gerada automaticamente e deve ser revisada antes do envio final.\n\n"
        "Fontes utilizadas:\n"
        f"{source_bundle}\n"
    )


def _openai_generate(prompt: str, config: AppConfig) -> str:
    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY nao configurada.")

    from openai import OpenAI

    client = OpenAI(api_key=config.openai_api_key)
    response = client.responses.create(
        model=config.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Voce e um assistente comercial. Escreva propostas objetivas em portugues do Brasil. "
                    "Nao invente dados, valores ou prazos que nao estejam nos documentos de entrada. "
                    "Se faltar informacao, deixe campos abertos para preenchimento humano."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.output_text.strip()


def _ollama_generate(prompt: str, config: AppConfig) -> str:
    payload = {
        "model": config.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }

    request = Request(
        f"{config.ollama_base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Erro no Ollama: {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Nao consegui conectar no Ollama em {config.ollama_base_url}. Verifique se o servidor esta rodando."
        ) from exc

    text = (data.get("response") or "").strip()
    if not text:
        raise RuntimeError("O Ollama retornou uma resposta vazia.")
    return text


def _generate_with_provider(prompt: str, config: AppConfig) -> str:
    provider = (config.llm_provider or "").strip().lower()

    if provider == "openai":
        return _openai_generate(prompt, config)
    if provider == "ollama":
        return _ollama_generate(prompt, config)
    if provider == "fallback":
        raise RuntimeError("Modo fallback selecionado.")

    if config.openai_api_key:
        return _openai_generate(prompt, config)
    return _ollama_generate(prompt, config)


def generate_proposal(
    config: AppConfig,
    recipient_name: str,
    recipient_email: str | None = None,
    query: str | None = None,
    files_root: Path | None = None,
    company_name: str | None = None,
    selected_products: list[str] | None = None,
) -> ProposalResult:
    query = query or recipient_name
    active_root = files_root or config.files_root
    source_bundle = build_source_bundle(active_root, query=query, limit=5)
    selected_products = selected_products or []
    product_summary = format_selected_products(selected_products)
    product_labels: list[str] = []
    for item in selected_products:
        product = get_product(item)
        product_labels.append(product.label if product else item)
    product_names = ", ".join(product_labels) or "Solução personalizada conforme o briefing."
    target_name = company_name or recipient_name
    greeting_name = recipient_name or company_name or "Olá"

    prompt = (
        f"Crie uma proposta comercial em portugues do Brasil para {target_name}."
        f"\nContato principal: {recipient_name or 'nao informado'}"
        f"\nEmail do destinatario: {recipient_email or 'nao informado'}"
        f"\nProdutos selecionados: {product_names}"
        "\n\nUse somente as informacoes abaixo como base. Nao invente valores, prazos ou entregas nao citadas."
        "\n\nCONTEXTO E PRODUTOS:\n"
        f"{product_summary}\n\n"
        "DOCUMENTOS DE APOIO:\n"
        f"{source_bundle}\n\n"
        "Escreva a proposta com tom executivo, consultivo e pronto para envio. "
        "Use a estrutura:\n"
        "1. Assunto\n"
        "2. Saudacao personalizada\n"
        "3. Entendimento da necessidade\n"
        "4. Solucao recomendada e como os produtos ajudam o cliente\n"
        "5. Beneficios comerciais e de experiencia\n"
        "6. Escopo sugerido e observacoes importantes\n"
        "7. Proximos passos objetivos\n"
        "8. Encerramento profissional com chamada para alinhamento\n"
        "\nSe faltar informacao, escreva de forma objetiva e marque o que depende de validacao humana."
    )

    try:
        body = _generate_with_provider(prompt, config)
    except Exception:
        body = _fallback_proposal(greeting_name, source_bundle)

    subject = f"Proposta comercial - {company_name or recipient_name}"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = config.output_dir / "propostas"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"proposta-{timestamp}.md"
    output_path.write_text(f"# {subject}\n\n{body}\n", encoding="utf-8")

    return ProposalResult(
        subject=subject,
        body=body,
        source_bundle=source_bundle,
        output_path=output_path,
    )
