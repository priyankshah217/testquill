# Spec: Create Listing — Field Validation v2

Status: ready for dev · Applies to: Web + Apps · Supersedes: Listing Validation v1

## Summary

We're tightening validation on the Create Listing form to cut down on junk
listings and support tickets. All rules below apply both client-side (inline,
on blur) and server-side (on submit). Server is the source of truth: if the
client is bypassed, the API must reject with the same message.

## Field rules

| Field | Required | Rule | Error message |
|---|---|---|---|
| Photos | Yes | 1 to 10 photos. JPG, PNG, or HEIC only. Max 10 MB each. | "Add at least 1 photo" / "You can add up to 10 photos" / "Only JPG, PNG or HEIC files are supported" / "Each photo must be under 10 MB" |
| Title | Yes | 5–80 characters after trimming whitespace. No more than 3 consecutive identical characters. | "Title must be 5–80 characters" / "Title can't repeat the same character more than 3 times in a row" |
| Category | Yes | Must be a **leaf** category (no children). | "Choose a more specific category" |
| Condition | Yes | One of: Brand new, Like new, Lightly used, Well used, Heavily used. | "Select a condition" |
| Price | Yes | Integer 0–9,999,999. 0 is allowed and displays as "Free". No decimals. | "Enter a price between 0 and 9,999,999" |
| Description | No | Max 4,000 characters. Must not contain a phone number (8+ consecutive digits, ignoring spaces and dashes). | "Description can be up to 4,000 characters" / "For your safety, don't include phone numbers in the description" |
| Deal method | Yes | At least one of: Meetup, Delivery. | "Choose at least one deal method" |
| Meetup location | If Meetup selected | Must be picked from the location search results (not free text). | "Pick a meetup location from the list" |
| Delivery fee | If Delivery selected | Integer 0–500. | "Delivery fee must be between 0 and 500" |

## Behaviour notes

- The **List it** button is disabled until all required fields pass client-side
  validation.
- Errors are shown inline below the field. On submit failure, the page scrolls
  to the **first** invalid field (top-to-bottom order as in the table).
- Unchecking Meetup clears and hides the Meetup location field. Unchecking
  Delivery clears and hides the Delivery fee field.
- Changing the category does **not** clear other fields.
- Draft autosave is out of scope for this release.

## Edge rules

- Title trimming happens before the length check: "   abc   " is 3 characters
  and fails.
- A photo rejected for size or type does not count toward the 10-photo limit.
- The phone-number rule counts digits after stripping spaces and dashes:
  "9123 4567" and "9123-4567" are both 8 digits and must be rejected.
  "Model 1234567" (7 digits) is allowed.
