import type { ContextDocument, Dataset } from '../types';

export const EXAMPLE_CONTEXT: ContextDocument = {
  name: 'atlas_context.pdf',
  format: 'pdf',
  converted: true,
  tokens: 1100,
  mode: 'full',
  sections: [
    { id: 'D1', title: 'Atlas General Store: company notes' },
    { id: 'D2', title: 'About the company' },
    { id: 'D3', title: 'Stores and channels' },
    { id: 'D4', title: 'Column dictionary' },
    { id: 'D5', title: 'Customers and loyalty' },
    { id: 'D6', title: 'Store closures' },
    { id: 'D7', title: 'Pricing changes' },
    { id: 'D8', title: 'Promotions' },
    { id: 'D9', title: 'Returns policy' },
    { id: 'D10', title: 'Data notes' },
  ],
  removed_sections: [],
};

/** The response example of docs/contract.md, section 5 (real values of the Atlas sample data). */
export const UPLOAD_EXAMPLE: Dataset = {
  dataset_id: 'ds_3f9a1c2b7d4e8f01',
  file_name: 'atlas_sales.xlsx',
  sheets: ['Orders', 'Targets'],
  rows: 59764,
  columns: [
    { name: 'order_id', type: 'text' },
    { name: 'order_date', type: 'date' },
    { name: 'store', type: 'text' },
    { name: 'channel', type: 'text' },
    { name: 'customer', type: 'text' },
    { name: 'customer_type', type: 'text' },
    { name: 'product', type: 'text' },
    { name: 'category', type: 'text' },
    { name: 'quantity', type: 'number' },
    { name: 'unit_price', type: 'number' },
    { name: 'amount', type: 'number' },
  ],
  roles: {
    date: 'order_date',
    amount: 'amount',
    customer: 'customer',
    product: 'product',
    quantity: 'quantity',
    unit_price: 'unit_price',
    region: 'store',
    order_id: 'order_id',
    target: 'Targets.target',
  },
  preview: {
    columns: ['order_id', 'order_date', 'store', 'customer', 'product', 'quantity', 'unit_price', 'amount'],
    rows: [
      ['A0000092', '2024-09-03', 'Toronto - Queen Street', 'Lakeshore Dental Clinic', 'Notebooks, 5 pack', 27, 9.49, 256.23],
    ],
  },
  checks: [
    { id: 'roles', name: 'Column roles', status: 'ok', detail: 'Date, amount, customer and order columns identified', amount: null },
    { id: 'duplicates', name: 'Duplicate rows', status: 'warning', detail: '12 duplicate rows', amount: 176.83 },
    { id: 'amount_mismatch', name: 'Quantity x unit price differs from amount', status: 'warning', detail: '40 rows', amount: null },
    { id: 'name_variants', name: 'Same customer written several ways', status: 'warning', detail: 'Lakeshore Dental Clinic appears in 3 spellings', amount: null },
    { id: 'missing_months', name: 'Months without sales', status: 'warning', detail: 'Online: 2025-07', amount: null },
    { id: 'dates_out_of_range', name: 'Dates outside the period', status: 'warning', detail: '2 rows dated 2052', amount: null },
    { id: 'placeholder_customer', name: 'Placeholder customer', status: 'warning', detail: '"Walk-in" is not a single customer; excluded from customer metrics', amount: null },
    { id: 'returns', name: 'Returns', status: 'ok', detail: '805 return lines', amount: -13190.44 },
  ],
  region: 'ON',
  context: EXAMPLE_CONTEXT,
};
