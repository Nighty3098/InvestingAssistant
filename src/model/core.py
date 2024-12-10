from datetime import datetime, timedelta

import joblib
import numpy as np
import yfinance as yf
from keras.models import load_model

# Загрузка модели и скейлера
model = load_model("stock_model.h5")
scaler = joblib.load("scaler.save")


# Прогнозирование цен акций на месяц вперед
def predict_price(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    data = yf.download(
        ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d")
    )

    last_60_days = data["Close"].values[-60:].reshape(-1, 1)

    # Нормализация данных
    last_60_days_scaled = scaler.transform(last_60_days)

    # Формирование входных данных для модели
    X_test = []
    X_test.append(last_60_days_scaled)
    X_test = np.array(X_test)
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    # Прогнозирование
    predicted_price = model.predict(X_test)

    # Обратное преобразование к исходному масштабу
    predicted_price = scaler.inverse_transform(predicted_price)

    return predicted_price[0][0]


# Основная функция с советом по покупке/продаже/удержанию
if __name__ == "__main__":
    ticker = "NVDA"
    predicted_price = predict_price(ticker)

    current_price = yf.download(ticker, period="1d")["Close"][-1]

    print(
        f"Predicted price for {ticker} next month: {predicted_price:.2f}\nCurrent price: {current_price:.2f}"
    )

    if predicted_price > current_price:
        print("Advice: Buy")
    elif predicted_price < current_price:
        print("Advice: Sell")
    else:
        print("Advice: Hold")
