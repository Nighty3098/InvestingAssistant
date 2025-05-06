<div align="center">
    <br>
    <img src="header.png" />
    <br>
</div>

<p align="center">
  <a href="https://github.com/Nighty3098/InvestingAssistant/stargazers">
    <br><br>
    <a href="https://discord.gg/6xEc5WFK"><img src="https://img.shields.io/discord/1238858182403559505.svg?label=Discord&logo=Discord&style=for-the-badge&color=f5a7a0&logoColor=FFFFFF&labelColor=1c1c29"></img></a>
    <br><br>
    <img class="badge" src="https://img.shields.io/github/issues/Nighty3098/InvestingAssistant?style=for-the-badge&color=dbb6ed&logoColor=ffffff&labelColor=1c1c29"  style="border-radius: 5px;"/>
    <img class="badge" src="https://img.shields.io/github/stars/Nighty3098/InvestingAssistant?style=for-the-badge&color=eed49f&logoColor=D9E0EE&labelColor=1c1c29" style="border-radius: 5px;"/>
    <img src="https://img.shields.io/github/commit-activity/t/Nighty3098/InvestingAssistant?style=for-the-badge&color=a6e0b8&logoColor=D9E0EE&labelColor=171b22" style="border-radius: 5px;"/>
</p>

<br><br><br>

# StockBot Documentation 📈

**Version 1.0** | **Last Updated: May 06, 2025**

---

> [!IMPORTANT]
> ONLY FOR PYTHON 3.12

## 📖 Overview

StockBot is a Telegram bot designed to provide users with stock market insights, including price predictions, news parsing, and fundamental analysis. Built using the **Pyrogram** library, the bot integrates with a deep learning model for stock price forecasting, a news parser for real-time market updates, and a database for user and stock management. The bot supports user authentication, stock tracking, and admin controls, with a token-based system for accessing premium features.

The project leverages **TensorFlow** for stock price predictions, **yfinance** for financial data, and **BeautifulSoup** for web scraping. It includes asynchronous news parsing, real-time notifications, and report generation in Excel format.

---

## 🚀 Features

- **User Management**: Register, manage, and delete user accounts with admin controls for banning/unbanning and role assignment.
- **Stock Tracking**: Add/remove stocks to a user's watchlist and retrieve detailed stock information.
- **Price Prediction**: Forecast stock prices for the next 60 days using a pre-trained deep learning model.
- **News Parsing**: Fetch and filter news from Investing.com, notifying users of articles relevant to their tracked stocks.
- **Fundamental Analysis**: Provide buy/sell recommendations based on financial metrics like P/E ratio, ROE, and risk factors.
- **Report Generation**: Generate Excel reports with stock data for user analysis.
- **Token System**: Limit access to premium features (e.g., price predictions) using a token-based system.
- **Admin Panel**: Manage users, assign admin roles, send tokens, and monitor system activity.
- **Multilingual Support**: Planned language selection (currently in development).
- **Asynchronous Processing**: Handle news parsing and notifications concurrently using asyncio.

---

## 🛠️ Requirements

To run StockBot, ensure the following dependencies are installed:

Install dependencies:

```bash
pip install -r req.txt
```

