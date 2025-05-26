import pandas as pd
import yfinance as yf

import pandas as pd
import yfinance as yf

def create_dataset(tickers, file_path):
    combined_data = pd.DataFrame()

    for ticker in tickers:
        temp = yf.Ticker(ticker).history('100y')
        temp['Ticker'] = ticker
        combined_data = pd.concat([combined_data, temp])

    combined_data.reset_index(inplace=True)
    combined_data.fillna(0, inplace=True)

    combined_data.to_csv(file_path, index=False)

    print(f'Downloaded data for {len(tickers)} tickers and saved to {file_path}')

tickers = [
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "AMZN",  # Amazon.com, Inc.
    "GOOGL",  # Alphabet Inc. (Class A)
    "FB",  # Meta Platforms, Inc. (Facebook)
    "TSLA",  # Tesla, Inc.
    "NVDA",  # NVIDIA Corporation
    "PYPL",  # PayPal Holdings, Inc.
    "NFLX",  # Netflix, Inc.
    "INTC",  # Intel Corporation
    "CSCO",  # Cisco Systems, Inc.
    "CMCSA",  # Comcast Corporation
    "PEP",  # PepsiCo, Inc.
    "AVGO",  # Broadcom Inc.
    "TXN",  # Texas Instruments Incorporated
    "QCOM",  # Qualcomm Incorporated
    "AMGN",  # Amgen Inc.
    "SBUX",  # Starbucks Corporation
    "ADBE",  # Adobe Inc.
    "INTU",  # Intuit Inc.
    "MDLZ",  # Mondelez International, Inc.
    "ISRG",  # Intuitive Surgical, Inc.
    "CHKP",  # Check Point Software Technologies Ltd.
    "GILD",  # Gilead Sciences, Inc.
    "ATVI",  # Activision Blizzard, Inc.
    "BKNG",  # Booking Holdings Inc.
    "LRCX",  # Lam Research Corporation
    "NOW",  # ServiceNow, Inc.
    "FISV",  # Fiserv, Inc.
    "SPLK",  # Splunk Inc.
    "ZM",  # Zoom Video Communications, Inc.
    "DOCU",  # DocuSign, Inc.
    "SNPS",  # Synopsys, Inc.
    "MRNA",  # Moderna, Inc.
    "BIIB",  # Biogen Inc.
    "ILMN",  # Illumina, Inc.
    "MELI",  # MercadoLibre, Inc.
    "COST",  # Costco Wholesale Corporation
    "JD",  # JD.com, Inc.
    "PDD",  # Pinduoduo Inc.
    "BIDU",  # Baidu, Inc.
    "NTES",  # NetEase, Inc.
    "NTGR",  # NETGEAR, Inc.
    "ASML",  # ASML Holding N.V.
    "MOEX Index",  # Индекс Московской биржи
    "RTS Index",  # Индекс РТС
    "MICEX10 Index",  # Индекс ММВБ-10
]

file_path = "combined_stock_data.csv"
dataset = create_dataset(tickers, file_path)

print(f"Dataset created and saved as {file_path}")
