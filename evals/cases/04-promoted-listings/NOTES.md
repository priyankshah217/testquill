# 04 — Promoted listings: designer notes

**Shape:** gappy draft PRD with explicit "TBD"s and many silent gaps.
**Primary dimension:** faithfulness. The generator should test what is stated
and either skip the gaps or flag them as open questions, never invent
behaviour.

## Stated requirements
- R1: Promote entry point on own listing.
- R2: Two packages: 3-day/30 coins, 7-day/60 coins.
- R3: Coins deducted immediately; insufficient balance → top-up prompt.
- R4: Promoted listing appears in top 3 of its category's search results,
  rotating with other promoted listings.
- R5: "Promoted" label on search card.
- R6: Time remaining visible on listing page.
- R7: On expiry, normal ranking resumes; label removed.
- R8: Only Available listings; restricted categories blocked.
- R9: Stats card: views + chats during promo vs equal prior period.

## Deliberate gaps (must NOT be asserted as fact)
- **Refunds** (explicitly TBD): listing sold, deleted, or reported mid-promotion.
- **Rotation capacity** (explicitly TBD): how many listings share top 3.
- **Re-promoting / stacking:** buying a second bump while one is active
  (extend? queue? blocked?). Not mentioned at all.
- **Status change mid-promotion:** listing marked Sold/Reserved while promoted.
  Does promotion stop? Not stated.
- **Keyword search vs category browse:** PRD only says "search results for its
  category"; behaviour on keyword search is unspecified.
- **Timezone / exact end time:** whether 3 days = 72h from purchase or ends at
  midnight.
- **Top-up return flow:** whether the purchase resumes automatically after
  top-up.
- **Notifications** on promotion start/end: none mentioned.

## Ideal behaviour
A good suite covers R1–R9 and, where it touches a gap, either omits it or
phrases it as a question/blocked case. Any test asserting a specific outcome for
a gap is **Unsupported**.

## Traps
- "Coins are refunded when the listing is sold during promotion" → **Unsupported**.
- "Seller receives a notification when promotion ends" → **Unsupported**.
- "Buying a second bump extends the duration" → **Unsupported**.
