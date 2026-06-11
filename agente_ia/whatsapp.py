from __future__ import annotations

from .config import AppConfig
from .proposal import ProposalResult


def _wait_for_login(page) -> None:
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)


def normalize_phone_number(raw_phone: str, default_country_code: str) -> str:
    digits = "".join(ch for ch in raw_phone if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith(default_country_code):
        return digits
    if len(digits) <= 11:
        return f"{default_country_code}{digits}"
    return digits


def send_whatsapp_message(
    config: AppConfig,
    recipient_name: str,
    proposal: ProposalResult,
    phone: str | None = None,
    send_now: bool = False,
) -> None:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Playwright nao esta instalado. Rode 'pip install -r requirements.txt' e depois 'python -m playwright install'."
        ) from exc

    config.browser_profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser_type = p.chromium
        launch_kwargs = {
            "headless": False,
            "user_data_dir": str(config.browser_profile_dir),
        }
        if config.browser_channel:
            launch_kwargs["channel"] = config.browser_channel

        context = browser_type.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()

        _wait_for_login(page)

        phone_digits = normalize_phone_number(phone or "", config.default_country_code)
        if phone_digits:
            page.goto(f"https://web.whatsapp.com/send?phone={phone_digits}", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
        else:
            search_locators = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]',
            ]
            search_box = None
            for selector in search_locators:
                try:
                    search_box = page.locator(selector).first
                    search_box.click(timeout=5000)
                    break
                except Exception:
                    continue
            if search_box is None:
                raise RuntimeError("Nao consegui encontrar a busca do WhatsApp Web.")

            search_box.fill(recipient_name)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)

        message_box = None
        try:
            message_box = page.locator('footer div[contenteditable="true"][role="textbox"]').first
            message_box.click(timeout=5000)
        except Exception:
            candidates = page.locator('div[contenteditable="true"][role="textbox"]')
            if candidates.count() > 1:
                message_box = candidates.nth(candidates.count() - 1)
                message_box.click(timeout=5000)

        if message_box is None:
            raise RuntimeError("Nao consegui encontrar a caixa de mensagem do WhatsApp.")

        message_box.fill(proposal.body)

        if send_now:
            try:
                page.get_by_role("button", name="Enviar").click(timeout=5000)
            except PlaywrightTimeoutError:
                page.keyboard.press("Enter")

        page.wait_for_timeout(1500)
        context.close()
