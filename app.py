import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Chocolate Intelligence Dashboard",
    page_icon="🍫",
    layout="wide"
)

# ---------------- CUSTOM CSS (🔥 IMPORTANT) ----------------
st.markdown("""
<style>
.main {
    background-color: #0E1117;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

div[data-testid="stMetric"] {
    background-color: #161B22;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}

.card {
    background-color: #161B22;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("Chocolate_Sales.csv")

    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

    df['Amount'] = (
        df['Amount'].astype(str)
        .str.replace('$','')
        .str.replace(',','')
    )
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    df = df.dropna(subset=['Amount','Date'])

    df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    df['Year'] = df['Date'].dt.year

    return df

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Filters")

country = st.sidebar.multiselect(
    "Country",
    df['Country'].unique(),
    default=df['Country'].unique()
)

product = st.sidebar.multiselect(
    "Product",
    df['Product'].unique(),
    default=df['Product'].unique()
)

df = df[(df['Country'].isin(country)) & (df['Product'].isin(product))]

# ---------------- HEADER ----------------
st.title("🍫 Chocolate Sales Intelligence")
st.caption("Modern Revenue Analytics Dashboard")

# ---------------- KPI ----------------
k1, k2, k3, k4 = st.columns(4)

k1.metric("🤑 Total Revenue", f"${df['Amount'].sum():,.0f}")
k2.metric("📦 Total Boxes shipped ", f"{df['Boxes Shipped'].sum():,.0f}")
k3.metric("⨏  Avg Revenue", f"{df['Amount'].mean():.2f}")
k4.metric("🔝 Top Country", df.groupby('Country')['Amount'].sum().idxmax())

# =========================================================
# SECTION 1
# =========================================================
st.markdown("## 💰 Revenue vs Efficiency")

col1, col2 = st.columns(2)

# LEFT: Top Products
result = df.groupby('Product', as_index=False)['Amount'].sum().nlargest(5,'Amount')

fig1 = px.bar(
    result,
    x='Product',
    y='Amount',
    color='Amount',
    log_y=True,
    template='plotly_dark',
    color_continuous_scale=px.colors.sequential.OrRd,
    title="Top Products"
)

col1.plotly_chart(fig1, use_container_width=True)

# RIGHT: Efficiency Pie
result = df.groupby('Sales Person', as_index=False).agg(
    Total_Revenue=('Amount','sum'),
    Total_Box=('Boxes Shipped','sum')
)

result['Efficiency'] = result['Total_Revenue'] / result['Total_Box']

fig2 = px.pie(
    result.nlargest(5,'Efficiency'),
    names='Sales Person',
    values='Efficiency',
    color_discrete_sequence=px.colors.diverging.oxy,
    title="Top Sales Efficiency"
)

col2.plotly_chart(fig2, use_container_width=True)

# =========================================================
# SECTION 2
# =========================================================
st.markdown("## 📈 Trends")

year = df.groupby('Year')['Amount'].sum().reset_index()
month = df.groupby('Month')['Amount'].sum().reset_index()

fig3 = make_subplots(rows=1, cols=2)

fig3.add_trace(go.Scatter(x=year['Year'], y=year['Amount']), row=1, col=1)
fig3.add_trace(go.Scatter(x=month['Month'], y=month['Amount']), row=1, col=2)

fig3.update_layout(template='plotly_dark', title="Year vs Month")

st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# SECTION 3
# =========================================================
st.markdown("## 🚀 Growth & Pareto")

col3, col4 = st.columns(2)

# LEFT: MoM
monthly = df.groupby('Month')['Amount'].sum().reset_index()
monthly['MoM'] = monthly['Amount'].pct_change()*100

fig4 = px.line(monthly, x='Month', y='MoM', template='plotly_dark')
col3.plotly_chart(fig4, use_container_width=True)

# RIGHT: Pareto
top = df.groupby('Sales Person')['Amount'].sum().sort_values(ascending=False).reset_index()
top['cum'] = top['Amount'].cumsum()
top['perc'] = top['cum']/top['Amount'].sum()*100

fig5 = make_subplots(specs=[[{"secondary_y": True}]])

fig5.add_bar(x=top['Sales Person'], y=top['Amount'], secondary_y=False)
fig5.add_scatter(x=top['Sales Person'], y=top['perc'], secondary_y=True)

fig5.update_layout(template='plotly_dark')

col4.plotly_chart(fig5, use_container_width=True)

# =========================================================
# SECTION 4
# =========================================================
st.markdown("## 📊 Seasonality")

col5, col6 = st.columns(2)

# LEFT (your missing 6b → Top Countries)
top_country = df.groupby('Country')['Amount'].sum().reset_index()

fig6 = px.bar(
    top_country.sort_values('Amount', ascending=False).head(10),
    x='Country',
    y='Amount',
    color='Amount',
    template='plotly_dark'
)

col5.plotly_chart(fig6, use_container_width=True)

# RIGHT Donut
peak = df.groupby('Month')['Amount'].sum().nlargest(5).reset_index()

fig7 = px.pie(
    peak,
    names='Month',
    values='Amount',
    hole=0.5,
    template='plotly_dark'
)

col6.plotly_chart(fig7, use_container_width=True)


st.markdown("## ⚠️ Outlier & Distribution Analysis")
st.caption("Understanding extreme transactions and value concentration")

col1, col2 = st.columns(2)

# =========================================================
# LEFT: VIOLIN (Distribution + IQR Bounds)
# =========================================================

Q1 = df['Amount'].quantile(0.25)
Q3 = df['Amount'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

fig_left = px.violin(
    df,
    y="Amount",
    box=True,
    points='all',
    template="plotly_dark",
    color_discrete_sequence=['#FF69B4'],
    title="Full Distribution with IQR Outlier Bounds",
    hover_data=['Country', 'Product']  # 🔥 cleaner
)

fig_left.add_hline(
    y=upper_bound,
    line_dash="dash",
    line_color="red",
    annotation_text="Upper Bound"
)

fig_left.add_hline(
    y=lower_bound,
    line_dash="dash",
    line_color="green",
    annotation_text="Lower Bound"
)

fig_left.update_layout(
    height=500,
    margin=dict(l=0, r=0, t=40, b=0)
)

col1.plotly_chart(fig_left, use_container_width=True)

# =========================================================
# RIGHT: BOX (High-Value Focus - 90th Percentile)
# =========================================================

cutoff = df['Amount'].quantile(0.90)

fig_right = px.box(
    df,
    y="Amount",
    points="outliers",
    template="plotly_dark",
    title="High-Value Transactions (Top 10%)"
)

fig_right.add_hline(
    y=cutoff,
    line_dash="dash",
    line_color="orange",
    annotation_text=f"90th Percentile ({cutoff:.0f})"
)

fig_right.update_layout(
    height=500,
    margin=dict(l=0, r=0, t=40, b=0)
)

col2.plotly_chart(fig_right, use_container_width=True)

# =========================================================
# SECTION 5
# =========================================================
st.markdown("## 🌍Total Sales Amount by Country")

country_sales = df.groupby('Country')['Amount'].sum().reset_index()

fig8 = px.choropleth(
    country_sales,
    locations='Country',
    locationmode='country names',
    color='Amount',
    color_continuous_scale=px.colors.sequential.Plasma,
    template='plotly_dark'
)

# 🔥 MAKE IT FULL WIDTH + PREMIUM LOOK
fig8.update_layout(
    height=550,  # 👈 increase height (try 500–700 based on screen)
    margin=dict(l=0, r=0, t=40, b=0),
    coloraxis_colorbar=dict(
        title="Revenue",
        thickness=12
    )
)

# 🔥 FIX MAP SCALING
fig8.update_geos(
    showframe=False,
    showcoastlines=True,
    projection_type='natural earth',  # 👈 better than default
    fitbounds="locations",  # 👈 zooms properly
    visible=True
)

st.plotly_chart(fig8, use_container_width=True)

st.markdown("## 💸 Revenue Heatmap (Country vs Product) View")

# Step 1: Create pivot
heatmap_data = (
    df
    .pivot_table(
        values='Amount',
        index='Country',
        columns='Product',
        aggfunc='sum',
        fill_value=0
    )
)

# Step 2: Sort properly (🔥 correct way)
heatmap_data['Total'] = heatmap_data.sum(axis=1)
heatmap_data = heatmap_data.sort_values('Total', ascending=False).drop(columns='Total')

# Step 3: Plot
fig9 = px.imshow(
    heatmap_data.head(8),
    text_auto=True,
    aspect="auto",
    color_continuous_scale='tempo',
    template='plotly_dark'
)

# Step 4: Layout Fix (Match Map)
fig9.update_layout(
    height=550,
    margin=dict(l=0, r=0, t=40, b=0),
    coloraxis_colorbar=dict(
        title="Revenue",
        thickness=12
    )
)

# Step 5: Axis polish
fig9.update_xaxes(side="top")

# Step 6: Render
st.plotly_chart(fig9, use_container_width=True)
# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Built by Rahul Bhankhad")
