# Atlas General Store: company notes

These notes explain our sales export (`atlas_sales.xlsx`). They are written by the store owners for anyone analysing the file. Atlas General Store is a fictional company used as sample data.

## About the company

Atlas General Store is a small Ontario retail chain. We sell everyday products under one roof: groceries, household supplies, health and beauty products, office and school supplies, seasonal items and a small range of toys and games. Most customers are local households. We also serve business accounts: offices, clinics, schools, daycares and community organisations that buy supplies in larger quantities.

## Stores and channels

We operate four stores and an online shop:

- Toronto - Queen Street, our first and largest store.
- Mississauga.
- Hamilton.
- Ottawa.
- Online, launched in 2023. Online orders are shipped from the Mississauga store but are recorded under the store name "Online".

All stores are open seven days a week. Business accounts order on weekdays only and are attached to one home store.

## Column dictionary

The `Orders` sheet has one row per product line of an order.

| Column | Meaning |
|---|---|
| `order_id` | Order number. Sales orders start with `A`, return transactions start with `R`. One order can have several lines. |
| `order_date` | Date of the sale or of the return. |
| `store` | Store where the order was placed, or "Online". |
| `channel` | "In-store" or "Online". |
| `customer` | Customer name. Loyalty members appear as "Loyalty L-" followed by their card number. "Walk-in" means the customer did not use a loyalty card: it is not a single customer. |
| `customer_type` | "Retail" for households, "Business" for business accounts. |
| `product` | Product name. |
| `category` | One of: Grocery, Household, Health and beauty, Office and school, Seasonal, Toys and games. |
| `quantity` | Number of units. Negative on return lines. |
| `unit_price` | Price of one unit, in Canadian dollars, before sales tax. |
| `amount` | Line total in Canadian dollars, before sales tax: quantity times unit price. Negative on return lines. |

The `Targets` sheet has one row per store and per month: `month` (YYYY-MM), `store` and `target`, the sales target for that store and month in Canadian dollars, before sales tax. Targets were set at the start of each year from a normal-year plan plus 4%.

## Customers and loyalty

Households can join the free Atlas loyalty program at the till or online. A loyalty member keeps the same card number in every store. Online orders always require a loyalty account, so the online shop has no "Walk-in" customers.

Business accounts are opened by the store manager and invoiced monthly. A business account belongs to one home store.

## Store closures

The Toronto - Queen Street store was closed from March 3 to March 28, 2025 for a full renovation (new shelving, lighting and checkout area). The store reopened on March 29, 2025. During the closure, business accounts attached to Queen Street were asked to wait for the reopening; we did not transfer their orders to another store.

No other store has been closed for more than one day since September 2024.

## Pricing changes

On June 1, 2025, we raised grocery prices by about 5% after an increase from our main grocery supplier. Prices in the other categories did not change during the period covered by the file.

## Promotions

- **Black Friday weekend**: from Black Friday to the following Monday, in all stores and online. In 2024, from November 29 to December 2; in 2025, from November 28 to December 1.
- **Back to school**: in August and September, office and school supplies are featured at the front of every store.
- **Holiday season**: toys, games and gift wrap are featured from mid-November to December 24.

Promotions do not change the prices recorded in the file: discounts are given as loyalty points, which are not part of the export.

## Returns policy

In our stores, customers can return a product within 30 days with a receipt, for a full refund. A return is recorded as a separate transaction (order number starting with `R`), with a negative quantity and a negative amount, on the date of the return and in the store where the product is returned.

## Data notes

- **Online orders for July 2025 are missing from this export.** We moved the online shop to a new system that month, and the July orders were not included in the export. Online sales did happen in July 2025.
- The file starts on September 1, 2024 and ends on August 31, 2026.
- Amounts are before sales tax (HST) and do not include shipping fees.
