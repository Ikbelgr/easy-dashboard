import pandas as pd
import datetime as dt
from typing import Optional, Tuple

def load_and_preprocess_data(file_path: str, preserve_columns: bool = False) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    
    if preserve_columns:
        # Keep original column names but still do necessary preprocessing
        original_columns = df.columns.tolist()
        # Convert to datetime and remove timezone
        df['transaction_date'] = pd.to_datetime(df['createdAt'] if 'createdAt' in df.columns else df['transaction_date'])
        df['transaction_date'] = df['transaction_date'].dt.tz_localize(None)
        # Extract transaction_month
        df['transaction_month'] = df['transaction_date'].apply(lambda x: dt.datetime(x.year, x.month, 1))
        # Convert amountToSend to numeric, handling any non-numeric values
        if 'amountToSend' in df.columns:
            df['amountToSend'] = pd.to_numeric(df['amountToSend'], errors='coerce')
        return df
    else:
        # Rename columns for consistency
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
        return df

def filter_data(df: pd.DataFrame, start_date: dt.datetime, end_date: dt.datetime, country: Optional[str]=None) -> pd.DataFrame:
    mask = (df['transaction_date'] >= start_date) & (df['transaction_date'] <= end_date)
    if country:
        mask &= (df['country'] == country)
    return df[mask].copy() 