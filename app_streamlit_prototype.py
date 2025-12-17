import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from pathlib import Path
from typing import Optional

# ============================================================
# Page configuration
# ============================================================
st.set_page_config(
    page_title="Wolfson Brands Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Theme control (Auto / Light / Dark)
# - Auto uses CSS prefers-color-scheme for the UI.
# - For charts, Auto uses Streamlit's theme base as best-effort.
#   If charts look off, switch to Light/Dark manually.
# ============================================================
with st.sidebar.expander("⚙️ Display settings", expanded=False):
    theme_mode = st.selectbox("Theme", ["Auto", "Light", "Dark"], index=0, key="ui_theme_mode")

def _css_tokens_light() -> str:
    return """
    :root{
      color-scheme: light;
      --bg:#ffffff;
      --text:#111827;
      --muted:#6b7280;
      --card:#ffffff;
      --sidebar:#fafafa;
      --border:#d1d5db;
      --border_soft:#e5e7eb;
      --thead:#f9fafb;
      --pill_bg: rgba(0,0,0,0.03);
    }
    """

def _css_tokens_dark() -> str:
    return """
    :root{
      color-scheme: dark;
      --bg:#0b1220;
      --text:#e5e7eb;
      --muted:#94a3b8;
      --card:#0f172a;
      --sidebar:#0b1220;
      --border:rgba(255,255,255,0.18);
      --border_soft:rgba(255,255,255,0.12);
      --thead:rgba(255,255,255,0.06);
      --pill_bg: rgba(255,255,255,0.06);
    }
    """

def inject_css(mode: str = "Auto") -> None:
    if mode == "Auto":
        tokens = _css_tokens_light() + """
        @media (prefers-color-scheme: dark){
        """ + _css_tokens_dark() + """
        }
        """
    elif mode == "Dark":
        tokens = _css_tokens_dark()
    else:
        tokens = _css_tokens_light()

    st.markdown(
        f"""
<style>
{tokens}

/* Base */
html, body, [data-testid="stAppViewContainer"], .stApp {{
  background: var(--bg) !important;
  color: var(--text) !important;
}}

/* Ensure text is not "faded" */
h1,h2,h3,h4,h5,h6, p, span, label, small, div {{
  color: var(--text) !important;
  opacity: 1 !important;
}}
[data-testid="stMarkdownContainer"] {{
  color: var(--text) !important;
  opacity: 1 !important;
}}

/* Hide Streamlit menu/footer only (keep header for sidebar toggle) */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* Layout padding */
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border_soft) !important;
}}
section[data-testid="stSidebar"] * {{
  color: var(--text) !important;
}}

/* Header card */
.report-header {{
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  background: var(--card);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 14px;
}}
.report-company {{ font-size: 14px; font-weight: 650; letter-spacing: .3px; color: var(--muted) !important; }}
.report-title {{ font-size: 26px; font-weight: 850; color: var(--text) !important; line-height: 1.1; margin-top: 2px; }}
.report-sub {{ font-size: 13px; color: var(--muted) !important; margin-top: 6px; }}
.report-meta {{ text-align: right; font-size: 13px; color: var(--muted) !important; }}
.report-meta .pill {{
  display: inline-block;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 6px 10px;
  background: var(--pill_bg);
}}

/* KPI boxes */
div[data-testid="stMetric"] {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
}}
div[data-testid="stMetric"] * {{ color: var(--text) !important; }}

/* Chart + dataframe borders */
div[data-testid="stPlotlyChart"],
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 10px 12px;
}}

/* Dataframe: readable in both themes */
div[data-testid="stDataFrame"] * {{ color: var(--text) !important; }}
div[data-testid="stDataFrame"] table {{ background: var(--card) !important; }}
div[data-testid="stDataFrame"] thead tr th {{
  background: var(--thead) !important;
  border-bottom: 1px solid var(--border_soft) !important;
}}
div[data-testid="stDataFrame"] tbody tr td {{
  background: var(--card) !important;
  border-bottom: 1px solid var(--border_soft) !important;
}}

/* Selects */
div[data-baseweb="select"] > div {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}}
div[data-baseweb="select"] * {{ color: var(--text) !important; }}

/* Tabs */
button[data-baseweb="tab"] {{
  font-size: 14px !important;
  padding: 10px 12px !important;
}}
button[data-baseweb="tab"] * {{
  color: var(--text) !important;
  opacity: 1 !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )

inject_css(theme_mode)

# ============================================================
# Plotly styling
# ============================================================
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

def get_is_dark(mode: str) -> bool:
    if mode == "Dark":
        return True
    if mode == "Light":
        return False
    # Auto: best-effort based on Streamlit theme base (may be None)
    base = (st.get_option("theme.base") or "light").lower()
    return base == "dark"

IS_DARK = get_is_dark(theme_mode)

def style_fig(fig, title: Optional[str] = None):
    """
    Apply a clean, professional style that works across Plotly versions.
    Fixes Plotly v6+ compatibility (title_font vs titlefont).
    """
    if IS_DARK:
        template = "plotly_dark"
        paper = "#0f172a"
        plot = "#0f172a"
        font = "#e5e7eb"
        axis_line = "rgba(255,255,255,0.55)"
        grid = "rgba(255,255,255,0.10)"
    else:
        template = "plotly_white"
        paper = "white"
        plot = "white"
        font = "#111827"
        axis_line = "rgba(0,0,0,0.55)"
        grid = "rgba(0,0,0,0.10)"

    fig.update_layout(
        template=template,
        paper_bgcolor=paper,
        plot_bgcolor=plot,
        margin=dict(l=12, r=12, t=46, b=12),
        title=dict(text=title or "", x=0.01, xanchor="left", font=dict(color=font)),
        font=dict(size=13, color=font),
        legend=dict(title=None),
    )

    common_axis = dict(
        showline=True,
        linewidth=1.1,
        linecolor=axis_line,
        mirror=True,
        ticks="outside",
        ticklen=4,
        tickwidth=1,
        showgrid=True,
        gridwidth=0.7,
        gridcolor=grid,
        tickfont=dict(color=font),
    )

    # Plotly v6+ uses title_font; older uses titlefont
    try:
        fig.update_xaxes(**common_axis, title_font=dict(color=font))
        fig.update_yaxes(**common_axis, title_font=dict(color=font))
    except Exception:
        fig.update_xaxes(**common_axis, titlefont=dict(color=font))
        fig.update_yaxes(**common_axis, titlefont=dict(color=font))

    return fig

# ============================================================
# Paths + loaders
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data(show_spinner=False)
def read_csv_cached(name: str) -> pd.DataFrame:
    return pd.read_csv(BASE_DIR / name)

def load_optional(name: str) -> Optional[pd.DataFrame]:
    p = BASE_DIR / name
    if not p.exists():
        return None
    return read_csv_cached(name)

# ============================================================
# Load core data
# ============================================================
if "campaign_type_clean" in df.columns:
    df["campaign_type_clean"] = (
        df["campaign_type_clean"]
        .astype("string")
        .str.strip()
        .str.replace(r"(?i)^no coupon$", "No campaign", regex=True)
    )


# ============================================================
# Sidebar filters
# ============================================================
st.sidebar.header("Control Panel (Filters)")
st.sidebar.caption("If the sidebar is hidden, click the `>` button in the top-left corner to reopen it.")

year_months = sorted(df["YearMonth"].dropna().unique().tolist()) if "YearMonth" in df.columns else []
if not year_months:
    st.error("Column `YearMonth` is missing or empty in monthly_aggregates.csv.")
    st.stop()

ym_from, ym_to = st.sidebar.select_slider(
    "Year-Month range",
    options=year_months,
    value=(year_months[0], year_months[-1]),
    key="flt_yearmonth",
)

def multiselect(col: str, label: str, key: str):
    if col not in df.columns:
        return []
    opts = sorted([x for x in df[col].dropna().unique().tolist()])
    return st.sidebar.multiselect(label, opts, default=[], key=key)

company = multiselect("Company", "Company", "flt_company")
brand = multiselect("Brands", "Brand", "flt_brand")
shop = multiselect("shop", "Shop", "flt_shop")
country = multiselect("shipping_country", "Country", "flt_country")
campaign = multiselect("campaign_type_clean", "Campaign type", "flt_campaign")
has_coupon = st.sidebar.selectbox("Has coupon", ["All", True, False], index=0, key="flt_coupon")

f = df[(df["YearMonth"] >= ym_from) & (df["YearMonth"] <= ym_to)].copy()
for col, sel in [
    ("Company", company),
    ("Brands", brand),
    ("shop", shop),
    ("shipping_country", country),
    ("campaign_type_clean", campaign),
]:
    if sel and col in f.columns:
        f = f[f[col].isin(sel)]
if has_coupon != "All" and "has_coupon" in f.columns:
    f = f[f["has_coupon"] == has_coupon]

# ============================================================
# Report header
# ============================================================
st.markdown(
    f"""
<div class="report-header">
  <div>
    <div class="report-company">WOLFSON BRANDS</div>
    <div class="report-title">E-commerce Performance Dashboard</div>
    <div class="report-sub">Multi-platform overview · KPI tracking · Drivers · Promotions · Customers · Basket · Data Quality</div>
  </div>
  <div class="report-meta">
    <div><span class="pill">Period: {ym_from} → {ym_to}</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# KPI helpers
# ============================================================
def kpi_sum(col: str) -> float:
    if col not in f.columns:
        return np.nan
    return float(np.nansum(f[col].to_numpy()))

def kpi_div(n: float, d: float) -> float:
    return float(n / d) if d else np.nan

orders = int(np.nansum(f["orders"].to_numpy())) if "orders" in f.columns else 0
net_rev = kpi_sum("net_revenue_gbp")
aov = kpi_div(net_rev, orders)
refund = kpi_sum("refund_gbp")
order_total = kpi_sum("order_total_gbp")
refund_rate = kpi_div(refund, order_total)

coupon_orders = (
    int(np.nansum(f.loc[f["has_coupon"] == True, "orders"].to_numpy()))
    if ("has_coupon" in f.columns and "orders" in f.columns)
    else 0
)
coupon_usage = kpi_div(coupon_orders, orders)

# ============================================================
# Tabs
# ============================================================
tabs = st.tabs(
    [
        "Executive Overview",
        "Revenue Drivers",
        "Promotions & Coupons",
        "Customer (RFM)",
        "Products & Basket",
        "Data Quality",
    ]
)

# ------------------ TAB 1 ------------------
with tabs[0]:
    st.subheader("Executive Overview")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Net Revenue (GBP)", f"{net_rev:,.0f}" if pd.notna(net_rev) else "—")
    c2.metric("Orders", f"{orders:,}")
    c3.metric("AOV (GBP)", f"{aov:,.2f}" if pd.notna(aov) else "—")
    c4.metric("Refund (GBP)", f"{refund:,.0f}" if pd.notna(refund) else "—")
    c5.metric("Refund Rate", f"{refund_rate:.2%}" if pd.notna(refund_rate) else "—")
    c6.metric("Coupon Usage", f"{coupon_usage:.2%}" if pd.notna(coupon_usage) else "—")

    by_ym = (
        f.groupby("YearMonth", as_index=False)
        .agg(net_revenue=("net_revenue_gbp", "sum"), orders=("orders", "sum"))
        .sort_values("YearMonth")
    )
    fig = style_fig(px.line(by_ym, x="YearMonth", y="net_revenue", markers=True), "Net Revenue Trend (by Month)")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t0_line_netrev_by_ym")

    left, right = st.columns(2)
    with left:
        if "Brands" in f.columns:
            top_brand = (
                f.groupby("Brands", as_index=False)
                .agg(net_revenue=("net_revenue_gbp", "sum"))
                .sort_values("net_revenue", ascending=False)
                .head(10)
            )
            fig = style_fig(px.bar(top_brand, x="Brands", y="net_revenue"), "Top 10 Brands (Net Revenue)")
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t0_bar_top_brand")
        else:
            st.info("Column `Brands` is missing in monthly_aggregates.csv.")

    with right:
        if "shipping_country" in f.columns:
            top_country = (
                f.groupby("shipping_country", as_index=False)
                .agg(net_revenue=("net_revenue_gbp", "sum"))
                .sort_values("net_revenue", ascending=False)
                .head(15)
            )
            fig = style_fig(px.bar(top_country, x="shipping_country", y="net_revenue"), "Top Countries (Net Revenue)")
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t0_bar_top_country")
        else:
            st.info("Column `shipping_country` is missing in monthly_aggregates.csv.")

# ------------------ TAB 2 ------------------
with tabs[1]:
    st.subheader("Revenue Drivers & Operational Health")

    if "shop" in f.columns:
        pivot = (
            f.groupby(["shop"], as_index=False)
            .agg(
                net_revenue=("net_revenue_gbp", "sum"),
                orders=("orders", "sum"),
                aov=("aov_gbp", "mean") if "aov_gbp" in f.columns else ("orders", "sum"),
                refund_rate=("refund_rate", "mean") if "refund_rate" in f.columns else ("orders", "sum"),
            )
            .sort_values("net_revenue", ascending=False)
        )
        st.dataframe(pivot, use_container_width=True)

    if "campaign_type_clean" in f.columns:
        by_campaign = (
            f.groupby("campaign_type_clean", as_index=False)
            .agg(net_revenue=("net_revenue_gbp", "sum"))
            .sort_values("net_revenue", ascending=False)
            .head(15)
        )
        fig = style_fig(px.bar(by_campaign, x="campaign_type_clean", y="net_revenue"),
                        "Net Revenue by Campaign Type (Top 15)")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t1_bar_netrev_by_campaign")

    if "refund_rate" in f.columns:
        by_ym2 = (
            f.groupby("YearMonth", as_index=False)
            .agg(refund_rate=("refund_rate", "mean"))
            .sort_values("YearMonth")
        )
        fig = style_fig(px.line(by_ym2, x="YearMonth", y="refund_rate", markers=True),
                        "Refund Rate Trend (by Month)")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t1_line_refund_rate_by_ym")

# ------------------ TAB 3 ------------------
with tabs[2]:
    st.subheader("Promotions & Coupon Optimisation")

    c1, c2, c3 = st.columns(3)
    net_coupon = (
        float(np.nansum(f.loc[f["has_coupon"] == True, "net_revenue_gbp"].to_numpy()))
        if "has_coupon" in f.columns
        else np.nan
    )
    net_nocoupon = (
        float(np.nansum(f.loc[f["has_coupon"] == False, "net_revenue_gbp"].to_numpy()))
        if "has_coupon" in f.columns
        else np.nan
    )
    c1.metric("Net Revenue (Coupon)", f"{net_coupon:,.0f}" if pd.notna(net_coupon) else "—")
    c2.metric("Net Revenue (No Coupon)", f"{net_nocoupon:,.0f}" if pd.notna(net_nocoupon) else "—")
    wdisc = float(np.nanmean(f["avg_discount_rate"].to_numpy())) if "avg_discount_rate" in f.columns else np.nan
    c3.metric("Avg Discount Rate", f"{wdisc:.2%}" if pd.notna(wdisc) else "—")

    if "campaign_type_clean" in f.columns:
        top_campaign = (
            f.groupby("campaign_type_clean", as_index=False)
            .agg(net_revenue=("net_revenue_gbp", "sum"))
            .sort_values("net_revenue", ascending=False)
            .head(15)
        )
        fig = style_fig(px.bar(top_campaign, x="campaign_type_clean", y="net_revenue"),
                        "Top Campaign Types (Net Revenue)")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t2_bar_netrev_by_campaign")

    if "has_coupon" in f.columns and "orders" in f.columns:
        usage = (
            f.groupby(["YearMonth"], as_index=False)
            .apply(
                lambda g: pd.Series(
                    {
                        "orders": int(np.nansum(g["orders"].to_numpy())),
                        "coupon_orders": int(np.nansum(g.loc[g["has_coupon"] == True, "orders"].to_numpy())),
                    }
                )
            )
            .reset_index(drop=True)
            .sort_values("YearMonth")
        )
        usage["coupon_usage"] = usage["coupon_orders"] / usage["orders"].replace(0, np.nan)
        fig = style_fig(px.line(usage, x="YearMonth", y="coupon_usage", markers=True),
                        "Coupon Usage Rate (by Month)")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="t2_line_coupon_usage_by_ym")

# ============================================================
# Optional datasets (tabs 4-6)
# ============================================================
rfm_df = load_optional("rfm_customer_table.csv")
rfm_targets = load_optional("rfm_target_list.csv")
sku_summary = load_optional("sku_summary.csv")
sku_rules = load_optional("sku_pair_rules_top200.csv")
missing_profile = load_optional("missing_profile_current.csv")
outlier_key = load_optional("outlier_profile_iqr_key_metrics.csv")
audit_top_orders = load_optional("audit_top_orders_by_order_total_gbp.csv")

# ------------------ TAB 4 ------------------
with tabs[3]:
    st.subheader("Customer Intelligence (RFM)")

    if rfm_df is None:
        st.warning("rfm_customer_table.csv was not found (make sure it is in the same folder as the app).")
    else:
        rfm = rfm_df.copy()
        cust_col = "Customer_ID" if "Customer_ID" in rfm.columns else None
        seg_col = "RFM_Segment" if "RFM_Segment" in rfm.columns else None
        clu_col = "kmeans_cluster" if "kmeans_cluster" in rfm.columns else None

        cA, cB, cC = st.columns(3)
        with cA:
            seg_sel = st.multiselect(
                "RFM Segment",
                sorted(rfm[seg_col].dropna().unique().tolist()) if seg_col else [],
                default=[],
                key="rfm_seg_sel",
            )
        with cB:
            clu_sel = st.multiselect(
                "Cluster",
                sorted(rfm[clu_col].dropna().unique().tolist()) if clu_col else [],
                default=[],
                key="rfm_clu_sel",
            )
        with cC:
            rec_rng = None
            if "recency_days" in rfm.columns and rfm["recency_days"].notna().any():
                rmin, rmax = int(np.nanmin(rfm["recency_days"])), int(np.nanmax(rfm["recency_days"]))
                rec_rng = st.slider("Recency (days)", rmin, rmax, (rmin, rmax), key="rfm_rec_rng")

        rf = rfm.copy()
        if seg_sel and seg_col:
            rf = rf[rf[seg_col].isin(seg_sel)]
        if clu_sel and clu_col:
            rf = rf[rf[clu_col].isin(clu_sel)]
        if rec_rng and "recency_days" in rf.columns:
            rf = rf[(rf["recency_days"] >= rec_rng[0]) & (rf["recency_days"] <= rec_rng[1])]

        k1, k2, k3, k4 = st.columns(4)
        n_cust = int(rf[cust_col].nunique()) if cust_col else len(rf)
        total_m = float(np.nansum(rf["monetary"].to_numpy())) if "monetary" in rf.columns else np.nan
        avg_m = float(np.nanmean(rf["monetary"].to_numpy())) if "monetary" in rf.columns else np.nan
        avg_f = float(np.nanmean(rf["frequency"].to_numpy())) if "frequency" in rf.columns else np.nan
        k1.metric("Customers", f"{n_cust:,}")
        k2.metric("Total Monetary (GBP)", f"{total_m:,.0f}" if pd.notna(total_m) else "—")
        k3.metric("Avg Monetary", f"{avg_m:,.2f}" if pd.notna(avg_m) else "—")
        k4.metric("Avg Frequency", f"{avg_f:.2f}" if pd.notna(avg_f) else "—")

        left, right = st.columns(2)

        with left:
            if seg_col and "monetary" in rf.columns and cust_col:
                seg_sum = (
                    rf.groupby(seg_col, as_index=False)
                    .agg(customers=(cust_col, "nunique"), monetary=("monetary", "sum"))
                    .sort_values("monetary", ascending=False)
                )
                fig = style_fig(px.bar(seg_sum, x=seg_col, y="monetary", hover_data=["customers"]),
                                "Total Monetary by Segment")
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="rfm_bar")

        # Replaced treemap with stacked bar (easier to read)
        with right:
            if seg_col and clu_col and cust_col:
                seg_cluster = (
                    rf.groupby([seg_col, clu_col], as_index=False)
                    .agg(customers=(cust_col, "nunique"))
                )
                seg_order = (
                    seg_cluster.groupby(seg_col, as_index=False)["customers"]
                    .sum()
                    .sort_values("customers", ascending=False)[seg_col]
                    .tolist()
                )
                seg_cluster[seg_col] = pd.Categorical(seg_cluster[seg_col], categories=seg_order, ordered=True)
                seg_cluster = seg_cluster.sort_values(seg_col)

                fig = px.bar(
                    seg_cluster,
                    y=seg_col,
                    x="customers",
                    color=clu_col,
                    orientation="h",
                    barmode="stack",
                    text="customers",
                )
                fig = style_fig(fig, "Customers by Segment (split by Cluster)")
                fig.update_traces(textposition="inside", insidetextanchor="middle")
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="rfm_seg_cluster_bar")
            else:
                st.info("Missing required columns for RFM charts (RFM_Segment / kmeans_cluster / Customer_ID).")

        if "recency_days" in rf.columns and "monetary" in rf.columns and len(rf) > 0:
            sample = rf.sample(min(len(rf), 5000), random_state=42)
            fig = style_fig(px.scatter(sample, x="recency_days", y="monetary"), "Recency vs Monetary (sample)")
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="rfm_scatter")

        st.markdown("### Target list")
        if rfm_targets is not None:
            st.dataframe(rfm_targets.head(200), use_container_width=True)
            st.download_button(
                "Download target list CSV",
                rfm_targets.to_csv(index=False).encode("utf-8"),
                "rfm_target_list.csv",
                "text/csv",
            )

