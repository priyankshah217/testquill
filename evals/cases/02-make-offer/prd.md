# PRD: Make an Offer

**Owner:** Marketplace Transactions squad
**Status:** Approved for build
**Platforms:** iOS, Android, Web

## 1. Background

Today buyers negotiate price through free-text chat. Sellers tell us they lose
track of who offered what, and buyers don't know whether their offer was seen.
We want a structured offer flow so both sides have a clear, trackable state.

## 2. Goals

- Increase the share of chats that end in a completed transaction.
- Give sellers a single place to see all pending offers on a listing.

**Non-goals:** automated price suggestions, bulk offers across listings, offers
on listings with fixed "no offers" pricing (see §3.1).

## 3. Requirements

### 3.1 Eligibility

- The "Make Offer" button appears on a listing only when:
  - the listing status is **Available**, and
  - the seller has **not** enabled "Fixed price — no offers" on the listing, and
  - the viewer is **not** the listing's seller.
- A buyer must be logged in to make an offer. Tapping "Make Offer" while logged
  out takes the buyer to login and returns them to the offer sheet afterwards.

### 3.2 Making an offer

- The offer sheet shows the listing price and a numeric amount field,
  pre-filled with the listing price.
- Offer amount must be a whole number, **greater than 0** and **no higher than
  the listing price**.
- Offers below **50% of the listing price** are allowed but show the inline
  warning: *"This offer is much lower than the asking price. The seller may be
  less likely to accept."* The buyer can still submit.
- A buyer can have only **one pending offer per listing**. If they already
  have one, the button reads "View your offer" instead of "Make Offer".
- Submitting an offer posts a system message in the buyer–seller chat:
  *"[Buyer] offered $X"*. If no chat exists, one is created.

### 3.3 Seller response

- The seller can **Accept**, **Decline**, or **Counter** a pending offer.
- **Accept:** offer status becomes *Accepted*. All other pending offers on the
  same listing are automatically *Declined*, and those buyers see a system
  message: *"This item has been reserved for another buyer."* The listing
  status changes to **Reserved**.
- **Decline:** offer status becomes *Declined*. The buyer may make a new offer.
- **Counter:** the seller enters a counter amount (same validation as §3.2,
  but it must be **higher than the buyer's offer**). The buyer can Accept or
  Decline the counter. Only **one counter round** is allowed; the buyer cannot
  counter a counter.

### 3.4 Expiry

- A pending offer (or pending counter) expires **48 hours** after it was sent
  if there is no response. Status becomes *Expired* and both parties see a
  system message: *"This offer has expired."*
- After expiry the buyer may make a new offer.

### 3.5 Withdrawal

- The buyer can withdraw a pending offer at any time before the seller
  responds. Status becomes *Withdrawn*.
- A buyer cannot withdraw an offer that has been accepted.

### 3.6 Seller offer inbox

- On their own listing, the seller sees an "Offers (N)" entry, where N is the
  count of *pending* offers.
- The inbox lists offers sorted by **amount, highest first**; ties are broken
  by earliest submitted.

### 3.7 Notifications

- Seller receives a push notification on every new offer.
- Buyer receives a push notification when their offer is accepted, declined,
  countered, or expires.

## 4. Analytics

Fire `offer_submitted`, `offer_accepted`, `offer_declined`, `offer_countered`,
`offer_expired`, `offer_withdrawn` with `listing_id`, `offer_amount`, and
`listing_price`.
