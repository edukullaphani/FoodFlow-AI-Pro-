import pandas as pd
from datetime import datetime

def compute_consumption_rate(df):
    return df['consumption'].mean()

def compute_days_to_expiry(df):
    # Assume expiry_date is the same for all, take first
    expiry = pd.to_datetime(df['expiry_date'].iloc[0])
    today = datetime.now()
    days = (expiry - today).days
    return max(0, days)  # if expired, 0