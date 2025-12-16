# Wolfson Brands – Power BI Dashboard Build Guide (theo Blueprint)

Tài liệu này chuyển blueprint thành checklist thao tác trong Power BI Desktop.

## 0) Files đầu vào (đã chuẩn bị sẵn)
- websales_coupon_merged_cleaned.csv (fact orders, 1 row = 1 order)
- dim_date.csv
- dim_* (shop/brand/company/country/payment/campaign/coupon)
- rfm_customer_table.csv + rfm_target_list.csv
- fact_order_skus.csv + sku_summary.csv + sku_pair_rules_top200.csv
- missing_profile_current.csv + outlier_profile_iqr_key_metrics.csv + audit_top_orders_by_order_total_gbp.csv
- powerbi_measures_dax.txt + wolfson_theme.json

## 1) Import & Data types (Power Query)
1. Get data → Text/CSV → import `websales_coupon_merged_cleaned.csv` đặt tên **FactOrders**.
2. Đổi kiểu dữ liệu (khuyến nghị):
   - IDs: boss_order_id, shop_order_id, Customer_ID, shipper_id → Text
   - Dates: order_date, completed_date, valid_from, expires → Date
   - Times: order_time, completed_time → Time
   - Metrics: *_gbp, Order Total (GBP), Refund (GBP), Discount_rate → Decimal number
   - Flags: has_coupon → True/False
3. Import các bảng dim_*.csv (tên theo file). Import dim_date.csv đặt tên **DimDate**.

## 2) Model (Star schema)
Tạo relationships (Many-to-one, single direction từ dim → fact):
- DimDate[Date] → FactOrders[order_date] (nếu FactOrders[order_date] là Date)
- dim_shop[shop] → FactOrders[shop]
- dim_brand[Brands] → FactOrders[Brands]
- dim_company[Company] → FactOrders[Company]
- dim_country[shipping_country] → FactOrders[shipping_country]
- dim_payment[payment_method] → FactOrders[payment_method]
- dim_campaign[campaign_type_clean] → FactOrders[campaign_type_clean]
- dim_coupon[coupon_code] → FactOrders[coupon_code]

> Mark as Date table: chọn DimDate → Table tools → Mark as date table → Date.

## 3) Measures (DAX)
- Model view → New measure → copy toàn bộ nội dung trong `powerbi_measures_dax.txt`.
- Kiểm tra tên bảng/cột khớp thực tế (nếu Power BI tự đổi tên cột có dấu ngoặc).

## 4) Global slicers (áp dụng cho toàn report)
Theo blueprint: Date range, Company, Brand, Shop, Country, has_coupon, campaign_type_clean. fileciteturn1file5

Gợi ý:
- Dùng slicer Date (Between) từ DimDate[Date]
- Các slicer khác: dropdown (single select OFF)

## 5) Pages theo Blueprint (6 trang)

### PAGE 1 — Executive Overview
Theo blueprint: KPI cards + trend + Top contributors + Geo. fileciteturn1file5
- KPI cards: [Net Revenue (GBP)], [Orders], [AOV (GBP)], [YoY Net Revenue %], [Refund Rate], [Coupon Usage %]
- Line chart: DimDate[YearMonth] vs [Net Revenue (GBP)]
- Bar Top 10: Brands hoặc shop theo [Net Revenue (GBP)] (Top N filter)
- Map/Bar: shipping_country theo [Net Revenue (GBP)]
- Drilldown hierarchy: Brands → shop → shipping_country

### PAGE 2 — Revenue Drivers & Operational Health
Theo blueprint: Matrix + Decomposition Tree + trend refund rate. fileciteturn1file3
- Matrix: Rows = shop; Values = [Net Revenue (GBP)], [Orders], [AOV (GBP)], [Refund (GBP)], [Refund Rate], [Net Sale Less Refund (GBP)]
- Decomposition Tree: Analyze = [Net Revenue (GBP)]; Explain by = Brands, shop, shipping_country, payment_method
- Line chart: DimDate[YearMonth] vs [Refund Rate]
- Drillthrough: từ Shop → Shop Detail Page (nếu làm thêm 1 trang detail)

