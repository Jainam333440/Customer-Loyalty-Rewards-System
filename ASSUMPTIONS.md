# Assumptions and decisions

1. One factory operates this application; multi-tenant support is out of scope.
2. Possession of a hidden code inside a sealed box is the purchase evidence. This is cheaper than retailer integration but cannot prove payment or prevent supply-chain theft. Print under a tamper-evident panel, never outside the box.
3. Codes have 128 random bits, are stored only as SHA-256 hashes, and are exported once to the owner for secure printing. Lost exports require revocation and reissue.
4. Owner creates a batch after production. Each batch has fixed integer points and expires after 365 days; unused codes can be revoked together.
5. Customers register with a unique username and password, avoiding collection of phone numbers and addresses. No email verification or password recovery is implemented in this assignment.
6. Points never expire and cannot be transferred or converted to money. No real payments occur.
7. Rewards have integer point costs and finite stock. Redeeming deducts points and reserves stock immediately. Owner marks pickup fulfilled or cancels with exactly one refund and stock restoration.
8. Pickup is in person. Customer shows the redemption ID while logged in; owner verifies the username. Shipping and notifications are excluded.
9. SQLite is suitable for a small factory demo on one server with persistent disk. Transactions serialize claims and redemptions. Production at scale should move to PostgreSQL and a managed deployment.
10. Failed login attempts are limited per source address; claim attempts per customer. A shared NAT may temporarily affect legitimate logins. Distributed abuse, account farming, and human fraud require additional production controls.
11. All changes require a same-origin CSRF token. Sessions expire after 8 hours. HTTPS and secure cookies are required outside localhost.
12. Audit events retain usernames/IDs but never passwords or raw box codes. Retention and customer deletion policy require client agreement before production.
13. A live hosted URL is optional in the brief. The deliverable is a runnable repository; deployment requires persistent storage and HTTPS. GitHub Pages cannot run this Python backend.
