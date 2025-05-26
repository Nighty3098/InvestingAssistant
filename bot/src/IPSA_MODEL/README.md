# Stock Price Prediction Model Documentation 📈

**Version 1.0** | **Last Updated: May 06, 2025**

---

## 📖 Overview

This project implements a deep learning model for predicting stock prices using historical stock market data. The model leverages a combination of Convolutional Neural Networks (CNNs), Bidirectional Gated Recurrent Units (GRUs), and an Attention mechanism to capture temporal patterns and dependencies in stock data. The model is trained on a dataset containing multiple stock tickers and predicts the closing price based on a sequence of historical data.

The codebase is written in Python, utilizing TensorFlow for model building, scikit-learn for preprocessing, and pandas for data handling. The model is designed to process multiple stock tickers, scale the data, create sequences for training, and evaluate performance using metrics like Mean Absolute Error (MAE), Mean Squared Error (MSE), and R² score.

---

## 🚀 Features

- **Data Preprocessing**: Loads and preprocesses stock data, handling multiple tickers with MinMax scaling.
- **Sequence Creation**: Generates time-series sequences for training and prediction with a configurable window size.
- **Deep Learning Model**: Combines CNNs, Bidirectional GRUs, and Attention for robust feature extraction and prediction.
- **Training Pipeline**: Supports CPU/GPU training with callbacks for early stopping, model checkpointing, and logging.
- **Evaluation**: Computes MAE, MSE, and R² score on test data, with visualization of training metrics.
- **Model Persistence**: Saves trained model and scalers for future use.
- **Visualization**: Plots training and validation loss, MAE, and MSE.

---

## 🛠️ Requirements

To run the project, ensure the following dependencies are installed:

```bash
pip install pandas numpy tensorflow sklearn joblib matplotlib
```

Alternatively, create a `requirements.txt` file:

```text
pandas>=2.0.0
numpy>=1.24.0
tensorflow>=2.12.0
scikit-learn>=1.2.0
joblib>=1.2.0
matplotlib>=3.7.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 📂 Project Structure

```
stock_prediction/
├── combined_stock_data.csv   # Input dataset (not included)
├── stock_model.keras         # Trained model (generated)
├── best_model.keras          # Best model checkpoint (generated)
├── stock_scaler.save         # Saved scalers (generated)
├── training_log.csv          # Training logs (generated)
├── training_metrics.png      # Training metrics plot (generated)
├── logs/                     # TensorBoard logs (generated)
└── main.py                   # Main script
```

---

## 📊 Data Format

The input dataset (`combined_stock_data.csv`) should contain historical stock data for multiple tickers with the following columns:

| Column        | Description                          | Type       |
|---------------|--------------------------------------|------------|
| Date          | Date of the stock data               | datetime   |
| Ticker        | Stock ticker symbol                  | string     |
| Open          | Opening price                        | float      |
| High          | Highest price of the day             | float      |
| Low           | Lowest price of the day              | float      |
| Close         | Closing price (prediction target)    | float      |
| Volume        | Trading volume                       | float      |
| Dividends     | Dividends paid                       | float      |
| Stock Splits  | Stock split ratio                    | float      |

Example:

```csv
Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits
2023-01-01,AAPL,130.28,132.67,129.61,131.86,123456789,0.0,0.0
2023-01-01,MSFT,240.22,243.15,238.75,241.01,987654321,0.0,0.0
...
```

---

## ⚙️ Configuration

The script includes several configurable parameters defined at the top of `main.py`:

| Parameter       | Description                              | Default Value |
|-----------------|------------------------------------------|---------------|
| `WINDOW_SIZE`   | Number of time steps in each sequence    | 60            |
| `EPOCHS`        | Maximum number of training epochs        | 1000          |
| `BATCH_SIZE`    | Batch size for training                  | 128           |

To modify these, edit the constants in `main.py`:

```python
WINDOW_SIZE = 60
EPOCHS = 1000
BATCH_SIZE = 128
```

---

## 🏃‍♂️ Running the Project

1. **Prepare the Dataset**:
   Ensure `combined_stock_data.csv` is in the project directory with the required format.

2. **Run the Script**:
   Execute the main script, specifying the device (CPU or GPU):

   ```bash
   python main.py
   ```

   The script will prompt for the device choice:
   ```
   Choose device for training (cpu/gpu):
   ```

3. **Outputs**:
   - `stock_model.keras`: Final trained model.
   - `best_model.keras`: Best model based on validation loss.
   - `stock_scaler.save`: Saved MinMax scalers for each ticker.
   - `training_log.csv`: CSV log of training metrics.
   - `training_metrics.png`: Plot of training and validation loss, MAE, and MSE.
   - `logs/`: TensorBoard logs for visualization.

4. **View TensorBoard**:
   Visualize training progress using TensorBoard:

   ```bash
   tensorboard --logdir logs/
   ```

   Open `http://localhost:6006` in a browser to view the training metrics.

---

## 🧠 Model Architecture

The model is a hybrid deep learning architecture combining CNNs, Bidirectional GRUs, and an Attention mechanism. Below is a summary of the layers:

1. **Input Layer**:
   - Shape: `(WINDOW_SIZE, num_features)` (e.g., `(60, 8)` for 8 features).

