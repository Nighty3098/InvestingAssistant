import os
from datetime import datetime, timedelta
from os import path

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
import yfinance as yf
from keras.layers import LSTM, Dense
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

from config import home_dir


class TrainCallback(tf.keras.callbacks.Callback):
    def __init__(self, app, user_id, wait_message):
        self.app = app
        self.user_id = user_id
        self.wait_message = wait_message

    async def update_message(self, epoch):
        await self.app.edit_message_text(
            chat_id=self.user_id,
            message_id=self.wait_message.id,
            text=f"⏳ Обучение модели... ({epoch+1}/500)",
        )

    def on_epoch_end(self, epoch, logs=None):
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.update_message(epoch))
        loop.close()


class StockModel:
    def __init__(self, ticker):
        self.ticker = ticker
        self.model = None
        self.scaler = None

        self.model_path = os.path.join(home_dir, "IPSA", "stock_model.h5")
        self.scaler_path = os.path.join(home_dir, "IPSA", "scaler.save")

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

            self.model.save(self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            return True
        except Exception as e:
            return False
