"""
Customer Analytics Dashboard
This application fetches data from MySQL and displays comprehensive analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# Import database configuration
from db_config import get_connection_string

# Page configuration
st.set_page_config(
    page_title="Customer Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Set seaborn style
sns.set_style("whitegrid")

@st.cache_data(ttl=300)
def load_data():
    """Load customer data from MySQL database"""
    try:
        engine = create_engine(get_connection_string())
        query = """
        SELECT customer_id, name, email, phone, purchase_amount, 
               product_category, region, purchase_date, customer_type, created_at
        FROM customers
        ORDER BY purchase_date DESC
        """
        df = pd.read_sql(query, engine)
        df['purchase_date'] = pd.to_datetime(df['purchase_date'])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['month'] = df['purchase_date'].dt.to_period('M')
        df['year'] = df['purchase_date'].dt.year
        engine.dispose()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def calculate_kpis(df):
    """Calculate key performance indicators"""
    total_customers = len(df)
    total_revenue = df['purchase_amount'].sum()
    avg_purchase = df['purchase_amount'].mean()
    active_regions = df['region'].nunique()
    new_customers = len(df[df['customer_type'] == 'New'])
    existing_customers = len(df[df['customer_type'] == 'Existing'])
    
    return {
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'avg_purchase': avg_purchase,
        'active_regions': active_regions,
        'new_customers': new_customers,
        'existing_customers': existing_customers
    }

def plot_category_performance(df):
    """Bar chart for product category performance"""
    fig, ax = plt.subplots(figsize=(10, 6))
    category_sales = df.groupby('product_category')['purchase_amount'].sum().sort_values(ascending=False)
    
    sns.barplot(x=category_sales.values, y=category_sales.index, palette='viridis', ax=ax)
    ax.set_xlabel('Total Sales ($)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Product Category', fontsize=12, fontweight='bold')
    ax.set_title('Sales by Product Category', fontsize=14, fontweight='bold')
    
    for i, v in enumerate(category_sales.values):
        ax.text(v, i, f' ${v:,.0f}', va='center', fontsize=10)
    
    plt.tight_layout()
    return fig

def plot_monthly_trend(df):
    """Line chart for monthly customer acquisition"""
    fig, ax = plt.subplots(figsize=(12, 6))
    monthly_customers = df.groupby('month').size()
    
    monthly_customers.plot(kind='line', marker='o', linewidth=2, markersize=8, ax=ax, color='#1f77b4')
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Customers', fontsize=12, fontweight='bold')
    ax.set_title('Monthly Customer Acquisition Trend', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    for x, y in zip(range(len(monthly_customers)), monthly_customers.values):
        ax.text(x, y, str(y), ha='center', va='bottom', fontsize=9)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def plot_regional_heatmap(df):
    """Heatmap for regional performance across product categories"""
    pivot_table = df.pivot_table(
        values='purchase_amount',
        index='product_category',
        columns='region',
        aggfunc='sum',
        fill_value=0
    )
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot_table, annot=True, fmt=',.0f', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Sales ($)'})
    ax.set_title('Regional Performance by Product Category', fontsize=14, fontweight='bold')
    ax.set_xlabel('Region', fontsize=12, fontweight='bold')
    ax.set_ylabel('Product Category', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig

def plot_customer_distribution(df):
    """Pie chart for customer distribution by region"""
    region_counts = df['region'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=region_counts.index,
        values=region_counts.values,
        hole=.3,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])
    
    fig.update_layout(
        title='Customer Distribution by Region',
        showlegend=True,
        height=400
    )
    
    return fig

def plot_purchase_distribution(df):
    """Box plot for purchase amount distribution"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.boxplot(data=df, y='product_category', x='purchase_amount', palette='Set2', ax=ax)
    ax.set_xlabel('Purchase Amount ($)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Product Category', fontsize=12, fontweight='bold')
    ax.set_title('Purchase Amount Distribution by Category', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig

def calculate_clv(df):
    """Calculate Customer Lifetime Value"""
    clv = df.groupby('email').agg({
        'purchase_amount': ['sum', 'count', 'mean']
    }).reset_index()
    clv.columns = ['email', 'total_spent', 'purchase_count', 'avg_purchase']
    clv = clv.sort_values('total_spent', ascending=False)
    return clv

def main():
    st.title("📊 Customer Analytics Dashboard")
    st.markdown("---")
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Load data
    df = load_data()
    
    if df is None or df.empty:
        st.error("Unable to load data. Please check your database connection.")
        return
    
    # Date range filter
    min_date = df['purchase_date'].min().date()
    max_date = df['purchase_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Region filter
    regions = ['All'] + list(df['region'].unique())
    selected_region = st.sidebar.selectbox("Select Region", regions)
    
    # Product category filter
    categories = ['All'] + list(df['product_category'].unique())
    selected_category = st.sidebar.selectbox("Select Product Category", categories)
    
    # Customer type filter
    customer_types = ['All', 'New', 'Existing']
    selected_customer_type = st.sidebar.selectbox("Select Customer Type", customer_types)
    
    # Apply filters
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['purchase_date'].dt.date >= date_range[0]) &
            (filtered_df['purchase_date'].dt.date <= date_range[1])
        ]
    
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['product_category'] == selected_category]
    
    if selected_customer_type != 'All':
        filtered_df = filtered_df[filtered_df['customer_type'] == selected_customer_type]
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # KPIs
    st.header("📈 Key Performance Indicators")
    kpis = calculate_kpis(filtered_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Customers",
            value=f"{kpis['total_customers']:,}",
            delta=f"{kpis['new_customers']} new"
        )
    
    with col2:
        st.metric(
            label="Total Revenue",
            value=f"${kpis['total_revenue']:,.2f}",
            delta="▲ Growth"
        )
    
    with col3:
        st.metric(
            label="Avg Purchase Value",
            value=f"${kpis['avg_purchase']:,.2f}",
            delta="Per customer"
        )
    
    with col4:
        st.metric(
            label="Active Regions",
            value=kpis['active_regions'],
            delta=f"{kpis['existing_customers']} existing"
        )
    
    st.markdown("---")
    
    # Visualizations
    st.header("📊 Sales Analytics")
    
    # Row 1: Category Performance and Monthly Trend
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Product Category")
        if not filtered_df.empty:
            fig1 = plot_category_performance(filtered_df)
            st.pyplot(fig1)
        else:
            st.info("No data available for selected filters")
    
    with col2:
        st.subheader("Monthly Customer Acquisition")
        if not filtered_df.empty:
            fig2 = plot_monthly_trend(filtered_df)
            st.pyplot(fig2)
        else:
            st.info("No data available for selected filters")
    
    st.markdown("---")
    
    # Row 2: Regional Heatmap and Customer Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Regional Performance Heatmap")
        if not filtered_df.empty:
            fig3 = plot_regional_heatmap(filtered_df)
            st.pyplot(fig3)
        else:
            st.info("No data available for selected filters")
    
    with col2:
        st.subheader("Customer Distribution by Region")
        if not filtered_df.empty:
            fig4 = plot_customer_distribution(filtered_df)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No data available for selected filters")
    
    st.markdown("---")
    
    # Row 3: Purchase Distribution
    st.subheader("Purchase Amount Distribution by Category")
    if not filtered_df.empty:
        fig5 = plot_purchase_distribution(filtered_df)
        st.pyplot(fig5)
    else:
        st.info("No data available for selected filters")
    
    st.markdown("---")
    
    # Customer Lifetime Value Analysis
    st.header("💰 Customer Lifetime Value (CLV) Analysis")
    
    if not filtered_df.empty:
        clv_df = calculate_clv(filtered_df)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Top 10 High-Value Customers")
            top_customers = clv_df.head(10).copy()
            top_customers['total_spent'] = top_customers['total_spent'].apply(lambda x: f"${x:,.2f}")
            top_customers['avg_purchase'] = top_customers['avg_purchase'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(top_customers, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("CLV Summary")
            st.metric("Total CLV", f"${clv_df['total_spent'].sum():,.2f}")
            st.metric("Avg CLV", f"${clv_df['total_spent'].mean():,.2f}")
            st.metric("Top Customer Value", f"${clv_df['total_spent'].iloc[0]:,.2f}")
    
    st.markdown("---")
    
    # Regional Performance Comparison
    st.header("🌍 Regional Performance Comparison")
    
    if not filtered_df.empty:
        region_stats = filtered_df.groupby('region').agg({
            'purchase_amount': ['sum', 'mean', 'count']
        }).round(2)
        
        region_stats.columns = ['Total Revenue', 'Avg Purchase', 'Customer Count']
        region_stats['Revenue %'] = (region_stats['Total Revenue'] / region_stats['Total Revenue'].sum() * 100).round(2)
        region_stats = region_stats.sort_values('Total Revenue', ascending=False)
        
        region_stats_display = region_stats.copy()
        region_stats_display['Total Revenue'] = region_stats_display['Total Revenue'].apply(lambda x: f"${x:,.2f}")
        region_stats_display['Avg Purchase'] = region_stats_display['Avg Purchase'].apply(lambda x: f"${x:,.2f}")
        region_stats_display['Revenue %'] = region_stats_display['Revenue %'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(region_stats_display, use_container_width=True)
    
    st.markdown("---")
    
    # Data Quality Metrics
    st.header("📋 Data Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_records = len(filtered_df)
        st.metric("Total Records", f"{total_records:,}")
    
    with col2:
        missing_values = filtered_df.isnull().sum().sum()
        st.metric("Missing Values", missing_values)
    
    with col3:
        data_completeness = ((1 - filtered_df.isnull().sum().sum() / (len(filtered_df) * len(filtered_df.columns))) * 100)
        st.metric("Data Completeness", f"{data_completeness:.2f}%")
    
    with st.expander("📄 View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"customer_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()