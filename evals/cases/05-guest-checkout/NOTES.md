# 05 — Guest checkout: designer notes

**Shape:** realistic PRD with one planted internal contradiction.

## The contradiction
- §1 Overview: guest orders capped at **$500 per order**.
- §4 Payment & risk rules: guest order total must not exceed **$300**.

**Ideal behaviour:** the suite surfaces the conflict (e.g. a test titled or
noted as "blocked: limit is $500 in §1 vs $300 in §4") or tests boundaries
in a way that makes the conflict visible. Silently picking one value is a
faithfulness defect; silently picking **$500** (the less-specific, overview
number) is worse than picking $300 (the rules section).

**Answer-key guidance:** write boundary tests for the cap but mark the
Expected Result as dependent on resolution, or write them against §4 ($300)
and note the conflict in `Requirement` (e.g. `§4 cap — CONFLICT with §1`).

## Other coverage hot spots
- Eligibility: meetup-only, offer-accepted, and logged-in users don't get the
  guest path.
- Required fields: each of email, name, phone, address missing.
- Card brands: Visa, Mastercard accepted; another brand (e.g. Amex) rejected.
- Cap boundary: total exactly at cap vs cap + 1, where total = item + delivery
  fee (item alone under cap but total over).
- Rate limit: 3rd order ok, 4th blocked with exact message, resets after 24h.
- 3DS failure: message shown and **no order created**.
- Track-order link works logged out.
- Create-account prompt pre-filled; order linked after account creation.
- Seller sees "Guest buyer" + name; listing → Sold.

## Deliberately NOT specified (must not be asserted as fact)
- Email/phone format validation rules.
- What "linked" looks like for an existing account with the same email.
- Refunds/cancellation for guest orders.
- Whether the 3/24h limit is also keyed by card or device (only email stated).

## Traps
- Asserting AmEx/PayPal accepted → contradicts §3 step 4.
- Asserting the guest must verify email before paying → **Unsupported**.
