# 02 — Make an Offer: designer notes

**Shape:** medium, well-structured PRD. The baseline case: the spec is clear,
so misses here are real coverage failures, not ambiguity.

## Coverage hot spots a strong suite should hit
- Eligibility: all three conditions individually (sold/reserved listing,
  fixed-price flag, own listing) plus the logged-out redirect-and-return.
- Amount boundaries: 0, 1, listing price, listing price + 1, non-integer,
  exactly 50% (no warning), just under 50% (warning, still submittable).
- One-pending-offer rule and the "View your offer" button state.
- Accept cascade: other pending offers auto-declined, their system message,
  listing → Reserved.
- Counter: must be > buyer offer and ≤ listing price; no counter-of-counter.
- Expiry at 48h for both offers *and* counters; new offer allowed afterwards.
- Withdraw allowed when pending; blocked once accepted.
- Inbox: count reflects only pending; sort by amount desc, tie → earliest first.
- Each of the 6 analytics events and the 4 buyer push triggers.

## Deliberately NOT specified (must not be asserted as fact)
- Whether a seller can withdraw/undo an Accept.
- Max number of offers a buyer can make on a listing over time.
- Currency formatting or decimal handling beyond "whole number".
- What happens to pending offers when the seller edits the listing price.
- Whether a declined buyer is notified *by chat message* (only push is stated
  for decline).

## Traps
- Asserting the buyer can counter the seller's counter → **Unsupported**
  (explicitly forbidden).
- Asserting an offer above listing price is accepted → contradicts §3.2.
- Asserting a 24h expiry or any number other than 48h → wrong.
