import pandas as pd
import numpy as np

def run_cohort_analysis(df_country: pd.DataFrame):
    df_country = df_country.copy()
    # Assign cohort month (first transaction month per customer)
    df_country['cohort_month'] = df_country.groupby('customer_id')['transaction_month'].transform('min')
    # Extract year/month for transaction and cohort
    transaction_year = df_country['transaction_month'].dt.year
    transaction_month = df_country['transaction_month'].dt.month
    cohort_year = df_country['cohort_month'].dt.year
    cohort_month = df_country['cohort_month'].dt.month
    # Calculate cohort index
    df_country['cohort_index'] = (transaction_year - cohort_year) * 12 + (transaction_month - cohort_month) + 1
    # Build cohort table (number of unique customers)
    cohort_data = df_country.groupby(['cohort_month', 'cohort_index'])['customer_id'].nunique().reset_index()
    cohort_counts = cohort_data.pivot_table(index='cohort_month', columns='cohort_index', values='customer_id')
    # Compute retention rates
    cohort_sizes = cohort_counts.iloc[:, 0]
    retention = cohort_counts.divide(cohort_sizes, axis=0).round(3) * 100
    retention.index = retention.index.strftime('%Y-%m')
    cohort_labels = [f"{index.strftime('%Y-%m')} ({int(size)})" for index, size in zip(cohort_counts.index, cohort_sizes)]
    return retention, cohort_labels 