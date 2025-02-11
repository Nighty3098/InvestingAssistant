import os
from datetime import datetime, timedelta
import logging

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
        self.model_path = model_path or os.path.join(os.getcwd(), "IPSA_MODEL", "price", "stock_model.keras")
        self.scaler_path = scaler_path or os.path.join(os.getcwd(), "IPSA_MODEL", "price", "scaler.save")

        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)


    def predict_price(self, ticker, window_size=249):  # Set window_size to match the model's expected time steps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window_size)

        # Download data
        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )

        # Select multiple features for scaling
        last_data = data[["Open", "High", "Low", "Close", "Volume", "Adj Close"]].values[-window_size:]

        # Scale the data
        last_data_scaled = self.scaler.transform(last_data)

        # Prepare data for the model
        X_test = np.array([last_data_scaled])  # Shape: (1, 249, 6)

        # Reshape to match the model's input shape
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], X_test.shape[2]))  # Shape: (1, 249, 6)

        # Predict the price
        predicted_probabilities = self.model.predict(X_test)

        # Clear session to free memory
        tf.keras.backend.clear_session()

        # Calculate the predicted price
        predicted_price = last_data[-1, 3] * (1 + (predicted_probabilities[0][0] - 0.5) * 0.1)  # Example calculation

        return float(predicted_price), float(predicted_probabilities[0][0])  # Return predicted price and probability as floats

    def analyze(self, ticker, threshold=0.05):
        predicted_price, predicted_probability = self.predict_price(ticker)

        current_price_data = yf.download(ticker, period="1d")["Close"]

        if current_price_data.empty:
            logging.error(f"No current price data found for ticker: {ticker}")
            return None

        current_price = current_price_data.iloc[-1]

        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[0]

        # Ensure both prices are floats
        current_price = float(current_price)
        predicted_price = float(predicted_price)

        # Form the message
        message = f"Predicted price for {ticker} next month: {predicted_price:.2f}$\nCurrent price: {current_price:.2f}$\n"

        # Use predicted_probability directly since it's already a float
        predicted_probability_value = predicted_probability  # No need for .item()

        logging.info(f"Probability of price increase: {predicted_probability_value:.2f}")

        price_change_percentage = (predicted_price - current_price) / current_price

        message += f"────────────────────────────\nExpected price change: {price_change_percentage * 100:.2f}%\n"

        if price_change_percentage > threshold:
            message += "Advice: Buy"
        elif price_change_percentage < -threshold:
            message += "Advice: Sell"
        else:
            message += "Advice: Wait"
        return message

    def predict_plt(self, ticker, user_id, period="6mo"):
        predicted_price, predicted_probability = self.predict_price(ticker)

        historical_data = yf.download(ticker, period=period)

        if historical_data.empty:
            logging.error(f"No historical data found for ticker: {ticker}")
            return None

        # Define forecast boundaries
        min_forecast = float(predicted_price * 0.95)  # Convert to float
        max_forecast = float(predicted_price * 1.05)  # Convert to float

        plt.figure(figsize=(14, 7))

        plt.plot(
            historical_data.index,
            historical_data["Open"],
            label="Historical Open Price",
            color="blue",
        )

        plt.plot(
            historical_data.index,
            historical_data["Close"],
            label="Historical Close Price",
            color="red",
        )

        future_dates = [
            historical_data.index[-1] + timedelta(days=i + 30) for i in range(1, 31)
        ]

        predicted_prices = [predicted_price] * len(future_dates)

        plt.plot(
            future_dates,
            predicted_prices,
            color="orange",
            label="Predicted Price",
            linestyle="--",
        )

        plt.scatter(
            future_dates[0],
            min_forecast,
            color="purple",
            label="Min Forecast",
            zorder=5,
            s=50,
        )

        plt.scatter(
            future_dates[0],
            max_forecast,
            color="gold",
            label="Max Forecast",
            zorder=5,
            s=50,
        )

        plt.axhline(
            y=min_forecast,
            color="purple",
            linestyle="--",
            label="Min Forecast Boundary",
        )
        plt.axhline(
            y=max_forecast, color="gold", linestyle="--", label="Max Forecast Boundary"
        )

        plt.text(
            future_dates[0],
            min_forecast + 2,
            f"{min_forecast:.2f}",  # This will now work
            fontsize=10,
            color="purple",
        )
        plt.text(
            future_dates[0],
            max_forecast + 2,
            f"{max_forecast:.2f}",  # This will now work
            fontsize=10,
            color="gold",
        )

        plt.scatter (
            future_dates[0],
            predicted_price,
            color="red",
            label="Predicted Price Point",
            zorder=5,
        )
        plt.text(
            future_dates[0],
            predicted_price + 2,
            f"{predicted_price:.2f}",  # This will now work
            fontsize=10,
            color="red",
        )

        plt.title(f"Price Prediction for {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Price")

        # Ensure single value
        current_price = float(historical_data["Close"].iloc[-1])

        plt.axhline(
            y=current_price,
            color="green",
            linestyle="--",
            label="Current Price",
        )

        filename = os.path.join(
            os.getcwd(), "client_data", f"stock_plot_predict_{user_id}_{ticker}.png"
        )

        plt.axis("on")
        plt.legend()
        plt.savefig(filename)

        plt.close()

        return filename

if __name__ == "__main__":
    stock_predictor = StockPredictor()
    print(stock_predictor.analyze("SBUX", 1))
    stock_predictor.predict_plt("SBUX", 1)
