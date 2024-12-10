from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from keras.layers import LSTM, Dense
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler


# Загрузка данных
def load_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)

    data = yf.download(ticker, start=start_date, end=end_date.strftime("%Y-%m-%d"))
    return data["Close"].values.reshape(-1, 1)


# Подготовка данных для LSTM
def prepare_data(data):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(60, len(scaled_data)):
        X.append(scaled_data[i - 60 : i, 0])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    return X, y, scaler


# Создание модели LSTM
def create_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))  # Прогнозируемая цена
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


if __name__ == "__main__":
    ticker = "NVDA"
    data = load_data(ticker)
    X, y, scaler = prepare_data(data)

    model = create_model((X.shape[1], 1))
    model.fit(X, y, epochs=50, batch_size=32)

    # Сохранение модели и скейлера
    model.save("stock_model.h5")
    joblib.dump(scaler, "scaler.save")
