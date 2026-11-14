# Box & Bonus — Customer Loyalty Rewards System

Submission repository: [Customer-Loyalty-Rewards-System](https://github.com/Jainam333440/Customer-Loyalty-Rewards-System)

A working factory rewards application. Customers register, claim hidden product-box codes, earn points, and reserve rewards. The factory owner issues codes, manages the reward catalog, processes pickup requests, and monitors claims and suspicious activity.

## Quick start (Windows, macOS, Linux)

Requires **Python 3.11+** with SQLite and OpenSSL/scrypt support. There are no third-party Python packages to install. Node.js 18+ is optional for the two JavaScript tests; it is not needed to run the application.

Open a terminal inside this folder:

```bash
python app.py init
python app.py
```

On Windows, use `py` if `python` is unavailable. On macOS/Linux, use `python3` if needed.

1. `init` prompts for your own owner username and password (at least 10 characters). Password input is hidden. It also creates three starter rewards. Run this once on a fresh database; do not use it to reset an existing owner.
2. Open **http://127.0.0.1:8000** in your browser.
3. Sign in as the owner and issue a batch of box codes. Download the CSV immediately.
4. Sign out, create a customer account, and sign in.
5. Enter one of the generated codes. Points appear immediately.
6. Redeem an affordable reward, then sign in as owner to fulfill or cancel it.

There are **no default credentials**, API keys, external AI calls, or payment services. AI helped build the application; customer actions do not depend on an AI model.

## Features

- Customer accounts, secure password hashing, session expiry, logout.
- Random 128-bit codes; database stores code hashes only; one claim per box globally.
- Transactional points ledger, balance checks, stock reservation, one-time refunds.
- Batch generation (1–500 codes), one-time CSV export, expiry, batch revocation.
- Owner-only reward creation/editing, visibility and stock management.
- Pickup fulfillment/cancellation, recent audit events, aggregate program metrics.
- Server-side role checks, request validation, CSRF controls and rate limits.
- Responsive cream/green interface with labeled controls and status messages.

## Technology and file map

| File | Purpose |
|---|---|
| `app.py` | Python standard-library HTTP server, routes, authentication/authorization adapter |
| `core.py` | SQLite schema, password/session handling, transactions and business rules |
| `static/index.html` | Initial page and authentication form |
| `static/app.js` | Customer and owner UI, API calls, CSV export |
| `static/style.css` | Responsive presentation |
| `tests/test_rewards.py` | 20 automated domain and HTTP integration tests |
| `tests/ui.test.cjs` | 2 JavaScript regression checks |
| `ASSUMPTIONS.md` | Every scope choice and limitation |
| `ARCHITECTURE.md` | Design reasons, data model, diagrams and security boundaries |
| `AI_LOG.md` | 8 actual development interactions, including two verified mistakes |
| `TEST_RESULTS.md` | Recorded results and remaining manual checks |
| `DEMO_GUIDE.md` | Short live demo and explanation prompts |
| `GITHUB_SUBMISSION.md` | Preserve commits and publish the public repository |
| `.env.example` | Placeholder configuration only |

## Tests

```bash
python -m unittest discover -s tests -v
node --test tests/ui.test.cjs
```

Tests create temporary databases and do not alter the real application database. See `TEST_RESULTS.md` for verified results and limitations. The Node checks exercise UI logic with DOM stubs; they are not full browser end-to-end tests.

## Configuration

`.env.example` documents environment variables; the app does **not** automatically read `.env` files.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_PATH` | `loyalty.sqlite3` | Persistent SQLite database path |
| `HOST` | `127.0.0.1` | Listening interface |
| `PORT` | `8000` | Listening port |
| `COOKIE_SECURE` | unset/`0` | Set to `1` only when served over HTTPS |

For example, PowerShell: `$env:PORT="8001"; python app.py`. Bash: `PORT=8001 python3 app.py`.
The server also accepts `--host` and `--port` arguments. `package.json` is only a preview convenience, not a Node backend.

## Deployment status and limits

**No public hosted application is deployed.** The assignment makes a deployed link optional. Submit the public GitHub **repository** URL after publication; repository access does not require application login, but using private rewards accounts does.

This is a locally runnable assignment/demo, not an Internet-hardened production service. Python's standard-library HTTP server is used to keep setup explainable and dependency-free. Before a real launch, replace the HTTP adapter with a production framework/server, use HTTPS, enable secure cookies, configure trusted proxy handling and request timeouts, add monitoring/backups and recovery, and assess data-retention obligations. SQLite needs persistent disk and a single server deployment; an ephemeral filesystem will lose records. See the architecture and assumptions for fraud limits.

GitHub Pages cannot run this backend. Never upload a database, raw code export, `.env`, or real credentials. The supplied `.gitignore` excludes these common paths. Code CSVs should stay under ignored `exports/` locally, and should be deleted securely after printing.
