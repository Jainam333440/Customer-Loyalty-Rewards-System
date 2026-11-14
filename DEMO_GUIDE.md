# Five-minute live demo

## Before presenting

Run `python app.py init` once, choose your owner credentials, then run `python app.py`. Keep one normal browser session for the owner and one private/incognito session for a customer. Run the automated tests. Never display a real production export in a recording.

## Demo script

1. **Problem (30 seconds):** “A factory wants repeat purchases. Each box contains a private code that turns one purchase into loyalty points. Customers spend those points on rewards.”
2. **Owner (45 seconds):** Sign in. Explain customer count, claimed boxes, outstanding points, pending pickup and rejected claims. Generate three 100-point codes and save the one-time export.
3. **Customer (60 seconds):** Create an account, claim one code, show 100 points and the ledger. Try the code again: it is rejected without adding points.
4. **Rewards (45 seconds):** Redeem the 75-point tote. Show 25 points and the pickup reference. As owner, cancel it: points return and stock is restored. Explain fulfillment as the alternative.
5. **Fraud (30 seconds):** Revoke the remaining unused batch codes and explain tamper-evident packaging, random codes, hashed storage and transactions. A code proves possession; it is not a retailer payment confirmation.
6. **AI review (60 seconds):** Open `AI_LOG.md`, show the hidden-reward and editor-reset mistakes, then show their passing regression tests. Open `ARCHITECTURE.md` and explain the diagram.

## Likely questions

**How do you identify a returning customer?** A unique account username and password; a secure session retrieves that account's persisted balance/history.

**What if two customers claim at once?** A write transaction locks the claim-and-award operation. One commits; the other sees the used code.

**Can someone claim by calling the API directly?** They can use the API, but authentication, role checks, CSRF, rate limits and code validation still apply server-side.

**Why no AI in the actual reward calculation?** Points and stock need exact, reproducible results. AI was used to develop and review the code.

**Why SQLite?** It makes a single-server assignment portable. Scaling would require a managed database and deployment changes.

**What is not finished for production?** Receipt verification, account recovery, verified customer identity, enterprise fraud detection, production HTTP hosting, monitoring, backups and retention tooling.