### PAGE 3 — Promotion & Coupon Optimisation
Theo blueprint: campaign performance + coupon trend + scatter. fileciteturn1file3
- KPI cards: [Coupon Usage %], [Net Revenue (Coupon)], [Net Revenue (No Coupon)], [Weighted Avg Discount Rate], [AOV (Coupon)], [AOV (No Coupon)]
- Bar: campaign_type_clean theo [Net Revenue (GBP)] (Top N)
- Line/Area: DimDate[YearMonth] vs [Coupon Usage %]
- Scatter: X = Discount_rate; Y = [AOV (GBP)] hoặc AOV (Coupon); Details/Legend = campaign_type_clean
- Drilldown Campaign → coupon_code (add hierarchy: campaign_type_clean → coupon_code)

**Metric switch (Bookmark/Selector)**: tạo bảng rời MetricSelector = {"Revenue","AOV","Coupon%"} và 1 measure SWITCH để đổi metric trong bar chart.

### PAGE 4 — Customer Intelligence (RFM + K-Means)
Theo blueprint: Treemap + bar + target list. fileciteturn1file2
- Import `rfm_customer_table.csv` đặt tên **DimCustomerRFM**
- Relationship: DimCustomerRFM[Customer_ID] → FactOrders[Customer_ID] (Many-to-one)
- KPI cards: [Known Customers], [Repeat Rate (Known)], Customer ID Coverage %, [Net Revenue (GBP)] by segment
- Treemap: Group = RFM_Segment; Values = SUM(DimCustomerRFM[monetary]) hoặc #customers
- Bar: RFM_Segment vs SUM(DimCustomerRFM[monetary])
- Table: dùng `rfm_target_list.csv` (hoặc filter RFM_Segment in visual) hiển thị Customer_ID, last_order_date, monetary, frequency, recency_days
- Filter mặc định Year >= 2023 (page filter) để phản ánh coverage như blueprint. fileciteturn1file2
- Drillthrough Segment → Customer list → Order history (optional)

### PAGE 5 — Products & Market Basket
Theo blueprint: Top SKUs + bundles/rules. fileciteturn1file2
- Import `fact_order_skus.csv` (FactOrderSKUs) và `sku_pair_rules_top200.csv` (DimSkuRules)
- Relationship: FactOrders[boss_order_id] → FactOrderSKUs[boss_order_id] (1-to-many)
- Bar Top 20 SKUs: sku vs DISTINCTCOUNT(boss_order_id)
- Matrix/Table rules: antecedent, consequent, support, confidence, lift (Top by lift, with min pair count đã lọc)
- Drillthrough SKU → danh sách orders chứa SKU (dùng FactOrderSKUs → boss_order_id)

### PAGE 6 — Data Quality, Coverage & Outliers
Theo blueprint: missingness + outlier + audit table. fileciteturn1file1
- Import `missing_profile_current.csv`, `outlier_profile_iqr_key_metrics.csv`, `audit_top_orders_by_order_total_gbp.csv`
- KPI cards: Customer ID coverage, Coupon code coverage, Outlier % theo metric
- Bar: column_name vs missing_pct
- Bar: column vs pct_outliers_iqr
- Table audit: top orders theo Order Total (GBP) / net_revenue_gbp

## 6) Tooltip + Drillthrough (khuyến nghị)
- Tooltip page: 3 KPI nhỏ (Revenue, Orders, AOV, Coupon Usage) khi hover vào Brand/Shop/Campaign. fileciteturn1file1
- Drillthrough pages: Shop Detail, Campaign Detail, Segment Detail, SKU Detail.

## 7) Xuất bản & chia sẻ link (Power BI Service)
1. File → Publish → chọn workspace.
2. Vào workspace → report → Share hoặc tạo App để share link nội bộ.
3. Nếu muốn share công khai: cần cấu hình tenant/permissions của tổ chức (thường bị hạn chế).