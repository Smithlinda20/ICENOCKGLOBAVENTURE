# ICE NOCK GLOBAL VENTURE — Sales, Inventory, Discount & Receipt System

A lean Django MVP for a two-role retail operation:

1. **Sales Representative** — fast POS screen (PACK/CARTON pricing, live
   server-verified discounts, receipts, WhatsApp `wa.me` sharing).
2. **Owner / Admin** — full central dashboard (products, prices, discount
   engine, inventory, sales, reports, sales-rep management, audit log,
   settings).

Currency: **NGN (₦)**. Timezone: **Africa/Lagos**. Installable as a
**PWA** (Progressive Web App) on any phone, tablet or desktop — an
"Install App" button appears automatically in supported browsers
(Chrome/Edge/Android; use Safari's "Add to Home Screen" on iOS).

---

## 1. What was implemented

- Django auth with two roles: `ADMIN` (Owner) and `SALESREP`.
- Product management: name, SKU, category, image, PACK price, CARTON
  price, opening/current stock, minimum stock, packs-per-carton,
  active flag, full price-change history (who/when/old/new).
- **Server-side discount engine** (`discounts/services.py`) supporting
  three configurable strategies (Highest Applicable Tier, Cumulative
  Tier Decomposition, Best Valid) driven entirely by admin-editable
  `DiscountRule` records — nothing is hard-coded.
- POS screen: product search, PACK/CARTON dropdown, qty +/-, live
  server-verified price/discount preview, optional customer
  name/WhatsApp number, 4 payment methods, one-click "Complete Sale".
- **All financial values are recomputed and validated server-side** on
  submit (`sales/services.py`) — the browser's numbers are never
  trusted. Stock is deducted atomically inside the same transaction.
- Receipts: on-screen 58mm/80mm thermal-style layout, browser Print,
  PDF download (ReportLab, works fully offline), WhatsApp `wa.me` deep
  link with a pre-filled message (NO WhatsApp API used anywhere),
  "Copy message" fallback, reprint logging.
- Inventory: stock-in, manual adjustment, returns (via sale
  cancellation), low-stock flags, full movement history with
  user/reason/timestamp.
- Admin dashboard: today's KPIs, month-to-date KPIs, low-stock alerts,
  recent sales.
- Reports: monthly sales analysis (gross/discount/net, by product, by
  unit type, by salesperson, by payment method), salesperson
  performance, inventory report, CSV export for sales & inventory.
- Audit log for logins, product/price/discount changes, stock
  adjustments, sales, cancellations, reprints, settings changes.
- Sales-rep filters: receipt #, product, date range, salesperson, unit
  type, payment method, customer phone.
- System Settings page (company info, receipt footer, currency,
  thermal width, low-stock default).
- Idempotent admin bootstrap from environment variables (never a
  hard-coded password) + optional `seed_demo` command for sample data.
- PWA: manifest, service worker (app-shell caching, network-first for
  live data), installable on any device, responsive Tailwind UI down
  to small phone widths.
- Render-ready: `requirements.txt`, `build.sh`, `render.yaml`,
  `.env-sample`, `.gitignore`, WhiteNoise for static files,
  `dj-database-url` for Postgres.

### Known limitations (deliberately out of scope for the 24-hour MVP,
### per the specification's own "Remove from MVP" list)
- No supplier/purchase-order module, no multi-branch/warehouse, no
  customer credit ledger, no payment gateway, no SMS/email marketing,
  no complex thermal printer drivers (standard browser printing is
  used, as specified) — all explicitly excluded by the spec.
- Payment methods (Cash/Transfer/POS/Other) are a fixed set rather
  than an admin-editable list, to keep the MVP lean.
- Cumulative discount decomposition uses a documented greedy
  "largest usable threshold first" algorithm (see the docstring in
  `discounts/services.py`) — since the spec's example is illustrative
  only, confirm this matches your exact intended behaviour before
  relying on it for large bulk orders, and adjust the algorithm if not.
- The project was authored in an offline sandbox without Django
  installed, so it has **not been run against a live Django server or
  had `makemigrations`/`migrate` executed automatically**. Follow the
  steps in Section 3 to generate migrations, migrate, and smoke-test
  before you go live. Read every file over once — treat this as a
  strong first build, not a guaranteed-perfect one.

---

## 2. Project structure

```
ice_nock_sales/
├── config/            settings, urls, wsgi, asgi
├── accounts/          custom User model, login, sales-rep management
├── core/               SystemSettings, admin dashboard, service worker
├── products/          Product, PriceHistory
├── discounts/         DiscountRule, discount engine service
├── inventory/         StockMovement, stock service
├── sales/             Sale, SaleItem, POS, receipts, PDF, WhatsApp
├── reports/           monthly analysis, performance, CSV export
├── audit/             AuditLog
├── templates/          all HTML templates (Tailwind CDN + Alpine CDN)
├── static/             css/app.css, manifest.json, PWA icons
├── development/       venv instructions
├── manage.py, requirements.txt, build.sh, render.yaml, .env-sample
```

---

## 3. Local setup (run these yourself — Django could not be executed in
   the environment that authored this project)

