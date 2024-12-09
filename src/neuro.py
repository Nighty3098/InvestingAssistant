import random
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import Sequential

np.random.seed(42)
random.seed(42)
tf.random.set_seed(42)

end_date = datetime.now().date()
start_date = end_date - timedelta(days=2 * 365)

ticker = "AAPL"

data = yf.download(ticker, start=start_date, end=end_date)
data = data[["Close"]]

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)


def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step - 1):
        X.append(data[i : (i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)


time_step = 60
X, y = create_dataset(scaled_data, time_step)

X = X.reshape(X.shape[0], X.shape[1], 1)
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

model.compile(optimizer="adam", loss="mean_squared_error")

early_stopping = EarlyStopping(monitor="loss", patience=5, restore_best_weights=True)

model.fit(X, y, batch_size=1, epochs=50, callbacks=[early_stopping])


def predict_price(model, data, days=1):
    predictions = []
    last_data = data[-time_step:].reshape(1, time_step, 1)

    for _ in range(days):
        pred = model.predict(last_data)
        predictions.append(pred[0][0])
        last_data = np.append(last_data[:, 1:, :], pred.reshape(1, 1, 1), axis=1)

    return scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()


pred_tomorrow = predict_price(model, scaled_data, days=1)[0]
pred_month = predict_price(model, scaled_data, days=60)

current_price = data["Close"].iloc[-1]


def give_advice(current_price, predicted_price):
    if predicted_price > current_price:
        advice = "Buy"
        probability = (predicted_price - current_price) / current_price * 100
    elif predicted_price < current_price:
        advice = "Sell"
        probability = (current_price - predicted_price) / current_price * 100
    else:
        advice = "Wait"
        probability = 0

    return advice, probability


advice_tomorrow, probability_tomorrow = give_advice(current_price, pred_tomorrow)

advice_month, probability_month = give_advice(current_price, pred_month[-1])

print(f"Current price AAPL: {current_price:.2f}")
print(f"Predicted price for tomorrow: {pred_tomorrow:.2f}")

print(f"Predicted price for the next month: {pred_month[-1]:.2f}")
print(f"Advice: {advice_month} (Probability: {abs(probability_month):.2f}%)")
