import os
from datetime import datetime, timedelta
from os import path

import joblib
import numpy as np
import yfinance as yf
from keras.models import load_model


class StockPredictor:
    def __init__(self):
        self.model_path = os.path.join(
            os.getcwd(), "IPSA_MODEL", "src", "stock_model.keras"
        )
        self.scaler_path = os.path.join(os.getcwd(), "IPSA_MODEL", "src", "scaler.save")

        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def predict_price(self, ticker):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )

        last_60_days = data["Close"].values[-60:].reshape(-1, 1)

        last_60_days_scaled = self.scaler.transform(last_60_days)

        X_test = []
        X_test.append(last_60_days_scaled)
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

        predicted_price = self.model.predict(X_test)

        predicted_price = self.scaler.inverse_transform(predicted_price)

        return predicted_price[0][0]

    def analyze(self, ticker):
        predicted_price = self.predict_price(ticker)

        current_price = yf.download(ticker, period="1d")["Close"][-1]

        message = f"Predicted price for {ticker} next month: {predicted_price:.2f}\nCurrent price: {current_price:.2f}\n"

        if predicted_price > current_price:
            message += "Advice: Buy"
        elif predicted_price < current_price:
            message += "Advice: Sell"
        else:
            message += "Advice: Hold"
        return message


if __name__ == "__main__":
    stock_predictor = StockPredictor()
    print(stock_predictor.analyze("AAPL"))
