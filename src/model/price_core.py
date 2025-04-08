import os
from datetime import datetime, timedelta
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import yfinance as yf
from keras.models import load_model

class StockPredictor:
    def __init__(self, model_path=None, scaler_path=None):
        self.base_dir = Path(__file__).parent / "IPSA_MODEL" / "price"
        self.model_path = model_path or self.base_dir / "best_model.keras"
        self.scaler_path = scaler_path or self.base_dir / "stock_scaler.save"
        self._check_files_exist()

        self.model = load_model(str(self.model_path))
        self.scalers = joblib.load(str(self.scaler_path))
        self.window_size = 60
        self.forecast_days = 60

    def _check_files_exist(self):
        if not self.model_path.exists() or not self.scaler_path.exists():
            raise FileNotFoundError("Model or scaler file not found.")

    def fetch_historical_data(self, ticker):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False, actions=True)
        if data.empty:
            raise ValueError(f"No data for {ticker}")
        data = data.ffill().bfill()
        return data[["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits", "Adj Close"]]

    def predict_future(self, ticker):
        data = self.fetch_historical_data(ticker)
        scaler = self.scalers.get(ticker, list(self.scalers.values())[0])  # Используем scaler для тикера или первый доступный
        scaled_data = scaler.transform(data)

        current_window = scaled_data[-self.window_size:]
        predictions = []
        for _ in range(self.forecast_days):
            pred = self.model.predict(current_window[np.newaxis, ...], verbose=0)[0, 0]
            predictions.append(pred)
            
            # Создаем новую строку с учетом последнего предсказания только для Close
            new_row = current_window[-1].copy()
            new_row[3] = pred  # Обновляем только Close (индекс 3)
            current_window = np.vstack([current_window[1:], new_row])

        # Обратное преобразование только для Close
        dummy = np.zeros((len(predictions), 8))
        dummy[:, 3] = predictions  # Close в 4-й колонке (индекс 3)
        predictions = scaler.inverse_transform(dummy)[:, 3]
        return predictions

    def analyze(self, ticker, threshold=0.05):
        predictions = self.predict_future(ticker)
        current_price = self.fetch_historical_data(ticker)["Close"].iloc[-1]
        avg_prediction = np.mean(predictions)
        price_change = (avg_prediction - current_price) / current_price

        message = (
            f"{self.forecast_days}-day forecast for {ticker}\n"
            f"Current price: {current_price:.2f}$\n"
            f"Avg projected price: {avg_prediction:.2f}$\n"
            f"Expected change: {price_change*100:.2f}%\n"
        )
        if price_change > threshold:
            message += "Recommendation: ACTIVELY BUY"
        elif price_change > threshold / 2:
            message += "Recommendation: BUY"
        elif price_change < -threshold:
            message += "Recommendation: ACTIVELY SELL"
        elif price_change < -threshold / 2:
            message += "Recommendation: SELL"
        else:
            message += "Recommendation: KEEP"
        return message

    def predict_plt(self, ticker, user_id):
        predictions = self.predict_future(ticker)
        history = self.fetch_historical_data(ticker)
        last_close = history["Close"].iloc[-1]

        plt.figure(figsize=(14, 7))
        plt.plot(history.index, history["Close"], label="Historical Close Price")

        future_dates = pd.date_range(history.index[-1], periods=self.forecast_days + 1)[1:]
        plt.plot(future_dates, predictions, label=f"{self.forecast_days}-day Forecast", linestyle="--")
        plt.scatter([history.index[-1], future_dates[0]], [last_close, predictions[0]], color="red", zorder=5)

        plt.title(f"{ticker} Price Forecast")
        plt.legend()
        output_dir = Path("client_data")
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"forecast_{user_id}_{ticker}.png"
        plt.savefig(filename)
        plt.close()
        return filename

if __name__ == "__main__":
    predictor = StockPredictor()
    ticker = "NVDA"
    print(predictor.analyze(ticker))
    predictor.predict_plt(ticker, "231312")
