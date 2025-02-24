# posX

## Intro

Within the scope of this assignment, we are going to design a service with HTTP API for Point of Sales (POS) system.

## User Stories

> As a *store manager*, I would like to register goods and their prices so that, I can operate my store.

> As a *store manager*, I would like to see a list of goods so that, I can check assortments offered by my store.

> As a *store manager*, I would like to check and update prices so that, I can control my priceing policy.

> As a *store manager*, I would like to create "buy n get n" campaigns so that, I can encourage customers to visit my store.

> As a *store manager*, I would like to create "discount" campaigns so that, I can encourage customers to visit my store.

> As a *store manager*, I would like to create "combo" campaigns so that, I can encourage customers to visit my store.

> As a *store manager*, I would like to make X reports so that, I can see the current state of the shift.
---
> As a *cashier*, I would like to open a new shift so that, I can start my working day.

> As a *cashier*, I would like to open a receipt so that, I can start serving customers.

> As a *cashier*, I would like to add goods to an open receipt so that, I can calculate how much the customer needs to pay.

> As a *cashier*, I would like to close the paid receipt so that, I can start serving the next customer.

> As a *cashier*, I would like to make Z reports so that, I can close my shift and go home.
---
> As a *customer*, I would like to see a receipt with all my items so that, I know how much I have to pay.

> As a *customer*, I would like to see discounted amount on my receipt so that, I know how much I have saved on the purchase.

> As a *customer*, I would like to pay in GEL, USD or EUR for a receipt so that, I can receive my items.

## Extra information

Discounts:
  - Specific items might have discounts.
  - Whole receipt might have a discount if it exceeds certain total amount.

Buy n get n:
  If user buys certain number of a specific product they might get something (or the same thing) as a gift.

Combo:
  If user buys certain proucts together they might get a discount.

Payment:
  Prices in the store are in national currency (GEL).
  To convert GEL to other currencies, use any public exchange rate API of your choice.

X Report contains information about:
  - number of receipts in the shift
  - total number of each items sold (broken down by item id)
  - Revenue (broken down by currency)

Sales report contains information about:
  - Sales (liftime) broken down by currency

## Technical Details

- UI is out of scope.
- Authorization is out of scope (all api endpoints are unrestricted).
- Use [SQLite](https://docs.python.org/3/library/sqlite3.html) for persistence.
- Use [FastAPI](https://fastapi.tiangolo.com/) for implementing API.

## API Reference

Note, following is a draft of SUGGESTED API endpoints to get you started. Request and response structures are left for you to figure out. You may use all, some, or none of them.

- Create product `POST /products`
- List products `GET /products`
- Update product `PATCH /products/{product_id}`
- Create campaign `POST /campaigns`
- Deactivate campaign `DELETE /campaigns/{campaign_id}`
- List campaigns `GET /campaigns`
- Create receipt `POST /receipts`
- Add item `POST /receipts/{receipt_id}/products`
- Calculate payment (in currency) `POST /receipts/{receipt_id}/quotes`
- Add payment to the receipt `POST /receipts/{receipt_id}/payments`
- Fetch a state report for open shift `GET /x-reports?shift_id={shift_id}`
- Fetch liftime sales report `GET /sales`

## Linting/formatting

- Format and lint your code using `ruff`
- Check your static types with `mypy`

## Testing

Provide automated tests that will falsify regressions (change in behaviour) in your software artifacts.

## Grading

We will not grade solutions:
  - without decomposition
  - with needlessly long methods or classes
  - with code duplications

In all these cases you will automatically get 0% so, we sincerely ask you to 
not make a mess of your code and not put us in an awkward position.

## Disclaimer

We reserve the right to resolve ambiguous requirements (if any) as we see fit just like a real-life stakeholder would.
So, do not assume anything, ask for clarifications.