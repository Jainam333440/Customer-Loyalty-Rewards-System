# Test results

Executed on 14 November 2026 in the build environment.

## Automated verification — PASS

- `python -m unittest discover -s tests -v`: **20 tests passed** in approximately 5.6 seconds.
- `node --test tests/ui.test.cjs`: **2 tests passed**.
- `node --check static/app.js`: passed.
- Python compilation of the initial HTTP/domain implementation: passed.

Coverage: duplicate claims across accounts; concurrent claims; expired/revoked/invalid codes; hashes-only storage; concurrent overspending; last-unit stock races; original-cost refunds and exactly-once cancellation; fulfilled-state locking; hidden rewards on creation/redemption; numeric validation; persistent rate limits; sessions/logout/expiry; password hashes and duplicate usernames; owner authorization; CSRF; registration role escalation; response privacy; login request headers; static path allowlist; cookie flags; editor reset identity; HTML escaping.

The initial Python run failed the hidden-reward test (the same domain test ran twice before the test inheritance was cleaned up). After the fix and cleanup, all 20 distinct tests passed. The pre-fix UI reset handler was tested separately against commit `38ad8b5` and failed with retained ID `7`; the current regression passes. See `AI_LOG.md`.

## Browser inspection — limited PASS

Opened the app through the development preview in Chrome. Confirmed title, readable desktop layout, rendered styling, username/password labels and the sign-in/create-account controls. The initial preview startup exposed missing CLI port parsing; after correction the preview served successfully.

Full browser login/claim/redemption, CSV downloads, mobile devices and keyboard/screen-reader audits were **not** executed in this session. Their backend operations are covered by automated tests; these manual checks remain for the student's final demo rehearsal. No claim is made of production load testing or a formal security audit.

## Manual rehearsal plan (not yet executed)

| Step | Action | Expected result |
|---|---|---|
| 1 | Initialize owner, start server, sign in | Owner overview, starter rewards |
| 2 | Issue 3 codes at 100 points each; download CSV | Three distinct codes, batch count 3 |
| 3 | Register customer and claim one code | Balance 100; ledger +100 |
| 4 | Submit same code again or from another account | Rejected; balance unchanged |
| 5 | Redeem 75-point tote | Balance 25; pending pickup; stock minus one |
| 6 | Cancel as owner | Balance 100; stock restored; one refund |
| 7 | Redeem again and fulfill | Terminal fulfilled state; no extra deduction |
| 8 | Revoke the batch and claim an unused code | Claim rejected; audit event shown |
| 9 | Create hidden reward, then activate it | Hidden from customer until activated |
| 10 | Edit reward, press Reset, add a different reward | New reward added; old reward unchanged |
| 11 | Refresh/restart server | Accounts, points and history persist |
| 12 | Narrow browser to a phone width; use Tab navigation | Cards stack; forms remain usable; table scrolls horizontally |

## Public repository verification — pending

No target repository URL was supplied in this request. Publication and anonymous accessibility verification must be completed before submission. A local preview is not a public deployment.
