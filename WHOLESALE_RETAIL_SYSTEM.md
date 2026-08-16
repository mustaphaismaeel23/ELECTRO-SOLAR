# Wholesale & Retail System - Implementation Guide

## Overview
Your ElectroSolar POS system now supports both wholesale and retail operations with separate pricing tiers and customer management.

---

## Key Features Added

### 1. **Dual Pricing System**
- Each product now has THREE price tiers:
  - **Cost Price**: Purchase cost from supplier
  - **Retail Price**: Standard selling price for retail customers
  - **Wholesale Price**: Discounted price for bulk/wholesale buyers
  
### 2. **Customer Types**
- **Retail**: Walk-in and regular customers (uses retail pricing)
- **Wholesale**: Bulk buyers, distributors, resellers (uses wholesale pricing)
- Each customer can be classified when created or edited

### 3. **Smart POS System**
- Sales type selector on POS screen (Retail/Wholesale)
- Product tiles show both retail and wholesale prices
- Prices automatically adjust based on selected sales type
- Customer type automatically sets the sales type when selected

### 4. **Sales Analytics**
- All sales tracked with transaction type (Retail/Wholesale)
- New reports to compare wholesale vs retail performance:
  - **Wholesale vs Retail**: Side-by-side comparison
  - **Wholesale Sales**: Wholesale transactions only
  - **Retail Sales**: Retail transactions only

---

## How to Use

### Setting Up Products with Wholesale Prices

1. Go to **Products** menu
2. Click on a product to edit or create a new one
3. Fill in:
   - **Cost Price**: Your purchase price from supplier
   - **Retail Price**: Price for regular customers
   - **Wholesale Price**: Discounted price for bulk orders
4. Save the product

**Example:**
- Cost: ₦45,000
- Retail: ₦58,000 (28% markup)
- Wholesale: ₦50,000 (11% markup, for bulk)

### Managing Customers

#### Creating a Wholesale Customer:
1. Go to **Customers**
2. Click **+ Add Customer**
3. Fill details:
   - Name: "Emeka Solar Ltd"
   - **Type**: Select **Wholesale**
   - Phone, Email, Address
   - Credit Limit (higher for wholesale)
4. Save

#### Creating a Retail Customer:
1. Go to **Customers**
2. Click **+ Add Customer**
3. Fill details:
   - Name: "John Doe"
   - **Type**: Select **Retail**
   - Other details (optional for walk-in)
4. Save

### Making a Sale

#### Retail Sale:
1. Go to **POS** (Point of Sale)
2. Ensure **Sales Type** selector shows **"Retail Sales"**
3. Add products to cart (prices shown are retail)
4. Select customer or enter walk-in name
5. Enter amount paid
6. Click **Complete Sale**

#### Wholesale Sale:
1. Go to **POS**
2. Change **Sales Type** selector to **"Wholesale Sales"**
3. Product prices automatically update to wholesale prices
4. Select a wholesale customer or enter name
5. Enter amount paid
6. Click **Complete Sale**

**Pro Tip**: When you select a wholesale customer, the system will automatically use wholesale pricing!

---

## Reports & Analytics

### New Wholesale/Retail Reports

Go to **Reports** and select from:

#### 1. **Wholesale vs Retail** (NEW)
- Compares total transactions, revenue, and outstanding balances
- See performance split by type
- Example output:
  ```
  Retail:    45 transactions, ₦450,000 revenue, ₦12,000 outstanding
  Wholesale: 8 transactions,  ₦320,000 revenue, ₦45,000 outstanding
  ```

#### 2. **Wholesale Sales** (NEW)
- Daily breakdown of wholesale transactions
- Filter by date range
- Track wholesale revenue trends

#### 3. **Retail Sales** (NEW)
- Daily breakdown of retail transactions
- Compare with wholesale
- Analyze retail market performance

### Existing Reports Now Enhanced:
- **Daily Transactions**: Shows sales type for each transaction
- **Customer Debt**: Shows customer type (Retail/Wholesale)
- All other reports continue as before

