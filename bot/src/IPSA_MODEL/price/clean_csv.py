import pandas as pd

input_file = "combined_stock_data.csv" 
output_file = "cleaned_stock_data.csv"

df = pd.read_csv(input_file)

columns_to_keep = ["Ticker", "Date", "Close", "High", "Low", "Open", "Volume"]
df_cleaned = df[columns_to_keep]

df_cleaned = df_cleaned.dropna()

df_cleaned.to_csv(output_file, index=False)

print(f"Saved as {output_file}")
