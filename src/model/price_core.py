import logging
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

logging.basicConfig(level=logging.INFO)


class StockPredictor:
    def __init__(self, model_path=None, scaler_path=None):
        # Определяем базовую директорию
        self.base_dir = Path(__file__).parent.parent / "IPSA_MODEL" / "price"

        # Устанавливаем пути по умолчанию
        self.model_path = model_path or self.base_dir / "best_model.keras"
        self.scaler_path = scaler_path or self.base_dir / "stock_scaler.save"
        # Проверяем существование файлов
        self._check_files_exist()

        # Загружаем модель и scaler
        self.model = load_model(str(self.model_path))
        self.scaler = joblib.load(str(self.scaler_path))

        self.window_size = 365
        self.forecast_days = 60

    def _check_files_exist(self):
        """Проверяет существование необходимых файлов"""
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
        # Загрузка исторических данных
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_size + self.forecast_days)

        data = yf.download(ticker, start=start_date, end=end_date)

        if data.empty:
            raise ValueError(f"No historical data for {ticker}")

        # Подготовка данных
        scaled_data = self.scaler.transform(
            data[["Open", "High", "Low", "Close", "Volume", "Adj Close"]]
        )

        # Итеративное прогнозирование
        predictions = []
        current_window = scaled_data[-self.window_size :]

        for _ in range(self.forecast_days):
            # Прогноз следующего дня
            next_pred = self.model.predict(current_window[np.newaxis, ...])[0][0]

            # Создание фиктивных данных для следующего шага
            new_row = np.array(
                [
                    [
                        next_pred,  # Open
                        next_pred,  # High
                        next_pred,  # Low
                        next_pred,  # Close
                        current_window[-1, 4],  # Volume (последнее известное значение)
                        next_pred,  # Adj Close
                    ]
                ]
            )

            # Обновление окна
            current_window = np.concatenate([current_window[1:], new_row], axis=0)
            predictions.append(next_pred)

        # Обратное масштабирование прогнозов
        dummy_data = np.zeros((len(predictions), 6))
        dummy_data[:, 3] = predictions  # Используем позицию Close
        predictions = self.scaler.inverse_transform(dummy_data)[:, 3]

        return predictions

    def analyze(self, ticker, threshold=0.05):
        try:
            predictions = self.predict_future(ticker)

            # Получаем данные и проверяем их наличие
            data = yf.download(ticker, period="1d")
            if data.empty:
                return f"No data available for {ticker}"

            # Явное преобразование к float
            current_price = float(data["Close"].iloc[-1])

            avg_prediction = np.mean(predictions)
            price_change = (avg_prediction - current_price) / current_price

            # Форматирование сообщения с округлением
            message = (
                "────────────────────────────\n"
                f"{self.forecast_days}-day forecast for {ticker}\n"
                f"Current price: {current_price:.2f}\n"
                f"Average predicted price: {avg_prediction:.2f}\n"
                f"Expected change: {price_change*100:.2f}%\n"
            )

            # Определение рекомендации
            if price_change > threshold:
                message += "Recommendation: STRONG BUY"
            elif price_change > threshold / 2:
                message += "Recommendation: BUY"
            elif price_change < -threshold:
                message += "Recommendation: STRONG SELL"
            elif price_change < -threshold / 2:
                message += "Recommendation: SELL"
            else:
                message += "Recommendation: HOLD"

            return message

        except Exception as e:
            logging.error(f"Error in analyze: {str(e)}", exc_info=True)
            return "Error generating prediction"

    def predict_plt(self, ticker, user_id):
        predictions = self.predict_future(ticker)
        history = yf.download(ticker, period="6mo")["Close"]

        plt.figure(figsize=(14, 7))
        plt.plot(history, label="Historical Price")

        future_dates = pd.date_range(history.index[-1], periods=self.forecast_days + 1)[
            1:
        ]
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
