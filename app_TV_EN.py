# streamlit_app_TV.py
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Terminal Value Sandbox", layout="centered")

DEFAULT_DISCOUNT_RATE = 0.20
DCF_COLOR = "#B52C2F"
TV_COLOR = "#002FA7"

# ---------- Instructions ----------
st.markdown("""
### How to use this tool
- Select how the terminal value should be calculated.
- For the growth method, choose a terminal growth rate.
- For the exit multiple method, choose an exit multiple.
- The tool shows how the terminal value assumption affects the total valuation.
""")

# ---------- Fixed cash flow assumptions ----------
cash_flows = [2760, 3150, 3530, 3900, 4140]
years = [1, 2, 3, 4, 5]

cf_n = cash_flows[-1]
cf_1 = cash_flows[0]

average_annual_increase = (cf_n - cf_1) / (len(cash_flows) - 1)
cf_n_plus_1 = cf_n + average_annual_increase

# ---------- User inputs ----------
st.subheader("Terminal value assumptions")

method = st.selectbox(
    "Select terminal value method",
    ["Growth method", "Exit multiple method"]
)

if method == "Growth method":
    g_pct = st.number_input(
    "Terminal growth rate [%]",
    min_value=0.0,
    value=2.0,
    step=1.0,
    format="%.0f",
    )

    discount_rate_pct = st.number_input(
        "Discount rate [%]",
        min_value=1.0,
        value=20.0,
        step=1.0,
        format="%.0f",
    )

    g = g_pct / 100
    discount_rate = discount_rate_pct / 100

    if g >= discount_rate:
        st.warning(
            "The terminal growth rate must be lower than the discount rate. "
            "Please choose a lower growth rate."
        )
        st.stop()

    terminal_value = cf_n * (1 + g) / (discount_rate - g)

else:
    exit_multiple = st.number_input(
        "Exit multiple",
        min_value=0.0,
        value=10.0,
        step=0.5,
        format="%.1f",
    )

    discount_rate = DEFAULT_DISCOUNT_RATE

    terminal_value = cf_n_plus_1 * exit_multiple

# ---------- Valuation ----------
present_values = [
    cf / ((1 + discount_rate) ** (year - 1))
    for cf, year in zip(cash_flows, years)
]

explicit_value = sum(present_values)

discounted_terminal_value = terminal_value / ((1 + discount_rate) ** 4)

valuation = explicit_value + discounted_terminal_value

# ---------- Output ----------
st.subheader("Valuation")
st.metric("Total valuation", f"USD {valuation:,.0f}k")

# ---------- Chart 1 ----------
st.subheader("Discounted cash flows and terminal value")

dcf_df = pd.DataFrame(
    {
        "Period": [f"Year {year}" for year in years] + ["Terminal value"],
        "Component": ["Discounted cash flows"] * len(years) + ["Terminal value"],
        "Value": present_values + [discounted_terminal_value],
        "sort_order": list(range(len(years))) + [len(years)],
    }
)

dcf_bar = (
    alt.Chart(dcf_df)
    .mark_bar()
    .encode(
        x=alt.X("Period:N", title="", sort=alt.SortField("sort_order")),
        y=alt.Y("Value:Q", title="Present value (thousand USD)"),
        color=alt.Color(
            "Component:N",
            title="",
            scale=alt.Scale(
                domain=["Discounted cash flows", "Terminal value"],
                range=[DCF_COLOR, TV_COLOR],
            ),
        ),
        tooltip=[
            alt.Tooltip("Period:N", title="Period"),
            alt.Tooltip("Component:N", title="Component"),
            alt.Tooltip("Value:Q", title="Value", format=",.0f"),
        ],
    )
)

st.altair_chart(dcf_bar, use_container_width=True)

# ---------- Chart 2 ----------
st.subheader("Valuation composition")

stack_df = pd.DataFrame(
    {
        "Category": ["Valuation", "Valuation"],
        "Component": ["Discounted cash flows", "Terminal value"],
        "Value": [explicit_value, discounted_terminal_value],
        "stack_order": [0, 1],
    }
)

bar = (
    alt.Chart(stack_df)
    .mark_bar()
    .encode(
        x=alt.X("Category:N", title=""),
        y=alt.Y("sum(Value):Q", title="Present value (thousand USD)"),
        color=alt.Color(
            "Component:N",
            title="",
            scale=alt.Scale(
                domain=["Discounted cash flows", "Terminal value"],
                range=[DCF_COLOR, TV_COLOR],
            ),
        ),
        order=alt.Order("stack_order:Q"),
        tooltip=[
            alt.Tooltip("Component:N", title="Component"),
            alt.Tooltip("Value:Q", title="Value", format=",.0f"),
        ],
    )
)

total_df = pd.DataFrame(
    {
        "Category": ["Valuation"],
        "Total": [valuation],
    }
)

label = (
    alt.Chart(total_df)
    .mark_text(dy=-10)
    .encode(
        x=alt.X("Category:N"),
        y=alt.Y("Total:Q"),
        text=alt.Text("Total:Q", format=",.0f"),
    )
)

st.altair_chart(bar + label, use_container_width=True)
