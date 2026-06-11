from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .config import AppConfig, load_config
from .emailer import send_email as send_email_action
from .files import search_documents
from .proposal import ProposalResult, generate_proposal as generate_proposal_action
from .products import products_by_category
from .workspace import create_client_workspace
from .validation import validate_flow as validate_flow_action
from .whatsapp import send_whatsapp_message as send_whatsapp_action


class AgentApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = load_config()
        self.current_proposal: ProposalResult | None = None

        self.root.title("Agente IA Local")
        self.root.geometry("1100x780")
        self.root.minsize(980, 700)
        self.root.configure(bg="#f4efe7")

        self._style = ttk.Style()
        try:
            self._style.theme_use("clam")
        except tk.TclError:
            pass
        self._style.configure("TFrame", background="#f4efe7")
        self._style.configure("TLabel", background="#f4efe7", foreground="#1f1a17", font=("Segoe UI", 10))
        self._style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8))
        self._style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#1f1a17")
        self._style.configure("Hint.TLabel", font=("Segoe UI", 9), foreground="#60554f")
        self._style.configure("Section.TLabelframe", background="#f4efe7", padding=10)
        self._style.configure("Section.TLabelframe.Label", background="#f4efe7", foreground="#1f1a17", font=("Segoe UI", 10, "bold"))

        self.query_var = tk.StringVar()
        self.recipient_var = tk.StringVar()
        self.company_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.client_root_var = tk.StringVar(value=str(self.config.files_root))
        self.status_var = tk.StringVar(value="Pronto para buscar arquivos e montar a proposta.")
        self.product_categories = products_by_category()
        self.product_vars: dict[str, tk.BooleanVar] = {}

        self._busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x")
        ttk.Label(header, text="Agente IA Local", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Buscar arquivos, gerar proposta, revisar e enviar por email ou WhatsApp Web.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        form = ttk.Frame(container)
        form.pack(fill="x", pady=(0, 12))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Nome da pessoa/cliente").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.recipient_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Email").grid(row=0, column=2, sticky="w", padx=(12, 8), pady=4)
        ttk.Entry(form, textvariable=self.email_var).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="WhatsApp/Telefone").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.phone_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Busca/tema").grid(row=1, column=2, sticky="w", padx=(12, 8), pady=4)
        ttk.Entry(form, textvariable=self.query_var).grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="Empresa").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.company_var).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Button(form, text="Criar pasta modelo", command=self.create_client_template).grid(
            row=2, column=2, sticky="ew", padx=(12, 8), pady=4
        )
        ttk.Label(form, text="Nome da empresa usada na proposta e na pasta.", style="Hint.TLabel").grid(
            row=2, column=3, sticky="w", pady=4
        )

        ttk.Label(form, text="Pasta do cliente").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.client_root_var).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Button(form, text="Selecionar", command=self.pick_client_folder).grid(
            row=3, column=2, sticky="ew", padx=(12, 8), pady=4
        )
        ttk.Label(
            form,
            text="Use uma pasta específica do cliente para evitar arquivos de evento.",
            style="Hint.TLabel",
        ).grid(row=3, column=3, sticky="w", pady=4)

        products_frame = ttk.Labelframe(container, text="Produtos FutureMedia", style="Section.TLabelframe")
        products_frame.pack(fill="x", pady=(0, 12))
        notebook = ttk.Notebook(products_frame)
        notebook.pack(fill="x")
        for category, items in self.product_categories.items():
            self._build_product_tab(notebook, category, items)

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(0, 12))
        self.search_btn = ttk.Button(buttons, text="Buscar arquivo", command=self.search_files)
        self.generate_btn = ttk.Button(buttons, text="Gerar proposta", command=self.generate_proposal)
        self.review_btn = ttk.Button(buttons, text="Revisar", command=self.review_proposal)
        self.validate_btn = ttk.Button(buttons, text="Validar fluxo", command=self.validate_flow)
        self.email_btn = ttk.Button(buttons, text="Enviar por email", command=self.send_email)
        self.whatsapp_btn = ttk.Button(buttons, text="Enviar no WhatsApp", command=self.send_whatsapp)

        for index, button in enumerate(
            [self.search_btn, self.generate_btn, self.review_btn, self.validate_btn, self.email_btn, self.whatsapp_btn]
        ):
            button.grid(row=0, column=index, padx=(0, 8), pady=4, sticky="ew")
            buttons.columnconfigure(index, weight=1)

        main = ttk.Frame(container)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.Labelframe(main, text="Resultado da busca", style="Section.TLabelframe")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.results_text = scrolledtext.ScrolledText(left, wrap="word", height=20, font=("Consolas", 10))
        self.results_text.grid(row=0, column=0, sticky="nsew")

        right = ttk.Labelframe(main, text="Proposta para revisar", style="Section.TLabelframe")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.proposal_text = scrolledtext.ScrolledText(right, wrap="word", height=20, font=("Segoe UI", 10))
        self.proposal_text.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Label(footer, textvariable=self.status_var, style="Hint.TLabel").pack(anchor="w")

        self.log(
            "Defina o nome, email ou tema e clique em Buscar arquivo ou Gerar proposta. "
            "Depois revise o texto e use os botoes de envio."
        )

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for button in [
            self.search_btn,
            self.generate_btn,
            self.review_btn,
            self.validate_btn,
            self.email_btn,
            self.whatsapp_btn,
        ]:
            button.configure(state=state)

    def log(self, message: str) -> None:
        self.status_var.set(message)
        self.root.after(0, self._append_results, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")

    def _append_results(self, text: str) -> None:
        self.results_text.insert("end", text)
        self.results_text.see("end")

    def _set_proposal_text(self, text: str) -> None:
        self.proposal_text.delete("1.0", "end")
        self.proposal_text.insert("1.0", text)

    def _get_query(self) -> str:
        query = self.query_var.get().strip()
        if query:
            return query
        return self.recipient_var.get().strip()

    def _selected_products(self) -> list[str]:
        return [key for key, var in self.product_vars.items() if var.get()]

    def _active_root(self) -> Path:
        raw_root = self.client_root_var.get().strip()
        if raw_root:
            return Path(raw_root).expanduser()
        return self.config.files_root

    def pick_client_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self._active_root()))
        if selected:
            self.client_root_var.set(selected)
            self.log(f"Pasta do cliente definida para: {selected}")

    def create_client_template(self) -> None:
        company_name = self.company_var.get().strip()
        if not company_name:
            messagebox.showinfo("Info", "Preencha o nome da empresa antes de criar a pasta modelo.")
            return

        base_root = self._active_root()
        selected_products = self._selected_products()
        result = create_client_workspace(
            base_dir=base_root,
            company_name=company_name,
            contact_name=self.recipient_var.get().strip() or None,
            selected_products=selected_products,
        )
        self.client_root_var.set(str(result.root))
        self.log(f"Pasta modelo criada em: {result.root}")
        messagebox.showinfo("Pasta criada", f"Pasta modelo criada com sucesso em:\n{result.root}")

    def _build_product_tab(self, parent: ttk.Frame, category: str, product_items: tuple) -> None:
        frame = ttk.Frame(parent, padding=8)
        parent.add(frame, text=category)

        columns = 3
        for index, product in enumerate(product_items):
            row = index // columns
            column = index % columns
            var = tk.BooleanVar(value=False)
            self.product_vars[product.key] = var
            check = ttk.Checkbutton(frame, text=product.name, variable=var)
            check.grid(row=row, column=column, sticky="w", padx=8, pady=6)
            frame.columnconfigure(column, weight=1)

    def _current_reviewed_proposal(self) -> ProposalResult:
        if self.current_proposal is None:
            raise RuntimeError("Nenhuma proposta gerada ainda.")

        body = self.proposal_text.get("1.0", "end").strip()
        if not body:
            raise RuntimeError("O texto da proposta esta vazio.")

        output_dir = self.config.output_dir / "propostas-revisadas"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = output_dir / f"proposta-revisada-{timestamp}.md"
        output_path.write_text(f"# {self.current_proposal.subject}\n\n{body}\n", encoding="utf-8")

        proposal = ProposalResult(
            subject=self.current_proposal.subject,
            body=body,
            source_bundle=self.current_proposal.source_bundle,
            output_path=output_path,
        )
        self.current_proposal = proposal
        return proposal

    def _run_async(self, worker, success_message: str | None = None) -> None:
        if self._busy:
            return

        self.set_busy(True)

        def runner() -> None:
            try:
                worker()
                if success_message:
                    self.root.after(0, lambda: self.log(success_message))
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("Erro", str(exc)))
                self.root.after(0, lambda: self.log(f"Falha: {exc}"))
            finally:
                self.root.after(0, lambda: self.set_busy(False))

        threading.Thread(target=runner, daemon=True).start()

    def search_files(self) -> None:
        query = self._get_query()
        if not query:
            messagebox.showinfo("Info", "Preencha o nome da pessoa ou o tema da busca.")
            return

        def worker() -> None:
            active_root = self._active_root()
            hits = search_documents(active_root, query=query, limit=12)
            lines = [f"Busca: {query}", f"Pasta base: {active_root}", ""]
            if not hits:
                lines.append("Nenhum arquivo encontrado.")
            else:
                for hit in hits:
                    lines.append(f"- {hit.path} | score={hit.score}")
                    if hit.excerpt:
                        lines.append(hit.excerpt[:900])
                        lines.append("")

            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            self.root.after(0, lambda: self._append_results("\n".join(lines) + "\n"))

        self._run_async(worker, "Busca concluida.")

    def generate_proposal(self) -> None:
        name = self.recipient_var.get().strip()
        if not name:
            messagebox.showinfo("Info", "Preencha o nome da pessoa ou cliente.")
            return

        query = self._get_query()

        def worker() -> None:
            proposal = generate_proposal_action(
                self.config,
                recipient_name=name,
                recipient_email=self.email_var.get().strip() or None,
                query=query,
                files_root=self._active_root(),
                company_name=self.company_var.get().strip() or None,
                selected_products=self._selected_products(),
            )
            self.current_proposal = proposal
            self.root.after(0, lambda: self._set_proposal_text(proposal.body))
            self.root.after(0, lambda: self.log(f"Proposta gerada em {proposal.output_path}"))

        self._run_async(worker)

    def review_proposal(self) -> None:
        try:
            reviewed = self._current_reviewed_proposal()
            self._set_proposal_text(reviewed.body)
            self.log(f"Revisao salva em {reviewed.output_path}")
            messagebox.showinfo("Revisao", f"Proposta revisada e salva em:\n{reviewed.output_path}")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def validate_flow(self) -> None:
        def worker() -> None:
            report = validate_flow_action(
                self.config,
                root=self._active_root(),
                recipient_name=self.recipient_var.get().strip() or None,
                recipient_email=self.email_var.get().strip() or None,
                phone=self.phone_var.get().strip() or None,
                query=self._get_query() or None,
                selected_products=self._selected_products(),
            )
            lines = [f"Validação do fluxo - pasta: {report.root}", ""]
            for item in report.items:
                lines.append(f"[{item.level.upper()}] {item.message}")
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            self.root.after(0, lambda: self._append_results("\n".join(lines) + "\n"))
            self.root.after(0, lambda: self.log("Validação concluída." if report.ok else "Validação encontrou problemas."))

        self._run_async(worker)

    def send_email(self) -> None:
        recipient_email = self.email_var.get().strip()
        if not recipient_email:
            messagebox.showinfo("Info", "Preencha o email do destinatario.")
            return

        if self.current_proposal is None:
            messagebox.showinfo("Info", "Gere a proposta antes de enviar por email.")
            return

        if not messagebox.askyesno("Confirmar envio", "Deseja enviar o email agora?"):
            return

        def worker() -> None:
            proposal = self._current_reviewed_proposal()
            draft_path = send_email_action(self.config, recipient_email=recipient_email, proposal=proposal, send_now=True)
            self.root.after(0, lambda: messagebox.showinfo("Email enviado", f"Email enviado com sucesso.\n{draft_path}"))
            self.root.after(0, lambda: self.log(f"Email enviado para {recipient_email}"))

        self._run_async(worker)

    def send_whatsapp(self) -> None:
        name = self.recipient_var.get().strip()
        if not name:
            messagebox.showinfo("Info", "Preencha o nome da pessoa ou cliente.")
            return

        if self.current_proposal is None:
            messagebox.showinfo("Info", "Gere a proposta antes de enviar no WhatsApp.")
            return

        if not messagebox.askyesno("Confirmar envio", "Deseja abrir o WhatsApp e enviar a mensagem agora?"):
            return

        def worker() -> None:
            proposal = self._current_reviewed_proposal()
            send_whatsapp_action(
                self.config,
                recipient_name=name,
                proposal=proposal,
                phone=self.phone_var.get().strip() or None,
                send_now=True,
            )
            self.root.after(0, lambda: messagebox.showinfo("WhatsApp", "Mensagem preparada/enviada com sucesso."))
            self.root.after(0, lambda: self.log(f"WhatsApp processado para {name}"))

        self._run_async(worker)


def main() -> int:
    root = tk.Tk()
    AgentApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
