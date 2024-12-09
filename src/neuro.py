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

np.random.seed(0)
random.seed(0)
tf.random.set_seed(0)

end_date = datetime.now().date()
start_date = end_date - timedelta(days=5 * 365)

ticker = "AAPL"

data = yf.download(ticker, start=start_date, end=end_date)
data = data[["Close"]]

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)


# Function to create dataset for LSTM model
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i : (i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)


time_step = 1
X, y = create_dataset(scaled_data, time_step)
X = X.reshape(X.shape[0], X.shape[1], 1)

model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(50))
model.add(Dense(25))
model.add(Dense(1))

model.compile(optimizer="adam", loss="mean_squared_error")

early_stopping = EarlyStopping(monitor="loss", patience=5, restore_best_weights=True)
model.fit(X, y, batch_size=300, epochs=300, callbacks=[early_stopping])


# Function to predict future prices for the next month
def predict_future_prices(model, data, days=30):
    predictions = []
    last_data = data[-time_step:].reshape(1, time_step, 1)

    for _ in range(days):
        pred = model.predict(last_data)
        predictions.append(scaler.inverse_transform(pred.reshape(-1, 1))[0][0])
        last_data = np.append(last_data[:, 1:, :], pred.reshape(1, 1, 1), axis=1)

    return predictions


# Predict prices for the next month
predicted_prices = predict_future_prices(model, scaled_data)

# Calculate minimum, maximum and average predicted prices
min_price = min(predicted_prices)
max_price = max(predicted_prices)
avg_price = sum(predicted_prices) / len(predicted_prices)

# print(f"Минимально прогнозируемая цена: {min_price:.2f}")
# print(f"Максимально прогнозируемая цена: {max_price:.2f}")
print(f"Средняя прогнозируемая цена: {avg_price:.2f}")

# Plotting historical and predicted prices
plt.figure(figsize=(30, 30))
plt.plot(data.index[-100:], data["Close"][-100:], label="Historical prices")
future_dates = [data.index[-1] + pd.Timedelta(days=i) for i in range(1, 31)]
plt.plot(future_dates, predicted_prices, label="Forecast", color="orange")
plt.legend()
plt.title("AAPL share price forecast for the month")
plt.xlabel("Date")
plt.ylabel("Price")
plt.show()
