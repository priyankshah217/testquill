# 01 — Mark as sold: designer notes

**Shape:** one-paragraph prompt. Run with `testquill -p "$(cat prd.md)"`.

**What it stresses:** restraint. Thin input should produce a small, focused
suite (roughly 6–12 cases). Padding with invented behaviour is the main
failure mode.

## Stated requirements
- R1: Seller can mark own listing as sold from the listing page.
- R2: Sold listing no longer appears in search results.
- R3: Buyers with an existing chat about the listing see a "Sold" badge.
- R4: Seller can undo (revert to available).

## Deliberately NOT specified (must not be asserted as fact)
- Whether the sold listing is still reachable via direct link / the seller's profile.
- Whether the seller picks *which buyer* it was sold to.
- Whether buyers receive a notification (only a badge is stated).
- Any time limit on undo.
- Whether undo restores the listing's original search ranking / bump status.
- Whether new chats can be started on a sold listing.
- Who besides the seller can mark it sold (implied: only the seller).

## Reasonable inferences (acceptable, not hallucinations)
- A non-owner cannot mark someone else's listing as sold (negative test).
- After undo, the listing reappears in search and the badge disappears.

## Traps
- Asserting a notification or push message is sent → **Unsupported**.
- Asserting "listing is deleted" → **Unsupported** (contradicts undo).
