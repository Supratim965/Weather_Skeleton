from datetime import date

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Sales performance dashboard",
    page_icon=":material/monitoring:",
    layout="wide",
)


@st.cache_data
def load_sample_data() -> pd.DataFrame:
    """Create a reproducible sample sales dataset for the dashboard."""
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    regions = ["North", "South", "East", "West"]
    products = ["Laptop", "Monitor", "Keyboard", "Mouse", "Headset"]
    channels = ["Retail", "Online", "Partner"]

    rows = []
    order_id = 10_000

    for day_number, order_date in enumerate(dates):
        month_factor = 1 + (order_date.month - 1) * 0.015
        weekday_factor = 1.18 if order_date.weekday() < 5 else 0.74

        for region_index, region in enumerate(regions):
            for product_index, product in enumerate(products):
                baseline_units = 8 + region_index * 2 + product_index
                units = round(baseline_units * month_factor * weekday_factor)
                unit_price = [920, 310, 80, 45, 125][product_index]
                discount = [0.06, 0.08, 0.04, 0.03, 0.05][region_index % 5]
                revenue = units * unit_price * (1 - discount)
                cost = revenue * (0.56 + product_index * 0.025)
                channel = channels[(day_number + region_index + product_index) % len(channels)]

                rows.append(
                    {
                        "order_id": f"ORD-{order_id}",
                        "date": order_date.date(),
                        "region": region,
                        "product": product,
                        "channel": channel,
                        "units": units,
                        "revenue": round(revenue, 2),
                        "profit": round(revenue - cost, 2),
                        "discount": discount,
                    }
                )
                order_id += 1

    return pd.DataFrame(rows)


def format_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value / 1_000:.1f}K"


def format_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def metric_delta(current: float, previous: float) -> str:
    if previous == 0:
        return "0.0%"
    return f"{((current - previous) / previous) * 100:.1f}%"


def previous_period(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    days = (end_date - start_date).days + 1
    previous_end = pd.Timestamp(start_date) - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=days - 1)
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    return data[(data["date"] >= previous_start) & (data["date"] <= previous_end)]


raw_data = load_sample_data()
min_date = raw_data["date"].min()
max_date = raw_data["date"].max()
all_regions = sorted(raw_data["region"].unique())
all_products = sorted(raw_data["product"].unique())
all_channels = sorted(raw_data["channel"].unique())

with st.sidebar:
    st.header("Filters", anchor=False)
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    selected_regions = st.multiselect("Regions", all_regions, default=all_regions)
    selected_products = st.multiselect("Products", all_products, default=all_products)
    selected_channels = st.pills(
        "Channels",
        all_channels,
        default=all_channels,
        selection_mode="multi",
    )

    metric_focus = st.segmented_control(
        "Chart metric",
        ["Revenue", "Profit", "Units"],
        default="Revenue",
    )

if len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

filtered_data = raw_data[
    (raw_data["date"] >= start_date)
    & (raw_data["date"] <= end_date)
    & (raw_data["region"].isin(selected_regions))
    & (raw_data["product"].isin(selected_products))
    & (raw_data["channel"].isin(selected_channels))
].copy()

previous_data = previous_period(raw_data, start_date, end_date)
previous_data = previous_data[
    (previous_data["region"].isin(selected_regions))
    & (previous_data["product"].isin(selected_products))
    & (previous_data["channel"].isin(selected_channels))
]

st.title("Sales performance dashboard")
st.caption(
    f"{start_date:%b %d, %Y} to {end_date:%b %d, %Y} across "
    f"{len(selected_regions)} regions, {len(selected_products)} products, "
    f"and {len(selected_channels)} channels."
)

if filtered_data.empty:
    st.warning("No records match the current filters.", icon=":material/filter_alt_off:")
    st.stop()

with st.sidebar:
    st.download_button(
        "Download filtered CSV",
        data=filtered_data.to_csv(index=False).encode("utf-8"),
        file_name="sales-dashboard-filtered.csv",
        mime="text/csv",
        icon=":material/download:",
    )

revenue = filtered_data["revenue"].sum()
profit = filtered_data["profit"].sum()
units = int(filtered_data["units"].sum())
orders = filtered_data["order_id"].nunique()
margin = profit / revenue if revenue else 0
average_order_value = revenue / orders if orders else 0

previous_revenue = previous_data["revenue"].sum()
previous_profit = previous_data["profit"].sum()
previous_units = int(previous_data["units"].sum())
previous_orders = previous_data["order_id"].nunique()
previous_average_order_value = previous_revenue / previous_orders if previous_orders else 0

daily = (
    filtered_data.groupby("date", as_index=False)
    .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), units=("units", "sum"))
    .sort_values("date")
)
daily["date"] = pd.to_datetime(daily["date"])

monthly = (
    filtered_data.assign(month=pd.to_datetime(filtered_data["date"]).dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), units=("units", "sum"))
    .sort_values("month")
)

metric_column = metric_focus.lower()
metric_format = "$,.0f" if metric_column in {"revenue", "profit"} else ","
axis_format = "$~s" if metric_column in {"revenue", "profit"} else "~s"