Additionally, you need:
- A Telegram Bot Token (obtained via [BotFather](https://t.me/BotFather)).
- API ID and API Hash from [my.telegram.org](https://my.telegram.org).
- A pre-trained stock prediction model (`best_model.keras`) and scaler (`stock_scaler.save`).

---

## 📂 Project Structure

```
<<<<<<< Updated upstream
git clone https://github.com/Nighty3098/InvestingAssistant --recurse-submodules
cd InvestingAssistant
poetry shell
poetry install
cd src
=======
StockBot/
├── client_data/                    # Generated reports and plots
├── IPSA_MODEL/price/              # Model and scaler files
│   ├── best_model.keras           # Pre-trained stock prediction model
│   └── stock_scaler.save          # MinMax scaler for data normalization
├── resources/                     # Static assets
│   ├── header.png                 # Bot welcome image
├── config.py                      # Configuration (API keys, bot token)
├── db.py                          # Database management
├── func.py                        # Utility functions
├── kb_builder/                    # Keyboard builders for UI
│   ├── admin_panel.py             # Admin keyboard and panel
│   ├── user_panel.py              # User keyboard and panel
├── model/                         # Prediction models
│   ├── influence_core.py          # News sentiment analysis (stub)
│   ├── price_core.py              # Stock price prediction
├── parsing.py                     # News parsing logic
├── create_report.py               # Report generation
├── resources/messages.py          # Predefined messages
├── main.py                        # Main bot script
└── logs/                          # Log files (generated)
>>>>>>> Stashed changes
```

---

## ⚙️ Configuration

1. **Environment Variables**:
   Create a `config.py` file with the following:

   ```python
   API_ID = "your_api_id"  # From my.telegram.org
   API_HASH = "your_api_hash"  # From my.telegram.org
   BOT_TOKEN = "your_bot_token"  # From BotFather
   app = Client("StockBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
   data_file = "data.db"  # SQLite database file
   log_file = "bot.log"  # Log file
   logger = ...  # Configure logging (see main.py)
   ```

2. **Database**:
   The bot uses SQLite (`data.db`) to store user data, stocks, and tokens. The `db.py` module handles table creation and queries.

3. **Model Files**:
   Ensure `best_model.keras` and `stock_scaler.save` are in `IPSA_MODEL/price/`. These are required for price predictions.

---

## 🏃‍♂️ Running the Bot

1. **Start the Bot**:
   Run the main script:

   ```bash
   python main.py
   ```

2. **Interact with the Bot**:
   - Open Telegram and start a chat with your bot.
   - Use the `/start` command to initialize the bot.
   - If unregistered, you'll be prompted to register.
   - Registered users see the main menu; admins see the admin panel.

3. **Outputs**:
   - `client_data/`: Stores generated reports (`*.xlsx`) and forecast plots (`*.png`).
   - `logs/`: Contains bot logs (`bot.log`).
   - `data.db`: SQLite database with user and stock data.

---

## 📱 Bot Commands and Features

### Commands

| Command         | Description                          | Access       |
|-----------------|--------------------------------------|--------------|
| `/start`        | Initialize the bot and show menu     | All users    |
| `/send_tokens`  | Send tokens to a user                | Admins only  |

### Callback Queries

The bot uses inline keyboards for navigation. Key actions include:

- **User Actions**:
  - `register_user`: Register a new user.
  - `my_stocks`: View tracked stocks.
  - `add_stocks`/`remove_stocks`: Manage stock watchlist.
  - `get_price`: Request a stock price prediction (requires tokens).
  - `news`: Fetch news for a specified period (admin-only or in development).
  - `settings`: Access settings (e.g., set city, language).
  - `remove_account`: Delete user account.
  - `to_main`: Return to the main menu.

- **Admin Actions**:
  - `admin_panel`: Access the admin panel.
  - `users_menu`: List all users with details (ID, tokens, role, status).
  - `add_admin`/`rm_admin`: Add/remove admin role for a user.
  - `ban_user`/`unblock_user`: Ban/unban a user.

### State Management

The bot uses a `user_states` dictionary to track user input states (e.g., `adding`, `removing`, `price`, `news`). This ensures proper handling of text inputs based on the current context.

---

## 🧠 Core Components

### 1. StockPredictor (`price_core.py`)

- **Purpose**: Predicts stock prices for the next 60 days using a pre-trained TensorFlow model.
- **Key Methods**:
  - `predict_future(ticker)`: Generates 60-day price forecasts.
  - `analyze(ticker, threshold=0.05)`: Provides a forecast summary with expected price change.
  - `predict_plt(ticker, user_id)`: Creates a plot of historical and forecasted prices.
- **Dependencies**: TensorFlow, yfinance, Matplotlib, joblib.
- **Output**: Forecast message, price change percentage, and a plot (`client_data/forecast_{user_id}_{ticker}.png`).

### 2. NewsParser (`parsing.py`)

- **Purpose**: Scrapes news from Investing.com and filters articles relevant to user-tracked stocks.
- **Key Methods**:
  - `is_stocks_in_news(url, user_id, ...)`: Checks if tracked stocks are mentioned in an article.
  - `get_news_text(url)`: Extracts article text.
  - `parse_investing_news(url, period, user_id)`: Parses news articles within a specified period.
  - `start_parsing(period, user_id)`: Aggregates news from multiple sources.
  - `check_new_articles(user_id)`: Asynchronously checks for new articles every 2 minutes.
- **Dependencies**: BeautifulSoup, requests, user-agent.
- **Output**: Formatted news messages with title, summary, URL, and price influence prediction.

### 3. AdvicePredictor (`create_report.py`)

- **Purpose**: Provides buy/sell recommendations based on fundamental analysis.
- **Key Methods**:
  - `analyze_fundamentals(ticker)`: Scores stocks based on P/E ratio, ROE, debt-to-equity, revenue growth, beta, and risk metrics.
  - `analyze(ticker, forecast_growth)`: Generates a recommendation with risk assessment.
- **Dependencies**: yfinance, pandas.
- **Output**: Recommendation message (e.g., "STRONG BUY", "SELL") with risk details.

### 4. ReportTable (`create_report.py`)

- **Purpose**: Generates Excel reports with stock data.
- **Key Methods**:
  - `download_data(ticker)`: Fetches stock data via yfinance.
  - `save_report(data)`: Saves data to an Excel file.
- **Dependencies**: pandas, yfinance.
- **Output**: Excel file (`client_data/{ticker}_report.xlsx`).

### 5. Database (`db.py`)

- **Purpose**: Manages user data, stocks, tokens, and admin roles using SQLite.
- **Key Functions** (assumed based on usage):
  - `check_user_account(user_id)`: Checks if a user is registered.
  - `check_user_ban(username)`: Checks if a user is banned.
  - `is_admin(user_id)`: Verifies admin status.
  - `get_users_stocks(user_id)`: Retrieves a user's tracked stocks.
  - `update_tokens(user_id, amount)`: Updates user tokens.
  - `add_city_to_db(user_id, city)`: Stores user city for timezone handling.
- **Output**: SQLite database (`data.db`).

---

## 📈 Usage Example

1. **User Interaction**:
   - User sends `/start`.
   - If unregistered, they click "Register" (`register_user` callback).
   - Registered users see the main menu with options like "My Stocks", "Get Price", "News", and "Settings".
   - To add a stock, user selects "My Stocks" → "Add Stocks", enters a ticker (e.g., "AAPL"), and confirms.
   - To get a price prediction, user selects "Get Price", enters a ticker, and receives a forecast plot and report (if tokens are available).

2. **Admin Interaction**:
   - Admin sends `/start` and sees the admin panel.
   - They can list users (`users_menu`), ban/unban users (`ban_user`/`unblock_user`), or send tokens (`/send_tokens username tokens`).
   - Admin can add/remove other admins (`add_admin`/`rm_admin`).

3. **News Notifications**:
   - Users receive news updates for tracked stocks every 2 minutes (if relevant articles are found).
   - News includes a title, summary, URL, and predicted price influence.

---

## 🛡️ Security and Limitations

### Security Features
- **User Authentication**: Checks user registration and ban status before granting access.
- **Admin Controls**: Restricts sensitive actions (e.g., banning users, sending tokens) to admins.
- **Token System**: Limits API-heavy features (e.g., price predictions) to prevent abuse.
- **Logging**: Comprehensive logging for debugging and monitoring (`bot.log`).

### Limitations
- **API Limits**: yfinance and Investing.com have request limits, which may cause failures during high usage.
- **News Parsing**: Limited to Investing.com sources and may miss relevant articles from other platforms.
- **Model Accuracy**: Price predictions depend on the pre-trained model's quality and may not account for sudden market events.
- **Language Support**: Multilingual support is in development and not fully implemented.
- **Error Handling**: Some errors (e.g., network failures) may not be gracefully handled for users.

---

## 📝 Notes

- **Model Dependency**: Ensure `best_model.keras` and `stock_scaler.save` are available. Train the model using the provided stock prediction script if needed.
- **Timezone Handling**: News parsing uses user-specified cities for timezone conversion. Default timezone may cause inaccuracies if not set.
- **Token Management**: Admins must manually assign tokens using `/send_tokens`. Consider automating token allocation in future updates.
- **Scalability**: For large user bases, consider optimizing database queries and news parsing with caching or parallel processing.
- **Extensibility**: Add support for more news sources, technical indicators, or real-time market data feeds.

---

## 📚 References

- Pyrogram Documentation: [https://docs.pyrogram.org/](https://docs.pyrogram.org/)
- TensorFlow Documentation: [https://www.tensorflow.org/](https://www.tensorflow.org/)
- yfinance Documentation: [https://github.com/ranaroussi/yfinance](https://github.com/ranaroussi/yfinance)
- BeautifulSoup Documentation: [https://www.crummy.com/software/BeautifulSoup/](https://www.crummy.com/software/BeautifulSoup/)
- Investing.com: [https://www.investing.com/](https://www.investing.com/)

For support, open an issue on the project repository or contact the development team.

---

**🤖 Built with Pyrogram and TensorFlow**
