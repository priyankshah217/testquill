# PRD — Guest Checkout for Delivery Listings

**Team:** Checkout · **Target release:** Q1 · **Reviewers:** Payments, Risk, Growth

## 1. Overview

New visitors drop off when forced to sign up before buying. Guest checkout lets
a visitor buy a delivery-enabled listing with just an email and a card. To
limit fraud exposure, guest orders are capped at **$500 per order**.

## 2. Scope

In scope: listings with Delivery enabled and a fixed price (no offers).
Out of scope: Meetup-only listings, listings bought via an accepted offer,
digital goods.

## 3. User flow

1. Visitor (not logged in) taps **Buy now** on an eligible listing.
2. A sheet offers **Continue as guest** or **Log in**.
3. Guest enters: email (required), full name (required), phone (required),
   delivery address (required).
4. Guest enters card details. Supported: Visa, Mastercard.
5. Guest reviews the order summary (item price + delivery fee = total) and taps
   **Pay**.
6. On success, guest sees an order confirmation screen with an order number,
   and receives a confirmation email.

## 4. Payment & risk rules

- Guest order total (item price + delivery fee) must not exceed **$300**. If it
  does, the **Continue as guest** option is hidden and only **Log in** is shown.
- A single email address can place at most **3 guest orders in 24 hours**.
  The 4th attempt is blocked with: *"You've reached the guest order limit.
  Log in or create an account to continue."*
- Card payment uses 3-D Secure. A failed 3DS challenge shows *"Payment could
  not be verified. Try another card."* and no order is created.

## 5. Post-purchase

- The confirmation email contains a **Track order** link that works without
  logging in.
- After purchase, the guest is shown an optional **Create account** prompt
  pre-filled with their email. If they create an account, the guest order is
  linked to it.

## 6. Seller side

- The seller sees the order like any other order, with the buyer shown as
  "Guest buyer" plus the name entered.
- The listing status changes to **Sold** once payment succeeds.

## 7. Metrics

Guest checkout conversion rate; % of guests who create an account post-purchase.
