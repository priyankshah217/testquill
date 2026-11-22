# 03 — Listing validation: designer notes

**Shape:** dense rules table. Many small, precise rules. Tests whether the
generator does boundary-value analysis and covers *every* rule rather than
sampling a few.

## Boundary values a strong suite should hit
- Photos: 0, 1, 10, 11; each format (JPG/PNG/HEIC) + one unsupported (e.g.
  GIF); exactly 10 MB vs just over; rejected photo not counting toward 10.
- Title: 4, 5, 80, 81 chars; whitespace-padded string whose trimmed length
  fails; 3 vs 4 consecutive identical chars.
- Category: leaf vs non-leaf.
- Price: -1, 0 ("Free"), 9,999,999, 10,000,000, decimal.
- Description: 4,000 vs 4,001; 7 vs 8 digits; digits with spaces/dashes.
- Deal method: none, Meetup only, Delivery only, both.
- Conditional fields: Meetup location free text rejected; Delivery fee 0, 500,
  501; uncheck clears + hides.
- Server-side: same rule rejected via API when client bypassed.
- Button disabled state; scroll-to-first-invalid order.
- Changing category keeps other fields.

## Deliberately NOT specified (must not be asserted as fact)
- Max photo resolution/dimensions, minimum file size.
- Whether description rule also blocks emails or URLs (only phone numbers).
- Exact visual of the "Free" label beyond the text "Free".
- Behaviour when 8+ digits appear in the **title** (rule is description-only).
- Draft autosave: explicitly out of scope; any test of it is **Unsupported**.

## Traps
- Testing that GIFs are accepted → contradicts the table.
- Asserting the title phone-number check → **Unsupported**.
- Asserting price allows decimals → contradicts the table.
