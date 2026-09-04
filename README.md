# vietbot

Multi-tenant Telegram-first food delivery ordering, governed by a nano-vm
FSM core (Program→Tool→Trace). One independent Telegram bot per tenant
(brand identity decision, 2026-09-04) — not a shared bot with deep-link
routing. Tenants share one Postgres + one nano-vm program set; only the
Telegram bot token and the subdomain differ per tenant.

## Architecture decisions this scaffold encodes

- **VPS**: non-RF IP — `api.telegram.org` is blocked from RF IPs (the
  reason this is a separate deploy from Sieshka, not a config flag on it).
- **Domain**: `nanovm.space`, wildcard subdomain per tenant
  (`<tenant_slug>.nanovm.space`).
- **Telegram**: webhook, not long polling — decided once TLS was already
  required for YooKassa anyway, no reason to pay the polling-vs-webhook
  cost twice.
- **YooKassa**: one ShopID for the whole platform for now (MVP decision).
  `tenants.yookassa_shop_id`/`yookassa_secret_key` are nullable columns
  already in the schema so switching to per-tenant ShopIDs later is a
  data migration, not a schema migration.
- **Session boundary / terminal-tool-raises**: both CONSTRAINTS.md rules
  from the Sieshka project applied from the first commit, not retrofitted
  after a production incident (as happened there).

## What's NOT built yet (explicit, not silently deferred)

- Menu/catalog domain (products, categories) — only `Order` exists.
- Real Telegram message flow (WebApp button / inline keyboard for cart) —
  webhook route currently acks and no-ops on `/start`.
- YooKassa payment tool — `Order.payment_method`/`total_amount` exist,
  no `yookassa_tools.py` yet.
- Alembic migration files — models exist, `alembic init`/first revision
  not generated in this scaffold.
- Admin/tenant-onboarding UI — new tenant + new bot are DB inserts done
  by hand (or a script) for now.

## Deploy steps (non-RF VPS)

1. **DNS**: point `*.nanovm.space` (or explicit `<tenant>.nanovm.space`
   records) at the VPS IP.

2. **Wildcard TLS cert** (DNS-01, not HTTP-01 — required for wildcards):
   ```bash
   certbot certonly --manual --preferred-challenges dns \
     -d "*.nanovm.space" -d "nanovm.space"
   ```
   Follow the TXT-record prompt at your DNS provider. Copy the resulting
   `fullchain.pem`/`privkey.pem` into `./nginx-ssl/` as
   `nanovm.space-fullchain.pem` / `nanovm.space-privkey.pem` (paths
   referenced in `nginx/default.conf`).

3. **Env**: `cp .env.example .env`, fill in `POSTGRES_PASSWORD`,
   `DATABASE_URL`, YooKassa creds when ready.

4. **Bring up the stack**:
   ```bash
   docker compose up -d --build
   ```

5. **Run migrations** (once `alembic` is initialized against
   `app/domains/models.py`):
   ```bash
   docker compose exec app alembic upgrade head
   ```

6. **Onboard first tenant** — insert a `tenants` row + a `tenant_bots`
   row (bot created via @BotFather first, token copied in), then:
   ```bash
   python scripts/set_webhook.py <bot_token> <tenant_slug> <bot_slug> <webhook_secret>
   ```
   `webhook_secret` must match the value stored in `tenant_bots.webhook_secret`
   — it's what Telegram echoes back in the
   `X-Telegram-Bot-Api-Secret-Token` header on every webhook call, and is
   the only thing standing between `/webhooks/telegram/<bot_slug>` and an
   unauthenticated stranger who guesses the slug.

## Next steps (proposed order)

1. Menu/catalog domain + admin insert path for it
2. Telegram WebApp checkout flow (reuses Sieshka's WebApp-in-Mini-App
   pattern conceptually, new implementation)
3. `yookassa_tools.py` — mirror Sieshka's manual-integration pattern
   (redirect, `payment_method_data.type` explicit, no embedded widget —
   that fight is already fought and documented in Sieshka's DECISIONS.md,
   no reason to relitigate it here)
4. Alembic first revision
5. Real per-tenant onboarding path (script or minimal admin form) instead
   of hand-written INSERTs
