import pandas as pd

# Path to the raw dataset
file_path = "global_superstore_raw.csv"

# Load dataset
df = pd.read_csv(file_path)

print("=" * 60)
print("METRICMIND DATASET VALIDATION")
print("=" * 60)

# 1. Number of rows and columns
print("\n1. Dataset Shape")
print(df.shape)

# 2. Column names
print("\n2. Columns")
for column in df.columns:
    print(column)

# 3. Data types
print("\n3. Data Types")
print(df.dtypes)

# 4. Missing values
print("\n4. Missing Values")
print(df.isnull().sum())

# 5. Duplicate rows
print("\n5. Duplicate Rows")
print(df.duplicated().sum())

# 6. First five rows
print("\n6. Sample Data")
print(df.head())

# 7. Numerical statistics
print("\n7. Numerical Statistics")
print(df.describe())


print("Total rows:", len(df))
print("Unique Order IDs:", df["Order.ID"].nunique())
print("Unique Product IDs:", df["Product.ID"].nunique())
print("Unique Customers:", df["Customer.ID"].nunique())


order_counts = df["Order.ID"].value_counts()

print(order_counts.head(10))

print("Duplicate Row IDs:", df["Row.ID"].duplicated().sum())

print("Sales:")
print(df["Sales"].describe())

print("\nProfit:")
print(df["Profit"].describe())

print("\nQuantity:")
print(df["Quantity"].describe())

print("\nDiscount:")
print(df["Discount"].describe())

print("\nShipping Cost:")
print(df["Shipping.Cost"].describe())

print(df["Order.Date"].head(10))
print(df["Ship.Date"].head(10))

print(df["Order.Date"].dtype)
print(df["Ship.Date"].dtype)

print(df["Region"].value_counts())
print(df["Market"].value_counts())
print(df["Country"].nunique())
print(
    df[df["Region"].astype(str).str.contains("Europe", case=False, na=False)]
    .shape
)
print(
    df[df["Market"].astype(str).str.contains("Europe", case=False, na=False)]
    .shape
)

europe = df[
    df["Region"].astype(str).str.contains("Europe", case=False, na=False)
]

print(europe.shape)

europe_sales = europe["Sales"].sum()
europe_profit = europe["Profit"].sum()

europe_margin = (europe_profit / europe_sales) * 100

print("European Sales:", europe_sales)
print("European Profit:", europe_profit)
print("European Profit Margin:", europe_margin)


eu = df[df["Market"] == "EU"]

print("EU rows:", len(eu))
print("EU sales:", eu["Sales"].sum())
print("EU profit:", eu["Profit"].sum())

if eu["Sales"].sum() != 0:
    print(
        "EU profit margin:",
        (eu["Profit"].sum() / eu["Sales"].sum()) * 100
    )

eu_by_year = (
    eu.groupby("Year")
      .agg(
          Sales=("Sales", "sum"),
          Profit=("Profit", "sum"),
          Orders=("Order.ID", "nunique")
      )
)

eu_by_year["Profit_Margin"] = (
    eu_by_year["Profit"] /
    eu_by_year["Sales"] * 100
)

print(eu_by_year)

df["Order.Date"] = pd.to_datetime(df["Order.Date"])

eu = df[df["Market"] == "EU"].copy()

eu["Quarter"] = eu["Order.Date"].dt.to_period("Q").astype(str)

eu_by_quarter = (
    eu.groupby("Quarter")
      .agg(
          Sales=("Sales", "sum"),
          Profit=("Profit", "sum"),
          Orders=("Order.ID", "nunique")
      )
)

eu_by_quarter["Profit_Margin"] = (
    eu_by_quarter["Profit"] /
    eu_by_quarter["Sales"] * 100
)

print(eu_by_quarter)