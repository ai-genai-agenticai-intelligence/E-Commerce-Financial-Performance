from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "Sample - Superstore.csv"

st.set_page_config(
    page_title="E-Commerce Financial Performance",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH, encoding="latin-1")
    data["Order Date"] = pd.to_datetime(data["Order Date"], errors="coerce")
    data["Ship Date"] = pd.to_datetime(data["Ship Date"], errors="coerce")
    data["Order Month"] = data["Order Date"].dt.to_period("M").dt.to_timestamp()
    data["Order Year"] = data["Order Date"].dt.year
    data["Order Day of Week"] = data["Order Date"].dt.day_name()
    data["Sales"] = pd.to_numeric(data["Sales"], errors="coerce").fillna(0)
    data["Profit"] = pd.to_numeric(data["Profit"], errors="coerce").fillna(0)
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(0)
    data["Discount"] = pd.to_numeric(data["Discount"], errors="coerce").fillna(0)
    return data.dropna(subset=["Order Date", "Category", "Segment"])


def currency(value):
    return f"${value:,.0f}"


def format_axis_currency(axis):
    axis.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda value, _: f"${value / 1000:,.0f}K")
    )


data = load_data()

st.title("E-Commerce Financial Performance")
st.caption(
    "Explore sales, profit, products, and customer segments across the Superstore dataset."
)

with st.sidebar:
    st.header("Filters")
    years = sorted(data["Order Year"].dropna().astype(int).unique())
    selected_years = st.multiselect("Order years", years, default=years)
    categories = sorted(data["Category"].dropna().unique())
    selected_categories = st.multiselect("Categories", categories, default=categories)
    segments = sorted(data["Segment"].dropna().unique())
    selected_segments = st.multiselect("Customer segments", segments, default=segments)

filtered = data[
    data["Order Year"].isin(selected_years)
    & data["Category"].isin(selected_categories)
    & data["Segment"].isin(selected_segments)
].copy()

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

orders = filtered["Order ID"].nunique()
customers = filtered["Customer ID"].nunique()
total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
profit_margin = total_profit / total_sales if total_sales else 0

metric_columns = st.columns(5)
metric_columns[0].metric("Total sales", currency(total_sales))
metric_columns[1].metric("Total profit", currency(total_profit))
metric_columns[2].metric("Profit margin", f"{profit_margin:.1%}")
metric_columns[3].metric("Orders", f"{orders:,}")
metric_columns[4].metric("Customers", f"{customers:,}")

st.divider()

monthly = (
    filtered.groupby("Order Month", as_index=False)[["Sales", "Profit"]]
    .sum()
    .sort_values("Order Month")
)
category_summary = (
    filtered.groupby("Category", as_index=False)[["Sales", "Profit"]]
    .sum()
    .sort_values("Sales", ascending=False)
)
subcategory_summary = (
    filtered.groupby("Sub-Category", as_index=False)[["Sales", "Profit"]]
    .sum()
    .sort_values("Sales", ascending=False)
)
segment_summary = (
    filtered.groupby("Segment", as_index=False)[["Sales", "Profit"]]
    .sum()
    .sort_values("Sales", ascending=False)
)

st.subheader("Sales and Profit Trend")
trend_figure, trend_axes = plt.subplots(figsize=(12, 4.5))
trend_axes.plot(
    monthly["Order Month"], monthly["Sales"], marker="o", label="Sales", color="#1769aa"
)
trend_axes.plot(
    monthly["Order Month"],
    monthly["Profit"],
    marker="o",
    label="Profit",
    color="#d95f02",
)
trend_axes.set_ylabel("Amount")
trend_axes.grid(axis="y", alpha=0.25)
trend_axes.legend(frameon=False, ncol=2)
format_axis_currency(trend_axes)
trend_figure.autofmt_xdate()
st.pyplot(trend_figure, use_container_width=True)
plt.close(trend_figure)

left_chart, right_chart = st.columns(2)
with left_chart:
    st.subheader("Sales by Category")
    category_figure, category_axis = plt.subplots(figsize=(6, 4))
    category_axis.pie(
        category_summary["Sales"],
        labels=category_summary["Category"],
        autopct="%1.0f%%",
        startangle=90,
        colors=sns.color_palette("Set2", len(category_summary)),
    )
    category_axis.set_title("Share of filtered sales")
    st.pyplot(category_figure, use_container_width=True)
    plt.close(category_figure)

with right_chart:
    st.subheader("Profit by Category")
    profit_figure, profit_axis = plt.subplots(figsize=(6, 4))
    profit_axis.bar(
        category_summary["Category"], category_summary["Profit"], color="#2a9d8f"
    )
    profit_axis.set_ylabel("Profit")
    profit_axis.tick_params(axis="x", rotation=20)
    profit_axis.grid(axis="y", alpha=0.25)
    format_axis_currency(profit_axis)
    st.pyplot(profit_figure, use_container_width=True)
    plt.close(profit_figure)

left_detail, right_detail = st.columns(2)
with left_detail:
    st.subheader("Top Sub-Categories by Sales")
    top_subcategories = subcategory_summary.head(10).sort_values("Sales")
    subcategory_figure, subcategory_axis = plt.subplots(figsize=(7, 5))
    subcategory_axis.barh(
        top_subcategories["Sub-Category"], top_subcategories["Sales"], color="#457b9d"
    )
    subcategory_axis.set_xlabel("Sales")
    subcategory_axis.grid(axis="x", alpha=0.25)
    format_axis_currency(subcategory_axis)
    st.pyplot(subcategory_figure, use_container_width=True)
    plt.close(subcategory_figure)

with right_detail:
    st.subheader("Segment Performance")
    segment_figure, segment_axis = plt.subplots(figsize=(7, 5))
    segment_plot = segment_summary.set_index("Segment")[["Sales", "Profit"]]
    segment_plot.plot(kind="bar", ax=segment_axis, color=["#264653", "#e9c46a"])
    segment_axis.set_ylabel("Amount")
    segment_axis.tick_params(axis="x", rotation=20)
    segment_axis.grid(axis="y", alpha=0.25)
    segment_axis.legend(frameon=False)
    format_axis_currency(segment_axis)
    st.pyplot(segment_figure, use_container_width=True)
    plt.close(segment_figure)

st.subheader("Segment Metrics")
segment_table = segment_summary.copy()
segment_table["Sales-to-profit ratio"] = segment_table["Sales"] / segment_table[
    "Profit"
].replace(0, pd.NA)
segment_table["Profit margin"] = segment_table["Profit"] / segment_table[
    "Sales"
].replace(0, pd.NA)
st.dataframe(
    segment_table.style.format(
        {
            "Sales": "${:,.2f}",
            "Profit": "${:,.2f}",
            "Sales-to-profit ratio": "{:.2f}",
            "Profit margin": "{:.1%}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

with st.expander("Filtered records"):
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        "filtered_superstore.csv",
        "text/csv",
    )
    st.dataframe(filtered.head(100), use_container_width=True, hide_index=True)
