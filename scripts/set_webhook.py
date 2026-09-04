"""One-off script: register a tenant bot's webhook URL with Telegram.

Usage:
    python scripts/set_webhook.py <bot_token> <tenant_slug> <bot_slug> <webhook_secret>

Example:
    python scripts/set_webhook.py 123456:ABC-DEF pho-saigon phosaigon-bot s3cr3t

Sets: https://pho-saigon.nanovm.space/webhooks/telegram/phosaigon-bot
"""

from __future__ import annotations

import sys

import httpx


def main() -> None:
    if len(sys.argv) != 5:
        print(__doc__)
        raise SystemExit(1)

    bot_token, tenant_slug, bot_slug, webhook_secret = sys.argv[1:5]
    url = f"https://{tenant_slug}.nanovm.space/webhooks/telegram/{bot_slug}"

    resp = httpx.post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        json={"url": url, "secret_token": webhook_secret},
        timeout=10,
    )
    resp.raise_for_status()
    print(resp.json())


if __name__ == "__main__":
    main()
