# AI development log

This is an honest record of this build session, not an invented previous conversation. The user supplied the assignment brief. The remaining entries summarize the AI assistant's implementation/review interactions and tools used, rather than claiming the user typed each internal task. No external AI-generated code was copied without review. The student should read and understand the implementation before submitting.

| # | Prompt / interaction (summarized) | Decision / result and verification |
|---|---|---|
| 1 | User: build a Customer Loyalty Rewards System for boxed physical products, with purchase proof, fraud prevention, owner controls and all repository requirements. | Chose hidden box codes and a deterministic rewards ledger. Documented that possession is weaker than receipt verification. |
| 2 | Design review: keep the application runnable and explainable without third-party dependency installation. | Selected Python, SQLite and vanilla JS. Separated the HTTP adapter from business rules and stated production limitations. |
| 3 | Implementation task: generate codes securely and prevent simultaneous reuse. | Used 128 random bits, hashes only in storage and serialized write transactions. Concurrent-claim test proves exactly one award. |
| 4 | Implementation task: reserve reward stock, preserve original prices and refund once. | Added cost snapshots and terminal fulfillment/cancellation states. Tested concurrent spending, last stock, price changes and repeated refunds. |
| 5 | **AI mistake 1: new hidden rewards were active.** The initial insert omitted the active field even though the UI offered Hidden. | `test_create_hidden_reward` failed with `AssertionError: 1 != 0`. The initial suite repeated domain tests in its HTTP subclass, so that same defect appeared twice; these were not two different mistakes. Fixed the INSERT to include visibility, removed duplicate test inheritance, and reran successfully. The failing implementation is visible before commit `b05d37d`. |
| 6 | **AI mistake 2: editor Reset retained the previous reward ID.** The initial handler only reset the heading. Hidden inputs can retain a programmatically assigned ID, causing the next save to edit the previous reward. | Review identified the stale identity. Added a regression invoking the real reset handler with an existing ID. Against pre-fix JS from commit `11a894d`, it failed with `'7' !== ''`. Fixed the handler to explicitly clear the hidden ID. The current test passes. This was verified with a DOM stub, not claimed as a full browser reproduction. |
| 7 | Security review: test the public HTTP boundary, not just helper functions. | Verified customer-to-owner endpoint denial, CSRF enforcement, role escalation rejection, session expiry/logout, private response fields and cookie flags. All 20 Python tests passed. |
| 8 | Delivery review: verify frontend logic, preview and submission history. | Both Node regression checks passed; JS syntax check passed. Browser inspection confirmed landing-page rendering. Preview initially failed because the server ignored injected port arguments; CLI host/port parsing corrected that. Added honest test limitations, architecture, demo steps and Git history preservation instructions. |

## What the student must be able to explain

- Why hiding a code is an assumption about purchase evidence, not absolute fraud prevention.
- Why a hash is stored rather than a raw code, and why random entropy matters.
- Why checking “unused” and later updating without a transaction is unsafe.
- Why refunding the current reward price would be wrong after a price change.
- Why owner authorization must happen on the server even if owner buttons are hidden.
- Which two AI mistakes were actually found and how their regressions prove the fixes.

Never describe this as entirely hand-written work. The repository intentionally includes the AI contribution and correction evidence.

## Publication note

The six existing local development stages were imported into the public GitHub repository in order using the GitHub connection because direct authenticated Git push was unavailable. GitHub assigned new commit IDs; the references above use those published IDs. The final imported source tree was identical to the locally tested source tree. The original IDs remain in the downloadable Git bundle.
