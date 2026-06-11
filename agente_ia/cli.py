from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .files import search_documents
from .proposal import generate_proposal
from .emailer import send_email
from .workspace import create_client_workspace
from .whatsapp import send_whatsapp_message
from .validation import validate_flow


def _print_hits(hits) -> None:
    if not hits:
        print("Nenhum arquivo relevante encontrado.")
        return
    for hit in hits:
        print(f"- {hit.path} | score={hit.score}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agente-ia", description="Agente local para propostas comerciais.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Procurar arquivos relevantes")
    scan.add_argument("--query", required=True)
    scan.add_argument("--limit", type=int, default=10)
    scan.add_argument("--root")

    proposal = sub.add_parser("proposal", help="Gerar proposta comercial")
    proposal.add_argument("--recipient-name", required=True)
    proposal.add_argument("--recipient-email")
    proposal.add_argument("--query")
    proposal.add_argument("--root")
    proposal.add_argument("--company")
    proposal.add_argument("--product", action="append", default=[])

    email = sub.add_parser("email", help="Gerar proposta e criar/enviar email")
    email.add_argument("--recipient-name", required=True)
    email.add_argument("--recipient-email", required=True)
    email.add_argument("--query")
    email.add_argument("--root")
    email.add_argument("--company")
    email.add_argument("--product", action="append", default=[])
    email.add_argument("--send", action="store_true", help="Envia de fato via SMTP")

    whatsapp = sub.add_parser("whatsapp", help="Gerar proposta e abrir/enviar no WhatsApp Web")
    whatsapp.add_argument("--recipient-name", required=True)
    whatsapp.add_argument("--phone")
    whatsapp.add_argument("--query")
    whatsapp.add_argument("--root")
    whatsapp.add_argument("--company")
    whatsapp.add_argument("--product", action="append", default=[])
    whatsapp.add_argument("--send", action="store_true", help="Envia de fato no WhatsApp")

    run = sub.add_parser("run", help="Fluxo completo")
    run.add_argument("--recipient-name", required=True)
    run.add_argument("--recipient-email")
    run.add_argument("--phone")
    run.add_argument("--query")
    run.add_argument("--root")
    run.add_argument("--company")
    run.add_argument("--product", action="append", default=[])
    run.add_argument("--send-email", action="store_true")
    run.add_argument("--send-whatsapp", action="store_true")

    validate = sub.add_parser("validate", help="Validar o fluxo sem enviar nada")
    validate.add_argument("--recipient-name")
    validate.add_argument("--recipient-email")
    validate.add_argument("--phone")
    validate.add_argument("--query")
    validate.add_argument("--root")
    validate.add_argument("--company")
    validate.add_argument("--product", action="append", default=[])

    init_client = sub.add_parser("init-client", help="Criar pasta modelo por cliente")
    init_client.add_argument("--company", required=True)
    init_client.add_argument("--contact")
    init_client.add_argument("--root")
    init_client.add_argument("--product", action="append", default=[])

    sub.add_parser("gui", help="Abrir a interface grafica nativa")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    if args.command == "scan":
        active_root = Path(args.root).expanduser() if args.root else config.files_root
        hits = search_documents(active_root, args.query, limit=args.limit)
        _print_hits(hits)
        return 0

    if args.command == "proposal":
        proposal = generate_proposal(
            config,
            recipient_name=args.recipient_name,
            recipient_email=args.recipient_email,
            query=args.query,
            files_root=Path(args.root).expanduser() if args.root else None,
            company_name=args.company,
            selected_products=args.product,
        )
        print(f"Proposta criada em: {proposal.output_path}")
        return 0

    if args.command == "email":
        proposal = generate_proposal(
            config,
            recipient_name=args.recipient_name,
            recipient_email=args.recipient_email,
            query=args.query,
            files_root=Path(args.root).expanduser() if args.root else None,
            company_name=args.company,
            selected_products=args.product,
        )
        draft_path = send_email(
            config,
            recipient_email=args.recipient_email,
            proposal=proposal,
            send_now=args.send,
        )
        mode = "enviado" if args.send else "rascunho"
        print(f"Email {mode}: {draft_path}")
        return 0

    if args.command == "whatsapp":
        proposal = generate_proposal(
            config,
            recipient_name=args.recipient_name,
            recipient_email=None,
            query=args.query,
            files_root=Path(args.root).expanduser() if args.root else None,
            company_name=args.company,
            selected_products=args.product,
        )
        send_whatsapp_message(
            config,
            recipient_name=args.recipient_name,
            proposal=proposal,
            phone=args.phone,
            send_now=args.send,
        )
        print("WhatsApp preparado com sucesso.")
        return 0

    if args.command == "run":
        proposal = generate_proposal(
            config,
            recipient_name=args.recipient_name,
            recipient_email=args.recipient_email,
            query=args.query,
            files_root=Path(args.root).expanduser() if args.root else None,
            company_name=args.company,
            selected_products=args.product,
        )
        print(f"Proposta criada em: {proposal.output_path}")

        if args.recipient_email:
            draft_path = send_email(
                config,
                recipient_email=args.recipient_email,
                proposal=proposal,
                send_now=args.send_email,
            )
            mode = "enviado" if args.send_email else "rascunho"
            print(f"Email {mode}: {draft_path}")

        send_whatsapp_message(
            config,
            recipient_name=args.recipient_name,
            proposal=proposal,
            phone=args.phone,
            send_now=args.send_whatsapp,
        )
        print("Fluxo concluido.")
        return 0

    if args.command == "validate":
        report = validate_flow(
            config,
            root=args.root,
            recipient_name=args.recipient_name,
            recipient_email=args.recipient_email,
            phone=args.phone,
            query=args.query,
            selected_products=args.product,
        )
        for item in report.items:
            print(f"[{item.level.upper()}] {item.message}")
        return 0 if report.ok else 2

    if args.command == "init-client":
        base_root = Path(args.root).expanduser() if args.root else config.files_root
        result = create_client_workspace(
            base_dir=base_root,
            company_name=args.company,
            contact_name=args.contact,
            selected_products=args.product,
        )
        print(f"Pasta do cliente criada em: {result.root}")
        print(f"Manifesto: {result.manifest_path}")
        return 0

    if args.command == "gui":
        from .gui import main as gui_main

        return gui_main()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
