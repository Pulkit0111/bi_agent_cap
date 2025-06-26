static_schema = """
    Table: ProductData
        - Column: Branchname & Data Type: NVARCHAR
        - Column: Productid & Data Type: BIGINT
        - Column: ProductName & Data Type: NVARCHAR
        - Column: stock & Data Type: NUMERIC
        - Column: ProductRate & Data Type: MONEY
        - Column: CATEGORY & Data Type: NVARCHAR
        - Column: BRAND & Data Type: NVARCHAR
        - Column: MODEL & Data Type: NVARCHAR
        - Column: COLOR & Data Type: NVARCHAR
        - Column: SUBCATEGORY & Data Type: VARCHAR
        - Column: FABRIC & Data Type: VARCHAR
        - Column: SIZE & Data Type: VARCHAR
        - Column: SHADE & Data Type: VARCHAR
        - Column: DEPARTMENT & Data Type: VARCHAR
        - Column: STYLE & Data Type: VARCHAR
        - Column: ReorderLevel & Data Type: DECIMAL
        - Column: ReorderQuantity & Data Type: DECIMAL
        - Column: LastPurchaseDate & Data Type: DATETIME
        - Column: CPU & Data Type: MONEY
        - Column: LastPurchasedHowManyDaysAgo & Data Type: INT
        - Column: Supplier & Data Type: NVARCHAR
        
        Table: SalesData
        - Column: branchid & Data Type: INT
        - Column: BranchName & Data Type: NVARCHAR
        - Column: Productid & Data Type: BIGINT
        - Column: productname & Data Type: NVARCHAR
        - Column: SaleBillNumber & Data Type: BIGINT
        - Column: SaleBillDate & Data Type: DATETIME
        - Column: SaleQuantity & Data Type: NUMERIC
        - Column: SaleRate & Data Type: MONEY
        - Column: SaleDiscountAmount & Data Type: FLOAT
        - Column: SaleTaxAmount & Data Type: MONEY
        - Column: SaleAmount & Data Type: MONEY
        - Column: SaleCustomerName & Data Type: NVARCHAR
        - Column: SaleCustomerCity & Data Type: NVARCHAR
        - Column: Salesman & Data Type: NVARCHAR
        - Column: BeforeTaxSaleAmount & Data Type: MONEY
    """