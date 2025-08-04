import pandas as pd
import datetime as dt

def monthly_summary_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(['transaction_month', 'distributionChannel']).size().reset_index(name='Total Transactions')
    return grouped

def monthly_customer_stats(df: pd.DataFrame) -> pd.DataFrame:
    total_customers = df.groupby('transaction_month')['customer_id'].nunique().reset_index(name='Active Customers')
    new_customers = df[df['nbTransactionsPaid'] == 1].groupby('transaction_month')['customer_id'].nunique().reset_index(name='New Customers')
    combined = pd.merge(total_customers, new_customers, on='transaction_month', how='left')
    combined['New Customers'] = combined['New Customers'].fillna(0).astype(int)
    combined['Month-Year'] = combined['transaction_month'].dt.strftime('%B %Y')
    return combined 