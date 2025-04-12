import pandas as pd
import yfinance as yf

class ReportTable:
    def __init__(self, ticker) -> None:
        self.report_path = f"client_data/{ticker}_report.xlsx"
    
    def download_data(self, ticker):
        ticker = yf.Ticker(ticker)
        ticker_info = ticker.info
        return ticker_info
    
    def save_report(self, data):
        df = pd.DataFrame([data])

        with pd.ExcelWriter(self.report_path) as writer:
            df.to_excel(writer, sheet_name='REPORT', index=False)

        return self.report_path
