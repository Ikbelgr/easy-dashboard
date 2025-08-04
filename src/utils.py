import pandas as pd

def group_top_n_with_other(df, value_col, label_col='ville', top_n=8):
    df_sorted = df.sort_values(by=value_col, ascending=False).reset_index(drop=True)
    top_df = df_sorted.iloc[:top_n].copy()
    other_df = df_sorted.iloc[top_n:]
    if not other_df.empty:
        other_sum = other_df[value_col].sum()
        other_row = pd.DataFrame({label_col: ['Other'], value_col: [other_sum]})
        combined_df = pd.concat([top_df[[label_col, value_col]], other_row], ignore_index=True)
    else:
        combined_df = top_df[[label_col, value_col]]
    total = combined_df[value_col].sum()
    combined_df['Percentage'] = (combined_df[value_col] / total * 100).round(2)
    return combined_df, total

def get_summary(df, year, month):
    filtered = df[(df['transaction_date'].dt.year == year) & (df['transaction_date'].dt.month == month)]
    return filtered.groupby(['country', 'ville']).agg(
        Total_Transactions=('customer_id', 'count'),
        Active_Customers=('customer_id', 'nunique')
    ).reset_index()

def print_data_table(data, value_col, label, total):
    print(f"\n📊 {label}")
    print(data.rename(columns={
        'ville': 'City',
        value_col: value_col.replace('_', ' ')
    }).to_string(index=False))
    print(f"➡️ Total {value_col.replace('_', ' ')}: {total:,}") 