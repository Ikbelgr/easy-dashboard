import streamlit as st
import datetime as dt
import pandas as pd
from src.data_loader import load_and_preprocess_data, filter_data
from src.summary import monthly_summary_by_channel, monthly_customer_stats
from src.plots import plot_combined_by_channel, plot_customers_with_new_and_total, plot_pie, plot_cohort_heatmap
from src.cohort import run_cohort_analysis
from src.utils import group_top_n_with_other, get_summary

st.set_page_config(page_title="Easy Dashboard", layout="wide")
st.title("Easy Dashboard")

# Sidebar controls
st.sidebar.header("Upload & Filter Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

min_date = dt.date(2024, 5, 1)
max_date = dt.date(2025, 6, 30)
start_date = st.sidebar.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)
country = st.sidebar.selectbox("Country", options=["All", "Tunisia", "Morocco"])

if uploaded_file:
    # Read the file once and create both versions
    df_raw = pd.read_csv(uploaded_file)
    
    # Create processed version (with renamed columns)
    df = df_raw.copy()
    df.rename(columns={
        'id_client': 'customer_id',
        'createdAt': 'transaction_date'
    }, inplace=True)
    # Convert to datetime and remove timezone
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['transaction_date'] = df['transaction_date'].dt.tz_localize(None)
    # Extract transaction_month
    df['transaction_month'] = df['transaction_date'].apply(lambda x: dt.datetime(x.year, x.month, 1))
    # Convert amountToSend to numeric, handling any non-numeric values
    if 'amountToSend' in df.columns:
        df['amountToSend'] = pd.to_numeric(df['amountToSend'], errors='coerce')
    
    # Create original version (preserving column names)
    original_df = df_raw.copy()
    # Convert to datetime and remove timezone
    original_df['transaction_date'] = pd.to_datetime(original_df['createdAt'] if 'createdAt' in original_df.columns else original_df['transaction_date'])
    original_df['transaction_date'] = original_df['transaction_date'].dt.tz_localize(None)
    # Extract transaction_month
    original_df['transaction_month'] = original_df['transaction_date'].apply(lambda x: dt.datetime(x.year, x.month, 1))
    # Convert amountToSend to numeric, handling any non-numeric values
    if 'amountToSend' in original_df.columns:
        original_df['amountToSend'] = pd.to_numeric(original_df['amountToSend'], errors='coerce')
    
    # Map country names to codes if needed
    country_map = {"Tunisia": "TUN", "Morocco": "MAC"}
    selected_country = None if country == "All" else country_map[country]
    
    # Convert dates to date-only for filtering (like Excel)
    start_datetime = dt.datetime.combine(start_date, dt.time())
    end_datetime = dt.datetime.combine(end_date, dt.time(23, 59, 59))
    df_filtered = filter_data(df, start_datetime, end_datetime, selected_country)
    
    # Alternative: filter by date only (like Excel might do)
    df_filtered_date_only = df.copy()
    if selected_country:
        df_filtered_date_only = df_filtered_date_only[df_filtered_date_only['country'] == selected_country]
    df_filtered_date_only = df_filtered_date_only[
        (df_filtered_date_only['transaction_date'].dt.date >= start_date) & 
        (df_filtered_date_only['transaction_date'].dt.date <= end_date)
    ]
    
    # KPI Section
    # Calculate KPIs for today (latest day in dataset)
    latest_date = df_filtered['transaction_date'].max().date()
    today_data = df_filtered[df_filtered['transaction_date'].dt.date == latest_date]
    
    # Calculate KPIs for this month (current month until now)
    current_month_start = dt.datetime(latest_date.year, latest_date.month, 1)
    this_month_data = df_filtered[df_filtered['transaction_date'] >= current_month_start]
    
    # Calculate KPIs with status breakdown
    def get_status_breakdown(data, metric_type='transactions'):
        if data.empty:
            return "0 total (0 completed, 0 in progress, 0 cancelled)"
        
        if 'status' not in data.columns:
            total = len(data) if metric_type == 'transactions' else data['customer_id'].nunique()
            return f"{total:,} total"
        
        # Count by status - handle both spellings
        status_counts = data['status'].value_counts()
        completed = status_counts.get('complete', 0)
        in_progress = status_counts.get('in progress', 0)
        cancelled = status_counts.get('cancelled', 0) + status_counts.get('canceled', 0)  # Handle both spellings
        total = completed + in_progress + cancelled
        
        return f"{total:,} total ({completed:,} completed, {in_progress:,} in progress, {cancelled:,} cancelled)"
    
    def get_customer_status_breakdown(data):
        if data.empty:
            return "0 total (0 completed, 0 in progress, 0 cancelled)"
        
        if 'status' not in data.columns:
            return f"{data['customer_id'].nunique():,} total"
        
        # Get unique customers by status - handle both spellings
        completed_customers = data[data['status'] == 'complete']['customer_id'].nunique()
        in_progress_customers = data[data['status'] == 'in progress']['customer_id'].nunique()
        cancelled_customers = data[(data['status'] == 'cancelled') | (data['status'] == 'canceled')]['customer_id'].nunique()
        total_customers = data['customer_id'].nunique()
        
        return f"{total_customers:,} total ({completed_customers:,} completed, {in_progress_customers:,} in progress, {cancelled_customers:,} cancelled)"
    
    def get_financial_status_breakdown(data):
        if data.empty:
            return "€0 total (€0 completed, €0 in progress, €0 cancelled)"
        
        if 'status' not in data.columns:
            total_amount = data['amountToSend'].sum() if 'amountToSend' in data.columns else 0
            return f"€{total_amount:,.0f} total"
        
        # Sum amounts by status - handle both spellings
        completed_amount = data[data['status'] == 'complete']['amountToSend'].sum() if 'amountToSend' in data.columns else 0
        in_progress_amount = data[data['status'] == 'in progress']['amountToSend'].sum() if 'amountToSend' in data.columns else 0
        cancelled_amount = data[(data['status'] == 'cancelled') | (data['status'] == 'canceled')]['amountToSend'].sum() if 'amountToSend' in data.columns else 0
        total_amount = completed_amount + in_progress_amount + cancelled_amount
        
        return f"€{total_amount:,.0f} total (€{completed_amount:,.0f} completed, €{in_progress_amount:,.0f} in progress, €{cancelled_amount:,.0f} cancelled)"
    
    # Calculate breakdowns for today
    today_transactions_breakdown = get_status_breakdown(today_data, 'transactions')
    today_customers_breakdown = get_customer_status_breakdown(today_data)
    
    # Calculate new customers for today (customers whose first transaction was today)
    first_tx_dates = df_filtered.groupby('customer_id')['transaction_date'].min().reset_index()
    today_new_customers_data = first_tx_dates[first_tx_dates['transaction_date'].dt.date == latest_date]
    today_new_customers_breakdown = get_customer_status_breakdown(today_data[today_data['customer_id'].isin(today_new_customers_data['customer_id'])])
    
    today_total_amount_breakdown = get_financial_status_breakdown(today_data)
    
    # Calculate breakdowns for this month
    this_month_transactions_breakdown = get_status_breakdown(this_month_data, 'transactions')
    this_month_customers_breakdown = get_customer_status_breakdown(this_month_data)
    
    # Calculate new customers for this month (customers whose first transaction was this month)
    this_month_new_customers_data = first_tx_dates[first_tx_dates['transaction_date'].dt.to_period('M') == pd.Timestamp(latest_date).to_period('M')]
    this_month_new_customers_breakdown = get_customer_status_breakdown(this_month_data[this_month_data['customer_id'].isin(this_month_new_customers_data['customer_id'])])
    
    this_month_total_amount_breakdown = get_financial_status_breakdown(this_month_data)
    
    # Get biggest amount (from completed transactions only)
    today_biggest_amount = today_data[today_data['status'] == 'complete']['amountToSend'].max() if 'amountToSend' in today_data.columns and 'status' in today_data.columns else 0
    
    # Get biggest transaction with status
    if 'amountToSend' in today_data.columns and 'status' in today_data.columns and not today_data.empty:
        biggest_tx = today_data.loc[today_data['amountToSend'].idxmax()]
        biggest_amount = biggest_tx['amountToSend']
        biggest_status = biggest_tx['status']
    else:
        biggest_amount = 0
        biggest_status = 'N/A'
    
    # Get this month's biggest transaction with status
    if 'amountToSend' in this_month_data.columns and 'status' in this_month_data.columns and not this_month_data.empty:
        month_biggest_tx = this_month_data.loc[this_month_data['amountToSend'].idxmax()]
        month_biggest_amount = month_biggest_tx['amountToSend']
        month_biggest_status = month_biggest_tx['status']
    else:
        month_biggest_amount = 0
        month_biggest_status = 'N/A'
    
    # Helper for status badge
    def status_badge(status):
        if status == 'complete':
            return '<span style="background:#e6f4ea;color:#219653;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;float:right;">🟢 Complete</span>'
        elif status == 'in progress':
            return '<span style="background:#fff4e5;color:#f2994a;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;float:right;">🟠 In Progress</span>'
        elif status in ['cancelled', 'canceled']:
            return '<span style="background:#ffeaea;color:#eb5757;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;float:right;">🔴 Cancelled</span>'
        else:
            return ''

    # Get status mode for today and this month
    today_status = today_data['status'].mode()[0] if 'status' in today_data.columns and not today_data.empty else ''
    month_status = this_month_data['status'].mode()[0] if 'status' in this_month_data.columns and not this_month_data.empty else ''

    # Display KPIs in modern card layout
    st.markdown("## 📊 Key Performance Indicators")
    
    # Create three columns for better layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### 📅 Today's Performance ({latest_date.strftime('%B %d, %Y')})")
        st.markdown("---")
        
        # Transactions card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #4CAF50;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">🛒 TRANSACTIONS</h5>
                        <h3 style="margin: 3px 0; color: #2E7D32; font-size: 20px; font-weight: 700;">{today_transactions_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Active Customers card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8f9 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #2196F3;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">👥 ACTIVE CUSTOMERS</h5>
                        <h3 style="margin: 3px 0; color: #1976D2; font-size: 20px; font-weight: 700;">{today_customers_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # New Customers card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #FF9800;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">🆕 NEW CUSTOMERS</h5>
                        <h3 style="margin: 3px 0; color: #F57C00; font-size: 20px; font-weight: 700;">{today_new_customers_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"### 📊 This Month ({latest_date.strftime('%B %Y')})")
        st.markdown("---")
        
        # Transactions card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #4CAF50;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">🛒 TRANSACTIONS</h5>
                        <h3 style="margin: 3px 0; color: #2E7D32; font-size: 20px; font-weight: 700;">{this_month_transactions_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Active Customers card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #2196F3;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">👥 ACTIVE CUSTOMERS</h5>
                        <h3 style="margin: 3px 0; color: #1976D2; font-size: 20px; font-weight: 700;">{this_month_customers_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # New Customers card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #FF9800;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">🆕 NEW CUSTOMERS</h5>
                        <h3 style="margin: 3px 0; color: #F57C00; font-size: 20px; font-weight: 700;">{this_month_new_customers_breakdown}</h3>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 💰 Financial Metrics")
        st.markdown("---")
        
        # Today's Total card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #FFC107;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">💰 TODAY'S TOTAL</h5>
                        <h4 style="margin: 3px 0; color: #F57F17; font-size: 16px; font-weight: 700; line-height: 1.3;">{today_total_amount_breakdown}</h4>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Month's Total card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #FFC107;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h5 style="margin: 0; color: #555; font-size: 14px; font-weight: 600;">💰 MONTH'S TOTAL</h5>
                        <h4 style="margin: 3px 0; color: #F57F17; font-size: 16px; font-weight: 700; line-height: 1.3;">{this_month_total_amount_breakdown}</h4>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Biggest Transaction card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%); padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #FFC107;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="flex: 1; text-align: center; border-right: 1px solid #eee; padding-right: 10px;">
                        <h5 style="margin: 0; color: #555; font-size: 12px; font-weight: 600;">🏆 TODAY'S BIGGEST</h5>
                        <h3 style="margin: 3px 0; color: #F57F17; font-size: 18px; font-weight: 700;">€{biggest_amount:,.0f}</h3>
                        <p style="margin: 0; color: #666; font-size: 10px;">({biggest_status})</p>
                    </div>
                    <div style="flex: 1; text-align: center; padding-left: 10px;">
                        <h5 style="margin: 0; color: #555; font-size: 12px; font-weight: 600;">🏆 MONTH'S BIGGEST</h5>
                        <h3 style="margin: 3px 0; color: #F57F17; font-size: 18px; font-weight: 700;">€{month_biggest_amount:,.0f}</h3>
                        <p style="margin: 0; color: #666; font-size: 10px;">({month_biggest_status})</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # st.write(df_filtered.head())

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Monthly Summary", "Customers", "Cohort Analysis", "Breakdowns", "Cities", "Promo Codes", "RFM Segmentation", "Month Comparison"
    ])

    with tab1:
        st.subheader("Monthly Transactions by Channel")
        
        view_by = st.radio("View by", ["Month", "Day"], horizontal=True, key="summary_view_by")
        if view_by == "Month":
            # Create status breakdown stacked bar chart
            if 'status' in df_filtered.columns:
                st.markdown("**📊 Monthly Transaction Summary Table**")
                
                # Calculate monthly transaction stats with status breakdown
                monthly_transaction_stats_with_status = []
                months = sorted(df_filtered['transaction_month'].unique(), reverse=True)
                
                for month in months:
                    month_data = df_filtered[df_filtered['transaction_month'] == month]
                    
                    # Total transactions for this month
                    total_transactions = len(month_data)
                    
                    # Status breakdown for this month
                    status_counts = month_data['status'].value_counts()
                    
                    # Handle both spellings
                    if 'cancelled' in status_counts.index and 'canceled' in status_counts.index:
                        status_counts['cancelled'] += status_counts['canceled']
                        status_counts = status_counts.drop('canceled')
                    elif 'canceled' in status_counts.index:
                        status_counts = status_counts.rename({'canceled': 'cancelled'})
                    
                    completed = status_counts.get('complete', 0)
                    in_progress = status_counts.get('in progress', 0)
                    cancelled = status_counts.get('cancelled', 0)
                    
                    # Channel breakdown for this month
                    channel_counts = month_data['distributionChannel'].value_counts()
                    
                    # More flexible channel matching
                    cash_pickup_count = 0
                    bank_transfer_count = 0
                    
                    # Status breakdown for each channel
                    cash_pickup_completed = 0
                    cash_pickup_in_progress = 0
                    cash_pickup_cancelled = 0
                    bank_transfer_completed = 0
                    bank_transfer_in_progress = 0
                    bank_transfer_cancelled = 0
                    
                    for channel, count in channel_counts.items():
                        channel_lower = str(channel).lower().strip()
                        if 'cash' in channel_lower or 'pickup' in channel_lower or 'pick up' in channel_lower:
                            cash_pickup_count += count
                            # Get status breakdown for cash pickup
                            cash_pickup_data = month_data[month_data['distributionChannel'] == channel]
                            cash_status_counts = cash_pickup_data['status'].value_counts()
                            cash_pickup_completed += cash_status_counts.get('complete', 0)
                            cash_pickup_in_progress += cash_status_counts.get('in progress', 0)
                            cash_pickup_cancelled += cash_status_counts.get('cancelled', 0) + cash_status_counts.get('canceled', 0)
                        elif 'bank' in channel_lower or 'transfer' in channel_lower or 'account' in channel_lower:
                            bank_transfer_count += count
                            # Get status breakdown for bank transfer
                            bank_transfer_data = month_data[month_data['distributionChannel'] == channel]
                            bank_status_counts = bank_transfer_data['status'].value_counts()
                            bank_transfer_completed += bank_status_counts.get('complete', 0)
                            bank_transfer_in_progress += bank_status_counts.get('in progress', 0)
                            bank_transfer_cancelled += bank_status_counts.get('cancelled', 0) + bank_status_counts.get('canceled', 0)
                    
                    monthly_transaction_stats_with_status.append({
                        'Month': month.strftime('%B %Y'),
                        'Total Transactions': total_transactions,
                        'Completed': completed,
                        'In Progress': in_progress,
                        'Cancelled': cancelled,
                        'Cash Pickup (Total)': cash_pickup_count,
                        'Cash Pickup (Completed)': cash_pickup_completed,
                        'Cash Pickup (In Progress)': cash_pickup_in_progress,
                        'Cash Pickup (Cancelled)': cash_pickup_cancelled,
                        'Bank Transfer (Total)': bank_transfer_count,
                        'Bank Transfer (Completed)': bank_transfer_completed,
                        'Bank Transfer (In Progress)': bank_transfer_in_progress,
                        'Bank Transfer (Cancelled)': bank_transfer_cancelled
                    })
                
                # Create and display the table
                import pandas as pd
                summary_df = pd.DataFrame(monthly_transaction_stats_with_status)
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
                
                st.markdown("**📊 Transactions by Status (Stacked Bar)**")
                status_monthly = df_filtered.groupby(['transaction_month', 'status']).size().reset_index(name='Total Transactions')
                # Handle both spellings of cancelled
                status_monthly['status'] = status_monthly['status'].replace({'canceled': 'cancelled'})
                import plotly.express as px
                fig_status = px.bar(
                    status_monthly,
                    x='transaction_month',
                    y='Total Transactions',
                    color='status',
                    barmode='stack',
                    title="Monthly Transactions by Status (Stacked Bar)"
                )
                fig_status.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Number of Transactions",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_status, use_container_width=True, key="monthly_status_chart")
            
            # Original channel breakdown
            st.markdown("**📊 Transactions by Distribution Channel**")
            grouped = monthly_summary_by_channel(df_filtered)
            pivoted = grouped.pivot(index='transaction_month', columns='distributionChannel', values='Total Transactions').fillna(0)
            fig = plot_combined_by_channel(pivoted, country)
            st.plotly_chart(fig, use_container_width=True, key="monthly_channel_chart")
        else:
            # Day view: let user pick a day within the filtered range
            min_day = df_filtered['transaction_date'].min().date()
            max_day = df_filtered['transaction_date'].max().date()
            selected_day = st.date_input("Select day", min_value=min_day, max_value=max_day, value=max_day, key="summary_day")
            day_df = df_filtered[df_filtered['transaction_date'].dt.date == selected_day]
            if not day_df.empty:
                # Status breakdown for the day (pie chart)
                if 'status' in day_df.columns:
                    st.markdown(f"**📊 Status Breakdown for {selected_day} (Pie Chart)**")
                    status_counts = day_df['status'].value_counts()
                    # Handle both spellings
                    if 'cancelled' in status_counts.index and 'canceled' in status_counts.index:
                        status_counts['cancelled'] += status_counts['canceled']
                        status_counts = status_counts.drop('canceled')
                    elif 'canceled' in status_counts.index:
                        status_counts = status_counts.rename({'canceled': 'cancelled'})
                    
                    import plotly.express as px
                    fig_status = px.pie(values=status_counts.values, names=status_counts.index, title=f"Transaction Status for {selected_day}")
                    st.plotly_chart(fig_status, use_container_width=True, key="daily_status_chart")
                
                # Channel breakdown for the day (pie chart)
                st.markdown(f"**📊 Channel Breakdown for {selected_day} (Pie Chart)**")
                channel_counts = day_df['distributionChannel'].value_counts()
                import plotly.express as px
                fig_channel = px.pie(values=channel_counts.values, names=channel_counts.index, title=f"Transactions by Channel for {selected_day}")
                st.plotly_chart(fig_channel, use_container_width=True, key="daily_channel_chart")
                
                # Show transaction summary for selected day
                st.markdown(f"**📊 Transaction Summary for {selected_day}**")
                
                # Show total transactions first
                total_transactions = len(day_df)
                st.markdown(f"**Total Transactions: {total_transactions}**")
                st.markdown("---")
                
                # Calculate channel and status breakdown
                cash_pickup_total = 0
                cash_pickup_completed = 0
                cash_pickup_in_progress = 0
                cash_pickup_cancelled = 0
                bank_account_total = 0
                bank_account_completed = 0
                bank_account_in_progress = 0
                bank_account_cancelled = 0
                
                for channel, count in channel_counts.items():
                    channel_lower = str(channel).lower().strip()
                    if 'cash' in channel_lower or 'pickup' in channel_lower or 'pick up' in channel_lower:
                        cash_pickup_total += count
                        # Get status breakdown for cash pickup
                        cash_pickup_data = day_df[day_df['distributionChannel'] == channel]
                        cash_status_counts = cash_pickup_data['status'].value_counts()
                        cash_pickup_completed += cash_status_counts.get('complete', 0)
                        cash_pickup_in_progress += cash_status_counts.get('in progress', 0)
                        cash_pickup_cancelled += cash_status_counts.get('cancelled', 0) + cash_status_counts.get('canceled', 0)
                    elif 'bank' in channel_lower or 'transfer' in channel_lower or 'account' in channel_lower:
                        bank_account_total += count
                        # Get status breakdown for bank account
                        bank_account_data = day_df[day_df['distributionChannel'] == channel]
                        bank_status_counts = bank_account_data['status'].value_counts()
                        bank_account_completed += bank_status_counts.get('complete', 0)
                        bank_account_in_progress += bank_status_counts.get('in progress', 0)
                        bank_account_cancelled += bank_status_counts.get('cancelled', 0) + bank_status_counts.get('canceled', 0)
                
                # Display in clean format
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💳 Cash Pickup:**")
                    st.write(f"Total: {cash_pickup_total}")
                    st.write(f"Completed: {cash_pickup_completed}")
                    st.write(f"In Progress: {cash_pickup_in_progress}")
                    st.write(f"Cancelled: {cash_pickup_cancelled}")
                
                with col2:
                    st.markdown("**🏦 Bank Account:**")
                    st.write(f"Total: {bank_account_total}")
                    st.write(f"Completed: {bank_account_completed}")
                    st.write(f"In Progress: {bank_account_in_progress}")
                    st.write(f"Cancelled: {bank_account_cancelled}")
                
                st.markdown("---")
            else:
                st.info("No transactions for this day.")

    with tab2:
        st.subheader("Unique & New Customers per Month")
        view_by = st.radio("View by", ["Month", "Day"], horizontal=True, key="customers_view_by")
        if view_by == "Month":
            # Status breakdown for customers (stacked bar)
            if 'status' in df_filtered.columns:
                st.markdown("**📊 Monthly Customer Summary Table**")
                
                # Calculate monthly customer stats with status breakdown
                monthly_customer_stats_with_status = []
                months = sorted(df_filtered['transaction_month'].unique(), reverse=True)
                
                for month in months:
                    month_data = df_filtered[df_filtered['transaction_month'] == month]
                    
                    # Total unique customers for this month
                    total_customers = month_data['customer_id'].nunique()
                    
                    # Get the most common status for each customer in this month
                    customer_status = month_data.groupby('customer_id')['status'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]).reset_index()
                    status_counts = customer_status['status'].value_counts()
                    
                    # Handle both spellings
                    if 'cancelled' in status_counts.index and 'canceled' in status_counts.index:
                        status_counts['cancelled'] += status_counts['canceled']
                        status_counts = status_counts.drop('canceled')
                    elif 'canceled' in status_counts.index:
                        status_counts = status_counts.rename({'canceled': 'cancelled'})
                    
                    completed = status_counts.get('complete', 0)
                    in_progress = status_counts.get('in progress', 0)
                    cancelled = status_counts.get('cancelled', 0)
                    
                    # New customers for this month
                    first_tx_dates = df_filtered.groupby('customer_id')['transaction_date'].min().reset_index()
                    new_customers = (first_tx_dates['transaction_date'].dt.to_period('M') == month.to_period('M')).sum()
                    
                    monthly_customer_stats_with_status.append({
                        'Month': month.strftime('%B %Y'),
                        'Total Customers': total_customers,
                        'Completed': completed,
                        'In Progress': in_progress,
                        'Cancelled': cancelled,
                        'New Customers': new_customers
                    })
                
                # Create and display the table
                import pandas as pd
                summary_df = pd.DataFrame(monthly_customer_stats_with_status)
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
                
                st.markdown("**📊 Customers by Status (Stacked Bar)**")
                customer_status_monthly = df_filtered.groupby(['transaction_month', 'status'])['customer_id'].nunique().reset_index(name='Unique Customers')
                customer_status_monthly['status'] = customer_status_monthly['status'].replace({'canceled': 'cancelled'})
                import plotly.express as px
                fig_customer_status = px.bar(
                    customer_status_monthly,
                    x='transaction_month',
                    y='Unique Customers',
                    color='status',
                    barmode='stack',
                    title="Monthly Unique Customers by Status (Stacked Bar)"
                )
                fig_customer_status.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Number of Unique Customers",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_customer_status, use_container_width=True, key="monthly_customer_status_chart")
            
            # Original customer stats
            st.markdown("**📊 Customer Statistics**")
            combined = monthly_customer_stats(df_filtered)
            fig = plot_customers_with_new_and_total(combined, country)
            st.plotly_chart(fig, use_container_width=True, key="monthly_customer_stats_chart")
        else:
            min_day = df_filtered['transaction_date'].min().date()
            max_day = df_filtered['transaction_date'].max().date()
            selected_day = st.date_input("Select day", min_value=min_day, max_value=max_day, value=max_day, key="customers_day")
            day_df = df_filtered[df_filtered['transaction_date'].dt.date == selected_day]
            if not day_df.empty:
                # Status breakdown for the day (pie chart)
                if 'status' in day_df.columns:
                    st.markdown(f"**📊 Customer Status for {selected_day} (Pie Chart)**")
                    customer_status_counts = day_df.groupby('status')['customer_id'].nunique()
                    # Handle both spellings
                    if 'cancelled' in customer_status_counts.index and 'canceled' in customer_status_counts.index:
                        customer_status_counts['cancelled'] += customer_status_counts['canceled']
                        customer_status_counts = customer_status_counts.drop('canceled')
                    elif 'canceled' in customer_status_counts.index:
                        customer_status_counts = customer_status_counts.rename({'canceled': 'cancelled'})
                    
                    import plotly.express as px
                    fig_customer_status = px.pie(values=customer_status_counts.values, names=customer_status_counts.index, title=f"Customer Status for {selected_day}")
                    st.plotly_chart(fig_customer_status, use_container_width=True, key="daily_customer_status_chart")
                
                # Active customers for the day
                active_customers = day_df['customer_id'].nunique()
                # New customers for the day (first-ever transaction on this day)
                first_tx_dates = df_filtered.groupby('customer_id')['transaction_date'].min().reset_index()
                new_customers = (first_tx_dates['transaction_date'].dt.date == selected_day).sum()
                
                # Calculate status breakdown for active customers
                if 'status' in day_df.columns:
                    # For active customers, count each customer only once
                    # Get the most common status for each customer on this day
                    customer_status = day_df.groupby('customer_id')['status'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]).reset_index()
                    
                    # Count customers by their most common status
                    status_counts = customer_status['status'].value_counts()
                    
                    # Handle both spellings
                    if 'cancelled' in status_counts.index and 'canceled' in status_counts.index:
                        status_counts['cancelled'] += status_counts['canceled']
                        status_counts = status_counts.drop('canceled')
                    elif 'canceled' in status_counts.index:
                        status_counts = status_counts.rename({'canceled': 'cancelled'})
                    
                    completed_active = status_counts.get('complete', 0)
                    in_progress_active = status_counts.get('in progress', 0)
                    cancelled_active = status_counts.get('cancelled', 0)
                    active_breakdown = f"({completed_active} completed, {in_progress_active} in progress, {cancelled_active} cancelled)"
                else:
                    active_breakdown = ""
                
                # Calculate status breakdown for new customers
                if 'status' in day_df.columns:
                    # Get only the customers who are actually new (first transaction on this day)
                    new_customer_ids = first_tx_dates[first_tx_dates['transaction_date'].dt.date == selected_day]['customer_id'].tolist()
                    new_customers_data = day_df[day_df['customer_id'].isin(new_customer_ids)]
                    
                    # For new customers, we need to count each customer only once, not multiple transactions
                    # Get the status of each new customer's first transaction on this day
                    new_customers_status = []
                    for customer_id in new_customer_ids:
                        customer_transactions = new_customers_data[new_customers_data['customer_id'] == customer_id]
                        if not customer_transactions.empty:
                            # Take the first transaction's status for this customer
                            first_status = customer_transactions.iloc[0]['status']
                            new_customers_status.append(first_status)
                    
                    # Count the statuses
                    from collections import Counter
                    status_counter = Counter(new_customers_status)
                    
                    completed_new = status_counter.get('complete', 0)
                    in_progress_new = status_counter.get('in progress', 0)
                    cancelled_new = status_counter.get('cancelled', 0) + status_counter.get('canceled', 0)
                    new_breakdown = f"({completed_new} completed, {in_progress_new} in progress, {cancelled_new} cancelled)"
                else:
                    new_breakdown = ""
                
                st.metric("Active Customers", f"{active_customers} {active_breakdown}")
                st.metric("New Customers", f"{new_customers} {new_breakdown}")
            else:
                st.info("No customer data for this day.")

    with tab3:
        st.subheader("Cohort Analysis")
        retention, cohort_labels = run_cohort_analysis(df_filtered)
        st.write("Retention Table:")
        # st.dataframe(retention)
        st.write("Cohort Sizes:")
        st.write(cohort_labels)
        st.pyplot(plot_cohort_heatmap(retention, cohort_labels, country))

    with tab4:
        st.subheader("Country, Network, Reason, Governorate Breakdown")
        # Prepare month options
        month_options = ["All period"]
        if 'transaction_month' in df_filtered.columns:
            months = sorted(df_filtered['transaction_month'].dt.to_period('M').unique())
            month_options += [str(m) for m in months]
        # Pie: Transactions by country
        selected_month_country = st.selectbox("Select period for Country breakdown", options=month_options, key='country_period')
        if selected_month_country == "All period":
            df_period = df_filtered
        else:
            period = pd.Period(selected_month_country)
            df_period = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
        tx_counts = df_period['country'].value_counts().reset_index()
        tx_counts.columns = ['Country', 'Total Transactions']
        st.plotly_chart(plot_pie(tx_counts['Country'], tx_counts['Total Transactions'], f'Total Transactions by Country'), use_container_width=True, key="country_tx_chart")
        # Pie: Unique customers by country
        selected_month_customers = st.selectbox("Select period for Unique Customers breakdown", options=month_options, key='customers_period')
        if selected_month_customers == "All period":
            df_period = df_filtered
        else:
            period = pd.Period(selected_month_customers)
            df_period = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
        unique_customers = df_period.groupby('country')['customer_id'].nunique().reset_index()
        unique_customers.columns = ['Country', 'Unique Customers']
        st.plotly_chart(plot_pie(unique_customers['Country'], unique_customers['Unique Customers'], 'Unique Customers by Country'), use_container_width=True, key="country_cust_chart")
        # Pie: Reason (if exists)
        if 'reason' in df_filtered.columns:
            selected_month_reason = st.selectbox("Select period for Reason breakdown", options=month_options, key='reason_period')
            if selected_month_reason == "All period":
                df_period = df_filtered
            else:
                period = pd.Period(selected_month_reason)
                df_period = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
            reason_counts = df_period['reason'].value_counts().reset_index()
            reason_counts.columns = ['Reason', 'Transaction Count']
            st.plotly_chart(plot_pie(reason_counts['Reason'], reason_counts['Transaction Count'], f"Reasons for Money Transfers"), use_container_width=True, key="reason_chart")
        # Pie: Network (if exists)
        if 'network' in df_filtered.columns:
            selected_month_network = st.selectbox("Select period for Network breakdown", options=month_options, key='network_period')
            if selected_month_network == "All period":
                df_period = df_filtered
            else:
                period = pd.Period(selected_month_network)
                df_period = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
            network_counts = df_period['network'].str.strip().str.title().value_counts().reset_index()
            network_counts.columns = ['Network', 'Transaction Count']
            st.plotly_chart(plot_pie(network_counts['Network'], network_counts['Transaction Count'], f'Network Usage'), use_container_width=True, key="network_chart")
        # Pie: Governorate (if exists)
        if 'gov' in df_filtered.columns:
            selected_month_gov = st.selectbox("Select period for Governorate breakdown", options=month_options, key='gov_period')
            if selected_month_gov == "All period":
                df_period = df_filtered
            else:
                period = pd.Period(selected_month_gov)
                df_period = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
            gov_counts = df_period['gov'].value_counts().reset_index()
            gov_counts.columns = ['Governorate', 'Transaction Count']
            st.plotly_chart(plot_pie(gov_counts['Governorate'], gov_counts['Transaction Count'], f'Transaction Distribution by Governorate'), use_container_width=True, key="gov_chart")

    with tab5:
        st.subheader("Cities Analysis")
        if 'gov' in df_filtered.columns and 'ville' in df_filtered.columns:
            govs = sorted(df_filtered['gov'].dropna().unique())
            selected_gov = st.selectbox("Select Governorate", options=govs)
            villes = sorted(df_filtered[df_filtered['gov'] == selected_gov]['ville'].dropna().unique())
            selected_ville = st.selectbox("Select City", options=villes)
            city_df = df_filtered[(df_filtered['gov'] == selected_gov) & (df_filtered['ville'] == selected_ville)]
            # Add view by option
            view_by = st.radio("View by", ["Month", "Day"], horizontal=True, key="city_view_by")
            if not city_df.empty:
                if view_by == "Month":
                    monthly = city_df.groupby(city_df['transaction_month']).agg(
                        Transactions=('customer_id', 'count'),
                        Active_Customers=('customer_id', 'nunique')
                    ).reset_index()
                    import plotly.express as px
                    fig1 = px.line(monthly, x='transaction_month', y='Transactions', title=f"Transactions Over Time - {selected_ville}")
                    fig2 = px.line(monthly, x='transaction_month', y='Active_Customers', title=f"Active Customers Over Time - {selected_ville}")
                    st.plotly_chart(fig1, use_container_width=True, key="city_tx_chart")
                    st.plotly_chart(fig2, use_container_width=True, key="city_cust_chart")
                else:
                    # Day view
                    min_day = city_df['transaction_date'].min().date()
                    max_day = city_df['transaction_date'].max().date()
                    selected_day = st.date_input("Select day", min_value=min_day, max_value=max_day, value=max_day, key="city_day")
                    day_df = city_df[city_df['transaction_date'].dt.date == selected_day]
                    if not day_df.empty:
                        transactions = day_df.shape[0]
                        active_customers = day_df['customer_id'].nunique()
                        st.metric("Transactions", transactions)
                        st.metric("Active Customers", active_customers)
                        # Optionally, plot a bar
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[
                            go.Bar(name='Transactions', x=[str(selected_day)], y=[transactions]),
                            go.Bar(name='Active Customers', x=[str(selected_day)], y=[active_customers])
                        ])
                        fig.update_layout(barmode='group', title=f"City Activity for {selected_ville} on {selected_day}")
                        st.plotly_chart(fig, use_container_width=True, key="city_day_chart")
                    else:
                        st.info("No data for this city on the selected day.")
                # Withdrawal points breakdown with period selector
                if 'network' in city_df.columns:
                    month_options = ["All period"]
                    if 'transaction_month' in city_df.columns:
                        months = sorted(city_df['transaction_month'].dt.to_period('M').unique())
                        month_options += [str(m) for m in months]
                    selected_month_network_city = st.selectbox("Select period for Withdrawal Points", options=month_options, key='city_network_period')
                    if selected_month_network_city == "All period":
                        city_period_df = city_df
                    else:
                        period = pd.Period(selected_month_network_city)
                        city_period_df = city_df[city_df['transaction_month'].dt.to_period('M') == period]
                    network_counts = city_period_df['network'].str.strip().str.title().value_counts().reset_index()
                    network_counts.columns = ['Network', 'Transaction Count']
                    st.plotly_chart(plot_pie(network_counts['Network'], network_counts['Transaction Count'], f'Withdrawal Points in {selected_ville}'), use_container_width=True, key="city_network_chart")
            else:
                st.info("No data for this city.")
        else:
            st.info("City and governorate data not available in this dataset.")

    with tab6:
        st.subheader("Promo Codes Analysis")
        if 'promoCode' in df_filtered.columns:
            promo_valid = df_filtered[df_filtered['promoCode'].notna() & (df_filtered['promoCode'].str.strip() != '')].copy()
            if not promo_valid.empty:
                promo_valid['promoCode_clean'] = promo_valid['promoCode'].str.strip().str.lower()
                promo_counts = promo_valid['promoCode_clean'].value_counts().reset_index()
                promo_counts.columns = ['Promo Code', 'Usage Count']
                st.write("Promo Code Usage:")
                st.dataframe(promo_counts, hide_index=True)
                st.plotly_chart(plot_pie(promo_counts['Promo Code'], promo_counts['Usage Count'], f"Promo Code Usage - {country}"), use_container_width=True, key="promo_chart")
            else:
                st.info("No valid promo codes found.")
        else:
            st.info("Promo code data not available in this dataset.")

    with tab7:
        st.subheader("RFM Segmentation")
        import plotly.express as px
        # Reference date: day after last transaction
        reference_date = df_filtered['transaction_date'].max() + pd.Timedelta(days=1)
        # Calculate RFM
        rfm = df_filtered.groupby('customer_id').agg({
            'transaction_date': lambda x: (reference_date - x.max()).days,  # Recency
            '_id': 'count',                                                 # Frequency
            'amountToSend': 'sum'                                           # Monetary
        }).reset_index()
        rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
        rfm['R_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm['M_score'] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm['RFM_score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
        # Segment function
        def refined_segment(row):
            if row['R_score'] >= 4 and row['F_score'] >= 4 and row['M_score'] >= 4:
                return 'Champions'
            elif row['F_score'] >= 4 and row['R_score'] >= 3:
                return 'Loyal'
            elif row['R_score'] >= 4:
                return 'Recent'
            elif row['F_score'] >= 4:
                return 'Frequent'
            elif row['M_score'] >= 4:
                return 'Big Spenders'
            elif row['R_score'] <= 2 and row['F_score'] <= 2:
                return 'Dormant'
            else:
                return 'Others'
        rfm['segment'] = rfm.apply(refined_segment, axis=1)
        st.write("RFM Table (first 10 rows):")
        st.dataframe(rfm.head(10), hide_index=True)
        # Prepare data for Plotly
        segment_counts = rfm['segment'].value_counts().reset_index()
        segment_counts.columns = ['segment', 'count']
        fig = px.bar(
            segment_counts,
            x='segment',
            y='count',
            labels={'segment': 'Segment', 'count': 'Number of Customers'},
            title='Customer Distribution by RFM Segment',
            color='segment',
            text='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(xaxis_title='Segment', yaxis_title='Number of Customers')
        st.plotly_chart(fig, use_container_width=True, key="rfm_chart")
        # Download button for RFM CSV
        csv = rfm.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download RFM Analysis as CSV",
            data=csv,
            file_name='rfm_analysis.csv',
            mime='text/csv'
        )
        st.markdown("""
#### RFM Segments – Understanding the Scores and Categories

**What do the R, F, and M scores mean?**
- **Recency (R):** How recently a customer made a transaction.  
  - Score **5** = Most recent, **1** = Longest ago.
- **Frequency (F):** How often a customer makes transactions.  
  - Score **5** = Most frequent, **1** = Least frequent.
- **Monetary (M):** How much money a customer sends.  
  - Score **5** = Sends the most, **1** = Sends the least.

Each customer receives a score from 1 (lowest) to 5 (highest) for each metric, based on their activity compared to all other customers. These scores are then used to assign customers to the segments below.

---

#### Who is Each Segment?

- **Champions**  
  **Who are they?**  
  Customers who are very recent, very active, and have high transaction value (R_score ≥ 4, F_score ≥ 4, M_score ≥ 4).  
  **These are our most valuable customers.** They transact often, send large amounts, and have made transactions recently. We should focus on keeping them happy and loyal—they are our top priority.

- **Loyal**  
  **Who are they?**  
  Customers who transact frequently and have been active recently (F_score ≥ 4, R_score ≥ 3).  
  **These are our regulars.** They make repeat transactions and show strong engagement over time. We should reward their loyalty and keep them coming back.

- **Recent**  
  **Who are they?**  
  Customers who have made transactions recently, but not yet frequently or with high value (R_score ≥ 4).  
  **These are our new or recently reactivated customers.** They may become loyal or high-value with the right encouragement.

- **Frequent**  
  **Who are they?**  
  Customers who make transactions often, even if their last transaction was a while ago or their amount is low (F_score ≥ 4).  
  **These are our frequent users.** They are used to our service, but may need incentives to send more or return sooner.

- **Big Spenders**  
  **Who are they?**  
  Customers who send large amounts, even if they are not recent or frequent (M_score ≥ 4).  
  **These are our high-value customers.** They have strong economic potential. We should try to re-engage and retain them.

- **Dormant**  
  **Who are they?**  
  Customers who haven’t made transactions recently and are not active (R_score ≤ 2 and F_score ≤ 2).  
  **These are our inactive customers.** They are at risk of being lost. We should consider targeted reactivation campaigns.

- **Others**  
  **Who are they?**  
  Customers who don’t fit into the above categories.  
  **These are our intermediate or irregular customers.** Their behavior is mixed, but with the right marketing, they could move into more valuable segments.
""")
    with tab8:
        st.subheader("Month Comparison")
        if 'transaction_month' in df_filtered.columns and 'ville' in df_filtered.columns:
            months = sorted(df_filtered['transaction_month'].dt.to_period('M').unique())
            month_options = [str(m) for m in months]
            col1, col2 = st.columns(2)
            with col1:
                selected_month1 = st.selectbox("Select First Month", options=month_options, key='month1')
            with col2:
                selected_month2 = st.selectbox("Select Second Month", options=month_options, key='month2')
            # Prepare data for both months
            def get_month_data(month_str):
                period = pd.Period(month_str)
                month_df = df_filtered[df_filtered['transaction_month'].dt.to_period('M') == period]
                by_city = month_df.groupby('ville').agg(
                    Transactions=('customer_id', 'count'),
                    Unique_Customers=('customer_id', 'nunique')
                ).reset_index()
                return by_city
            data1 = get_month_data(selected_month1)
            data2 = get_month_data(selected_month2)
            from src.utils import group_top_n_with_other
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**{selected_month1}**")
                city_data1_tx, _ = group_top_n_with_other(data1[['ville', 'Transactions']].copy(), 'Transactions', top_n=8)
                city_data1_cust, _ = group_top_n_with_other(data1[['ville', 'Unique_Customers']].copy(), 'Unique_Customers', top_n=8)
                st.plotly_chart(plot_pie(city_data1_tx['ville'], city_data1_tx['Transactions'], f"Transactions by City - {selected_month1}"), use_container_width=True, key="month1_tx")
                st.plotly_chart(plot_pie(city_data1_cust['ville'], city_data1_cust['Unique_Customers'], f"Unique Customers by City - {selected_month1}"), use_container_width=True, key="month1_cust")
            with c2:
                st.write(f"**{selected_month2}**")
                city_data2_tx, _ = group_top_n_with_other(data2[['ville', 'Transactions']].copy(), 'Transactions', top_n=8)
                city_data2_cust, _ = group_top_n_with_other(data2[['ville', 'Unique_Customers']].copy(), 'Unique_Customers', top_n=8)
                st.plotly_chart(plot_pie(city_data2_tx['ville'], city_data2_tx['Transactions'], f"Transactions by City - {selected_month2}"), use_container_width=True, key="month2_tx")
                st.plotly_chart(plot_pie(city_data2_cust['ville'], city_data2_cust['Unique_Customers'], f"Unique Customers by City - {selected_month2}"), use_container_width=True, key="month2_cust")
        else:
            st.info("Month or city data not available in this dataset.")
else:
    st.info("Please upload a CSV file to begin analysis.") 