2. **Convolutional Layers**:
   - 5 Conv1D layers with filters (2048, 1024, 512, 256, 128), kernel size 5, ReLU activation, and causal padding.
   - Each Conv1D is followed by BatchNormalization and Dropout (0.3).
   - A MaxPooling1D layer (pool size 2) is applied after the last Conv1D.

3. **Recurrent Layers**:
   - Two Bidirectional GRU layers (256 and 128 units) with return_sequences=True.
   - Dropout (0.4) applied after each GRU layer.

4. **Attention Layer**:
   - Attention mechanism to focus on important time steps, using the GRU output as query and value.

5. **Pooling and Dense Layers**:
   - GlobalMaxPooling1D to reduce the sequence to a single vector██
   - Two Dense layers (1024 and 512 units) with ReLU activation, L2 regularization (0.02 and 0.01), BatchNormalization, and Dropout (0.5 and 0.4).
   - Final Dense layer (1 unit) for predicting the closing price.

6. **Compilation**:
   - Optimizer: AdamW (learning rate 0.0001, weight decay 0.001).
   - Loss: Mean Squared Error (MSE).
   - Metrics: MAE, MSE.

---

## 📈 Training and Evaluation

### Training Process

- **Data Split**: 80% training, 20% testing (non-shuffled to preserve temporal order).
- **Callbacks**:
  - `ModelCheckpoint`: Saves the best model based on validation loss (`best_model.keras`).
  - `EarlyStopping`: Stops training if validation loss doesn't improve for 15 epochs, restoring best weights.
  - `TensorBoard`: Logs training metrics to `./logs/`.
  - `CSVLogger`: Saves epoch-wise metrics to `training_log.csv`.

### Evaluation Metrics

The model is evaluated on the test set using:
- **Loss (MSE)**: Mean Squared Error.
- **MAE**: Mean Absolute Error.
- **MSE**: Mean Squared Error (redundant with loss but logged for clarity).
- **R² Score**: Coefficient of determination, indicating the proportion of variance explained by the model.

Example output:

```
Model evaluation on test data:
Test Loss: 0.0123
Test MAE: 0.0876
Test MSE: 0.0123
Test Accuracy (R² score): 92.45%
```

---

## 🔮 Making Predictions

To make predictions for a single stock ticker, use the following example code:

```python
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model

# Load model and scaler
model = load_model("stock_model.keras")
scalers = joblib.load("stock_scaler.save")

# Load and preprocess data for a single ticker
ticker = "AAPL"
df = pd.read_csv("combined_stock_data.csv")
company_df = df[df["Ticker"] == ticker].copy()
company_df = company_df.drop(columns=["Date", "Ticker"])
numeric_cols = ["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
company_df = company_df[numeric_cols].ffill().bfill()

# Scale data
scaler = scalers[ticker]
scaled_data = scaler.transform(company_df[numeric_cols])
scaled_df = pd.DataFrame(scaled_data, columns=numeric_cols)

# Prepare sequence
sequence = prepare_single_sequence(scaled_df)

# Predict
prediction = model.predict(sequence)[0][0]

# Inverse transform to get actual price
temp_array = np.zeros((1, len(numeric_cols)))
temp_array[0, scaled_df.columns.get_loc("Close")] = prediction
actual_price = scaler.inverse_transform(temp_array)[0, scaled_df.columns.get_loc("Close")]

print(f"Predicted closing price for {ticker}: ${actual_price:.2f}")
```

---

## 🛡️ Limitations and Assumptions

- **Stationarity**: Assumes stock price patterns are learnable from historical data, which may not always hold due to market volatility.
- **Data Quality**: Relies on clean, complete data. Missing values are handled with forward/backward fill, which may introduce bias.
- **Feature Set**: Uses a fixed set of features (Open, High, Low, Close, Volume, Dividends, Stock Splits). Additional features (e.g., news sentiment) could improve performance.
- **Sequence Length**: Fixed window size (60 days) may not be optimal for all stocks.
- **Overfitting**: Regularization (Dropout, L2) and early stopping mitigate overfitting, but complex models may still overfit on noisy financial data.

---

## 📝 Notes

- **GPU Support**: The script detects GPU availability and uses it if specified. Ensure CUDA and cuDNN are installed for GPU training.
- **Data Size**: Large datasets may require significant memory. Adjust `BATCH_SIZE` or use a smaller `WINDOW_SIZE` for memory-constrained systems.
- **Scalability**: The model processes multiple tickers sequentially. For very large datasets, consider parallel processing or batch processing.
- **Extensibility**: The model can be extended with additional features (e.g., technical indicators) or alternative architectures (e.g., Transformers).

---

## 📚 References

- TensorFlow Documentation: [https://www.tensorflow.org/](https://www.tensorflow.org/)
- scikit-learn Documentation: [https://scikit-learn.org/](https://scikit-learn.org/)
- Pandas Documentation: [https://pandas.pydata.org/](https://pandas.pydata.org/)
- Matplotlib Documentation: [https://matplotlib.org/](https://matplotlib.org/)

For further assistance, open an issue on the project repository or contact the development team.

---

**📈 Built with TensorFlow and Python**