---

## Sales History Filtering

In the **Sales** section:
- New dropdown filter: **All Types**, **Retail Only**, **Wholesale Only**
- Each sale shows its type with a badge:
  - 🔵 **Wholesale** (blue badge)
  - ⚪ **Retail** (grey badge)

---

## Database Changes

The following changes were made to support this system:

### Products Table
- Added `wholesale_price REAL` column
- Existing `selling_price` now specifically for retail

### Customers Table
- Added `customer_type TEXT` column (values: 'retail', 'wholesale')
- Defaults to 'retail' for existing customers

### Sales Table
- Added `sales_type TEXT` column (values: 'retail', 'wholesale')
- Tracks which type each transaction is

---

## Business Logic

### Pricing Rules

1. **Retail Sales**:
   - Uses `selling_price` from products
   - Available to all customers
   - No minimum order

2. **Wholesale Sales**:
   - Uses `wholesale_price` (if set)
   - Falls back to `selling_price` if no wholesale price exists
   - Typically higher volume, lower margin

### Credit Management

- Wholesale customers usually get higher credit limits
- Retail customers have lower limits
- All credit calculations work the same way

### Stock Tracking

- Stock is decreased for both retail and wholesale sales
- No separate inventory tracking by type
- Same stock movements apply

---

## Sample Data

The system comes with sample data:

### Sample Wholesale Customers:
- **Emeka Solar Ltd**: ₦1,000,000 credit limit
- **Bright Electrical**: ₦500,000 credit limit
- **Green Energy Co.**: ₦750,000 credit limit

### Sample Products (with wholesale prices):
- 150W Solar Panel: Retail ₦58,000 → Wholesale ₦50,000
- 100Ah Battery: Retail ₦50,000 → Wholesale ₦44,000
- Inverter 1.5kVA: Retail ₦72,000 → Wholesale ₦64,000

---

## Best Practices

### For Efficient Wholesale/Retail Management:

1. **Pricing Strategy**:
   - Set wholesale prices at 80-90% of retail
   - Encourages bulk purchases
   - Maintain profitability

2. **Customer Management**:
   - Clearly mark customers as wholesale/retail
   - Set appropriate credit limits
   - Track wholesale separately for analysis

3. **Sales Process**:
   - Select correct sales type before adding items
   - Verify customer type is correct
   - Review pricing before completing

4. **Reporting**:
   - Run Wholesale vs Retail report monthly
   - Track which type is more profitable
   - Adjust pricing strategy based on data

5. **Inventory**:
   - Monitor stock by popularity (retail vs wholesale)
   - Adjust supplier orders based on demand type
   - Keep wholesale stock levels higher for bulk orders

---

## Troubleshooting

### Prices Not Changing?
- Make sure you set `Wholesale Price` when editing products
- Verify sales type selector on POS
- Refresh the page

### Customer Type Not Saving?
- Ensure you selected the customer type dropdown
- Not all old customers may have type set (defaults to retail)
- Update existing customers to set their type

### Sales Type Shows Blank?
- Default sales type is "retail"
- Clear browser cache if selector doesn't load
- Check that JavaScript is enabled

---

## Future Enhancements

Consider these additions:
- Minimum order quantities for wholesale
- Volume-based discounts (tiers)
- Separate wholesale/retail inventory
- Customer-specific pricing
- Wholesale order scheduling
- Bulk discount calculator

---

## Quick Start Checklist

- [ ] Review existing products and add wholesale prices
- [ ] Update/add wholesale customers
- [ ] Train staff on POS sales type selector
- [ ] Test a wholesale transaction
- [ ] Test a retail transaction
- [ ] Review Wholesale vs Retail report
- [ ] Adjust pricing strategy if needed

---

**System Ready!** Your wholesale and retail system is fully operational. Start by updating product prices and then begin creating wholesale customers.

Need help? Review the specific sections above or check your product/customer management screens for the new fields.