with st.container(horizontal=True):
    st.metric(
        "Revenue",
        format_currency(revenue),
        metric_delta(revenue, previous_revenue),
        border=True,
        chart_data=daily["revenue"].tail(30),
        chart_type="line",
    )
    st.metric(
        "Profit",
        format_currency(profit),
        metric_delta(profit, previous_profit),
        border=True,
        chart_data=daily["profit"].tail(30),
        chart_type="line",
    )
    st.metric(
        "Units sold",
        f"{units:,}",
        metric_delta(units, previous_units),
        border=True,
        chart_data=daily["units"].tail(30),
        chart_type="bar",
    )
    st.metric("Orders", f"{orders:,}", metric_delta(orders, previous_orders), border=True)
    st.metric(
        "Avg. order value",
        format_currency(average_order_value),
        metric_delta(average_order_value, previous_average_order_value),
        border=True,
    )
    st.metric("Margin", f"{margin:.1%}", border=True)

left, right = st.columns((2, 1))
with left:
    with st.container(border=True):
        st.subheader(f"{metric_focus} trend", anchor=False)
        trend_chart = (
            alt.Chart(daily)
            .mark_area(line=True, point=True, opacity=0.2)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y(
                    f"{metric_column}:Q",
                    title=metric_focus,
                    axis=alt.Axis(format=axis_format),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                    alt.Tooltip(f"{metric_column}:Q", title=metric_focus, format=metric_format),
                ],
            )
        )
        st.altair_chart(trend_chart)

with right:
    with st.container(border=True):
        st.subheader(f"{metric_focus} by channel", anchor=False)
        channel_summary = (
            filtered_data.groupby("channel", as_index=False)[metric_column]
            .sum()
            .sort_values(metric_column, ascending=False)
        )
        channel_chart = (
            alt.Chart(channel_summary)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("channel:N", title="Channel", sort="-y"),
                y=alt.Y(
                    f"{metric_column}:Q",
                    title=metric_focus,
                    axis=alt.Axis(format=axis_format),
                ),
                tooltip=[
                    alt.Tooltip("channel:N", title="Channel"),
                    alt.Tooltip(f"{metric_column}:Q", title=metric_focus, format=metric_format),
                ],
            )
        )
        st.altair_chart(channel_chart)

chart_left, chart_right = st.columns(2)
with chart_left:
    with st.container(border=True):
        st.subheader(f"{metric_focus} by region", anchor=False)
        region_summary = (
            filtered_data.groupby("region", as_index=False)[metric_column]
            .sum()
            .sort_values(metric_column, ascending=False)
        )
        region_chart = (
            alt.Chart(region_summary)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X(
                    f"{metric_column}:Q",
                    title=metric_focus,
                    axis=alt.Axis(format=axis_format),
                ),
                y=alt.Y("region:N", title="Region", sort="-x"),
                tooltip=[
                    alt.Tooltip("region:N", title="Region"),
                    alt.Tooltip(f"{metric_column}:Q", title=metric_focus, format=metric_format),
                ],
            )
        )
        st.altair_chart(region_chart)

with chart_right:
    with st.container(border=True):
        st.subheader("Product profitability", anchor=False)
        product_summary = (
            filtered_data.groupby("product", as_index=False)
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), units=("units", "sum"))
            .sort_values("profit", ascending=False)
        )
        product_chart = (
            alt.Chart(product_summary)
            .mark_circle(size=350)
            .encode(
                x=alt.X("revenue:Q", title="Revenue", axis=alt.Axis(format="$~s")),
                y=alt.Y("profit:Q", title="Profit", axis=alt.Axis(format="$~s")),
                size=alt.Size("units:Q", title="Units"),
                color=alt.Color("product:N", title="Product"),
                tooltip=[
                    "product:N",
                    alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
                    alt.Tooltip("profit:Q", title="Profit", format="$,.0f"),
                    alt.Tooltip("units:Q", title="Units", format=","),
                ],
            )
        )
        st.altair_chart(product_chart)

summary_left, summary_right = st.columns(2)
with summary_left:
    with st.container(border=True):
        st.subheader("Monthly performance", anchor=False)
        monthly_chart = (
            alt.Chart(monthly)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("month:T", title="Month", timeUnit="yearmonth"),
                y=alt.Y(
                    f"{metric_column}:Q",
                    title=metric_focus,
                    axis=alt.Axis(format=axis_format),
                ),
                tooltip=[
                    alt.Tooltip("month:T", title="Month", format="%b %Y"),
                    alt.Tooltip(f"{metric_column}:Q", title=metric_focus, format=metric_format),
                ],
            )
        )
        st.altair_chart(monthly_chart)

with summary_right:
    with st.container(border=True):
        st.subheader("Top products", anchor=False)
        top_products = product_summary.assign(
            margin=product_summary["profit"] / product_summary["revenue"]
        )
        st.dataframe(
            top_products[["product", "revenue", "profit", "margin", "units"]],
            hide_index=True,
            column_config={
                "product": st.column_config.TextColumn("Product", pinned=True),
                "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
                "profit": st.column_config.NumberColumn("Profit", format="$%.2f"),
                "margin": st.column_config.ProgressColumn(
                    "Margin",
                    format="percent",
                    min_value=0,
                    max_value=1,
                ),
                "units": st.column_config.NumberColumn("Units", format="%d"),
            },
        )

with st.container(border=True):
    st.subheader("Detailed orders", anchor=False)
    table_data = filtered_data.sort_values("date", ascending=False).assign(
        margin=filtered_data["profit"] / filtered_data["revenue"]
    )
    st.dataframe(
        table_data,
        hide_index=True,
        column_config={
            "order_id": st.column_config.TextColumn("Order ID", pinned=True),
            "date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
            "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
            "profit": st.column_config.NumberColumn("Profit", format="$%.2f"),
            "discount": st.column_config.NumberColumn("Discount", format="percent"),
            "margin": st.column_config.NumberColumn("Margin", format="percent"),
        },
    )
