def detect_trend(df):
    if len(df) < 2:
        return "stable"
    first = df['consumption'].iloc[0]
    last = df['consumption'].iloc[-1]
    if last > first:
        return "increasing"
    elif last < first:
        return "decreasing"
    else:
        return "stable"