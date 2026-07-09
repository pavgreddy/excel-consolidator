import pandas as pd
import os

def generate_dummy_data():
    os.makedirs("dummy_data", exist_ok=True)

    # File 1: Purchasing data
    purchasing = pd.DataFrame({
        "Item Code": ["ITM001", "ITM002", "ITM003", "ITM001", "ITM004"],
        "Vendor": ["ABC Suppliers", "XYZ Corp", "ABC Suppliers", "PQR Ltd", "XYZ Corp"],
        "Purchase Price": [150.00, 230.50, 150.00, 148.00, 310.00],
        "Quantity": [100, 50, 200, 150, 75],
        "Purchase Date": ["2024-01-15", "2024-01-18", "2024-02-10", "2024-02-20", "2024-03-05"],
        "Invoice No": ["INV001", "INV002", "INV003", "INV004", "INV005"]
    })

    # File 2: Sales data (intentionally different column names)
    sales = pd.DataFrame({
        "SKU": ["ITM001", "ITM002", "ITM001", "ITM003", "ITM004", "ITM002"],
        "Customer": ["Retail Co", "Wholesale Ltd", "Retail Co", "Mega Store", "Retail Co", "Wholesale Ltd"],
        "Sale Price": [200.00, 300.00, 195.00, 210.00, 400.00, 295.00],
        "Units Sold": [50, 30, 80, 40, 25, 20],
        "Sale Date": ["15-01-2024", "18-01-2024", "05-02-2024", "12-02-2024", "08-03-2024", "15-03-2024"],
        "Invoice Number": ["SINV001", "SINV002", "SINV003", "SINV004", "SINV005", "SINV006"]
    })

    # File 3: Inventory data (intentionally different column names)
    inventory = pd.DataFrame({
        "Material ID": ["ITM001", "ITM002", "ITM003", "ITM004", "ITM005"],
        "Product Name": ["Steel Rod", "Copper Wire", "Aluminium Sheet", "Iron Bolt", "Plastic Cap"],
        "Stock Quantity": [500, 200, 300, 150, 1000],
        "Unit Cost": [145.00, 225.00, 155.00, 305.00, 50.00],
        "Last Updated": ["2024-03-01", "2024-03-01", "2024-03-01", "2024-03-01", "2024-03-01"],
        "Warehouse": ["WH-A", "WH-B", "WH-A", "WH-C", "WH-B"]
    })

    # File 4: Vendor data (messy - has duplicates and missing values)
    vendors = pd.DataFrame({
        "Supplier Name": ["ABC Suppliers", "XYZ Corp", "PQR Ltd", "ABC Suppliers", None],
        "Contact": ["abc@email.com", "xyz@email.com", "pqr@email.com", "abc@email.com", "unknown@email.com"],
        "Payment Terms": ["30 days", "45 days", "30 days", "30 days", "60 days"],
        "Rating": [4.5, 3.8, 4.2, 4.5, None],
        "Category": ["Raw Material", "Electronics", "Raw Material", "Raw Material", "Packaging"]
    })

    purchasing.to_excel("dummy_data/purchasing.xlsx", index=False)
    sales.to_excel("dummy_data/sales.xlsx", index=False)
    inventory.to_excel("dummy_data/inventory.xlsx", index=False)
    vendors.to_excel("dummy_data/vendors.xlsx", index=False)

    print("✅ Dummy data generated in dummy_data/ folder!")
    print(f"   - purchasing.xlsx ({len(purchasing)} rows)")
    print(f"   - sales.xlsx ({len(sales)} rows)")
    print(f"   - inventory.xlsx ({len(inventory)} rows)")
    print(f"   - vendors.xlsx ({len(vendors)} rows)")

if __name__ == "__main__":
    generate_dummy_data()