import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import yfinance as yf
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from config import logger

class StockPredictor:
    def __init__(self, model_path=None, scaler_path=None):
        self.base_dir = Path(__file__).parent.parent / "IPSA_MODEL" / "price"

        self.model_path = model_path or self.base_dir / "best_model.keras"
        self.scaler_path = scaler_path or self.base_dir / "stock_scaler.save"
        self._check_files_exist()

        self.model = load_model(str(self.model_path))
        self.scaler = joblib.load(str(self.scaler_path))

        # Set window_size to match the model's expected input (60 time steps)
        self.window_size = 60  # Changed from 365 to match model expectation
        self.forecast_days = 60

    def _check_files_exist(self):
        missing_files = []

        if not self.model_path.exists():
            missing_files.append(str(self.model_path))

        if not self.scaler_path.exists():
            missing_files.append(str(self.scaler_path))

        if missing_files:
            raise FileNotFoundError(
                f"Missing required files: {', '.join(missing_files)}\n"
                "Please train the model first or provide correct paths."
            )

    def predict_future(self, ticker):
        if not hasattr(self, 'scaler') or not isinstance(self.scaler, MinMaxScaler):
            self.scaler = MinMaxScaler()
            logger.info("Initialized new MinMaxScaler")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_size + self.forecast_days)

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)

                if data.empty:
                    raise ValueError(f"No historical data for {ticker}")

                feature_data = data[["Open", "High", "Low", "Close", "Volume"]].values

                if not hasattr(self.scaler, 'data_min_'):
                    self.scaler.fit(feature_data)
                    logger.info(f"Scaler fitted with data for {ticker}")

                scaled_data = self.scaler.transform(feature_data)

                # Ensure current_window has exactly self.window_size (60) time steps
                if len(scaled_data) < self.window_size:
                    raise ValueError(f"Not enough data points ({len(scaled_data)}) for window_size {self.window_size}")
                current_window = scaled_data[-self.window_size:]  # Shape: (60, 5)

                predictions = []
                for _ in range(self.forecast_days):
                    # Predict with shape (1, 60, 5)
                    next_pred = self.model.predict(current_window[np.newaxis, ...])[0][0]

                    new_row = np.array([[
                        next_pred,  # Open
                        next_pred,  # High
                        next_pred,  # Low
                        next_pred,  # Close
                        current_window[-1, 4],  # Volume
                    ]])

                    current_window = np.concatenate([current_window[1:], new_row], axis=0)
                    predictions.append(next_pred)

                dummy_data = np.zeros((len(predictions), 5))
                dummy_data[:, 0] = predictions
                
                predictions = self.scaler.inverse_transform(dummy_data)[:, 0]

                return predictions

            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {ticker}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Failed to predict future for {ticker} after {max_retries} attempts")
                    raise

    def analyze(self, ticker, threshold=0.05):
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    predictions = self.predict_future(ticker)

                    data = yf.download(ticker, period="1d")
                    if data.empty:
                        return f"Data not found {ticker}"

                    current_price = float(data["Open"].iloc[-1])

                    avg_prediction = np.mean(predictions)
                    price_change = (avg_prediction - current_price) / current_price

                    message = (
                        "────────────────────────────\n"
                        f"{self.forecast_days}-daily forecast for {ticker}\n"
                        f"Current price: {current_price:.2f}\n"
                        f"Average projected price: {avg_prediction:.2f}\n"
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

                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error in analyze: {str(e)}", exc_info=True)
            return "Error in generating the forecast. The API request limit may have been exceeded.."

    def predict_plt(self, ticker, user_id):
        predictions = self.predict_future(ticker)
        history = yf.download(ticker, period="6mo")["Open"]

        plt.figure(figsize=(14, 7))
        plt.plot(history, label="Historical Price")

        future_dates = pd.date_range(history.index[-1], periods=self.forecast_days + 1)[1:]
        plt.plot(
            future_dates,
            predictions,
            label=f"{self.forecast_days}-day Forecast",
            linestyle="--",
        )

        plt.scatter(future_dates[0], predictions[0], color="red", zorder=5)
        plt.scatter(future_dates[-1], predictions[-1], color="green", zorder=5)

        plt.fill_between(
            future_dates,
            np.min(predictions) * 0.95,
            np.max(predictions) * 1.05,
            alpha=0.2,
            color="gray",
        )

        plt.title(f"{ticker} Price Forecast")
        plt.legend()

        filename = f"forecast_{user_id}_{ticker}.png"
        plt.savefig(filename)
        plt.close()

        return filename


if __name__ == "__main__":
    ticker = "NVDA"
    predictor = StockPredictor()
    print(predictor.analyze(ticker))
    print(predictor.predict_plt(ticker, "231312"))