# ------------------ TAB 5 ------------------
with tabs[4]:
    st.subheader("Products & Market Basket")

    if sku_summary is None or sku_rules is None:
        st.warning("sku_summary.csv or sku_pair_rules_top200.csv is missing.")
    else:
        topn = st.slider("Top N SKUs", 10, 50, 20, 5, key="sku_topn")

        if "sku" in sku_summary.columns and "revenue_alloc_gbp" in sku_summary.columns:
            top_skus = sku_summary.sort_values("revenue_alloc_gbp", ascending=False).head(topn)
            fig = style_fig(px.bar(top_skus, x="sku", y="revenue_alloc_gbp"),
                            f"Top {topn} SKUs (Revenue Allocated, GBP)")
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="sku_bar")
            st.dataframe(top_skus, use_container_width=True)

        needed = {"antecedent", "consequent", "support", "confidence", "lift", "pair_order_count"}
        if needed.issubset(set(sku_rules.columns)):
            c1, c2, c3 = st.columns(3)
            with c1:
                min_support = st.slider(
                    "Min support",
                    0.0,
                    float(sku_rules["support"].max()),
                    float(np.quantile(sku_rules["support"], 0.5)),
                    step=0.0001,
                    key="min_support",
                )
            with c2:
                min_conf = st.slider("Min confidence", 0.0, 1.0, 0.2, step=0.05, key="min_conf")
            with c3:
                min_lift = st.slider("Min lift", 0.0, float(sku_rules["lift"].max()), 5.0, step=1.0, key="min_lift")

            rr = sku_rules[
                (sku_rules["support"] >= min_support)
                & (sku_rules["confidence"] >= min_conf)
                & (sku_rules["lift"] >= min_lift)
            ].copy()

            fig = style_fig(
                px.scatter(
                    rr,
                    x="confidence",
                    y="lift",
                    size="pair_order_count",
                    hover_data=["antecedent", "consequent", "support", "pair_order_count"],
                ),
                "Association Rules (Confidence vs Lift)",
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="rules_scatter")

            sku_pick = st.selectbox(
                "Drill-down SKU",
                options=sorted(pd.unique(pd.concat([sku_rules["antecedent"], sku_rules["consequent"]]).dropna()).tolist()),
                key="sku_pick",
            )
            rel = rr[(rr["antecedent"] == sku_pick) | (rr["consequent"] == sku_pick)].copy()
            rel = rel.sort_values(["lift", "confidence", "support"], ascending=False).head(50)
            st.dataframe(rel, use_container_width=True)

# ------------------ TAB 6 ------------------
with tabs[5]:
    st.subheader("Data Quality, Coverage & Outliers")

    if missing_profile is not None and {"column_name", "missing_pct"}.issubset(set(missing_profile.columns)):
        top_m = missing_profile.sort_values("missing_pct", ascending=False).head(20)
        fig = style_fig(px.bar(top_m, x="column_name", y="missing_pct"), "Top Missingness (%)")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="miss_bar")
        st.dataframe(top_m, use_container_width=True)

    if outlier_key is not None and {"column", "pct_outliers_iqr"}.issubset(set(outlier_key.columns)):
        out = outlier_key.sort_values("pct_outliers_iqr", ascending=False)
        fig = style_fig(px.bar(out, x="column", y="pct_outliers_iqr"), "Outlier Prevalence (IQR) — Key Metrics")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key="out_bar")
        st.dataframe(out, use_container_width=True)

    st.markdown("### Audit: Top orders")
    if audit_top_orders is not None:
        st.dataframe(audit_top_orders.head(200), use_container_width=True)
