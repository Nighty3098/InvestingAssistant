from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from keras.layers import LSTM, Dense
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

from config import home_dir, logger


class CustomCallback(Callback):
    def __init__(self, user_id, app, wait_message):
        super().__init__()
        self.user_id = user_id
        self.app = app
        self.wait_message = wait_message

    def on_epoch_end(self, epoch, logs=None):
        # Обновляем текст сообщения с процентом завершения
        percent_complete = (epoch + 1) / self.params["epochs"] * 100
        message = f"Epochs: {percent_complete:.2f}%"

        self.app.loop.create_task(
            self.app.edit_message_text(
                chat_id=self.user_id, message_id=self.wait_message.id, text=message
            )
        )


class StockModel:
    def __init__(self, ticker):
        self.ticker = ticker
        self.model = None
        self.scaler = None

    def load_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 5)

        data = yf.download(
            self.ticker, start=start_date, end=end_date.strftime("%Y-%m-%d")
        )
        return data["Close"].values.reshape(-1, 1)

    def prepare_data(self, data):
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(data)

        X, y = [], []
        for i in range(60, len(scaled_data)):
            X.append(scaled_data[i - 60 : i, 0])
            y.append(scaled_data[i, 0])

        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        return X, y

    def create_model(self, input_shape):
        self.model = Sequential()
        self.model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        self.model.add(LSTM(units=50))
        self.model.add(Dense(units=1))
        self.model.compile(optimizer="adam", loss="mean_squared_error")

    def train_model(self):
        try:
            data = self.load_data()
            X, y = self.prepare_data(data)

            self.create_model((X.shape[1], 1))
            self.model.fit(X, y, epochs=500, batch_size=32)

            self.model.save(home_dir + "IPSA/stock_model.h5")
            joblib.dump(self.scaler, home_dir + "IPSA/scaler.save")
            return True
        except Exception as e:
            return False
