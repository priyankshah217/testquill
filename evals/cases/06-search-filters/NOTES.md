# 06 — Search filters: designer notes

**Shape:** interdependent controls. Exercises the existing output-contract rule
"If two or more controls are interdependent, test EVERY direction (A affects B
AND B affects A)."

## Dependency matrix: a strong suite tests each direction
| Rule | Direction A → B | Direction B → A |
|---|---|---|
| 1 Free ↔ Price | Free on clears price | Typing price turns Free off |
| 2 Min ↔ Max | min > max swap on blur | empty min = 0, empty max = unbounded |
| 3 Meetup ↔ Distance | Meetup off resets+disables Distance | Distance disabled until Meetup on |
| 4 Permission ↔ Distance/Nearest | Denied disables both + helper text | Grant enables both without reopening |
| 5 Nearest ↔ Meetup | Choosing Nearest auto-selects Meetup | Deselecting Meetup reverts sort to Best match |
| 6 Free ↔ Price sorts | Free on hides price sorts, active one → Best match | Free off shows them again |
| 7 Category ↔ Condition | no_condition category hides+clears | switching back does NOT restore |

**Chains worth one test each:**
- Nearest active → remove Meetup chip → Distance reset + sort → Best match.
- Free on while Price low→high active → sort falls back, price cleared.

Also: Reset restores every default listed; Show N results updates live.

## Deliberately NOT specified (must not be asserted as fact)
- Whether filters persist across sessions/app restarts.
- Exact result counts or ranking for Best match.
- Behaviour on permission "Ask next time" / approximate location.
- Whether Free off restores the previously cleared price values (not stated;
  rule 1 only says it clears).
- Max/min allowed price values.

## Traps
- "Turning Free off restores the previous price range" → **Unsupported**.
- "Switching back to a normal category restores conditions" → contradicts rule 7.
