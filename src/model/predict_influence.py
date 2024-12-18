# predict.py

import os
import pickle
import re

import numpy as np
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences

# Загрузка модели и токенизатора
model = load_model(
    os.path.join(os.getcwd(), "IPSA_MODEL", "news", "sentiment_model.h5")
)
with open(
    os.path.join(os.getcwd(), "IPSA_MODEL", "news", "tokenizer.pickle"), "rb"
) as handle:
    tokenizer = pickle.load(handle)


# Очистка текста
def clean_text(text):
    text = re.sub(r"[^a-zA-Z\s]", "", text)  # Удаляем все символы кроме букв
    return text.lower()


def predict_price_influence(news_article):
    cleaned_article = clean_text(news_article)
    sequence = tokenizer.texts_to_sequences([cleaned_article])
    padded_sequence = pad_sequences(sequence, maxlen=100)

    prediction = model.predict(padded_sequence)
    return "Positive Influence" if prediction[0][0] > 0.5 else "Negative Influence"


# Пример использования функции предсказания
if __name__ == "__main__":
    new_article = """
    (Reuters) -The U.S. Treasury has informed Japan's Nippon Steel that the panel reviewing its proposed $14.9 billion purchase of U.S. Steel has not yet come to an agreement on how to address security concerns, the Financial Times reported on Sunday.
    Treasury, which leads the Committee on Foreign Investment in the U.S. (CFIUS), wrote to both companies on Saturday saying the nine agencies on the panel were struggling to reach a consensus ahead of the deadline to submit a recommendation to President Joe Biden, the report added, citing several sources familiar with the talks.
    CFIUS, a powerful committee charged with reviewing foreign investments in U.S. firms for national security risks, has until Dec. 22 to make a decision on whether to approve, block or extend the timeline for the deal's review, Reuters has reported.
    U.S. Steel and CFIUS did not immediately respond to Reuters' requests for comments on the Financial Times report, while Nippon Steel declined to comment.
    The acquisition has faced opposition within the U.S. since it was announced last year, with both Biden and his incoming successor Donald Trump publicly indicating their intentions to block the purchase.
    CFIUS told the two companies in September that the deal would create national security risks because it could hurt the supply of steel needed for critical transportation, construction and agriculture projects, according to a letter seen by Reuters.

    """
    result = predict_price_influence(new_article)
    print(f"Predicted Influence: {result}")