```bash
# 1. Create and activate a virtual environment
python -m venv development/venv
source development/venv/bin/activate      # Windows: development\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env file and edit it
cp .env-sample .env
# On Windows, set the same variables in your shell/IDE instead of relying on .env
# (this project reads plain os.environ - install python-dotenv usage in
# manage.py/wsgi.py yourself if you want automatic .env loading, or export
# the variables in your shell before running manage.py).

# 4. Generate migrations and set up the database (SQLite by default locally)
python manage.py makemigrations
python manage.py migrate

# 5. Create the owner/admin account from your env vars (never hard-coded)
python manage.py bootstrap_admin

# 6. (Optional) Load demo products, a demo sales rep, and sample discount rules
python manage.py seed_demo

# 7. Run the dev server
python manage.py runserver
```

Then sign in at `http://127.0.0.1:8000/` with:
- **Owner/Admin**: the `ADMIN_USERNAME` / `ADMIN_PASSWORD` you set in `.env`
  (defaults suggested: `Admin1` / `Admin1234` — **change this immediately**).
- **Demo sales rep** (if you ran `seed_demo`): `rep1` / `Rep12345`.

### Smoke-test checklist (do this before submitting)
- [ ] Admin login works, dashboard loads.
- [ ] Add a product with distinct PACK and CARTON prices.
- [ ] Create at least one discount rule (e.g. Carton 10+ = 1%).
- [ ] Sales-rep login works.
- [ ] POS: search product, add to cart, switch PACK/CARTON, change qty,
      confirm discount preview updates.
- [ ] Complete a sale, confirm stock reduced by the right amount.
- [ ] Receipt page: Print, Download PDF, and WhatsApp link (if a phone
      number was entered) all work.
- [ ] Admin → Sales shows the transaction; Cancel restores stock.
- [ ] Reports → Monthly Analysis shows correct totals for today.
- [ ] Install the app via the "📲 Install App" button (desktop Chrome/Edge
      or Android) or "Add to Home Screen" (iOS Safari).

---

## 4. Render deployment

1. Push this project to a Git repository (GitHub/GitLab).
2. On Render, create a **Blueprint** from `render.yaml`, or create the
   web service manually with:
   - Build command: `./build.sh`
   - Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
3. Attach a Render PostgreSQL database and set `DATABASE_URL` (the
   provided `render.yaml` does this for you automatically).
4. Set environment variables in the Render dashboard:
   `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`,
   `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
5. Deploy. `build.sh` installs dependencies, collects static files,
   runs migrations, and idempotently bootstraps the owner/admin account.
6. **Change the admin password immediately after your first login** —
   the suggested `Admin1234` is for initial setup only.

---

## 5. Security notes

- All prices, discounts, totals and stock are calculated and validated
  **only** on the Django server (`sales/services.py`,
  `discounts/services.py`, `inventory/services.py`).
- CSRF protection, hashed passwords, and secure session/CSRF cookies
  (auto-enabled when `DEBUG=False`) are on by default.
- No secrets are hard-coded anywhere in the source; the admin account
  is created from environment variables only.
- Every price change, discount change, product change, stock
  adjustment, sale, cancellation, reprint, and settings change is
  written to the audit log with the acting user and Lagos timestamp.

Business: ICE NOCK GLOBAL VENTURE · 08033604514 · abdulazizmohammedbello4@gmail.com
