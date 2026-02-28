import os
import pickle
import re

import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_DIR = "/app/src/IPSA_MODEL/news"
MODEL_PATH = os.path.join(MODEL_DIR, "sentiment_model.keras")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.pickle")

try:
    model = load_model(MODEL_PATH)
    with open(TOKENIZER_PATH, "rb") as handle:
        tokenizer = pickle.load(handle)
except FileNotFoundError as e:
    raise FileNotFoundError(f"Could not load model or tokenizer: {e}")

MAX_LEN = 100


def clean_text(text):
    """Clean text by removing special characters, normalizing whitespace, and converting to lowercase."""
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def predict_price_influence(news_article):
    """Predict the price influence of a news article."""
    cleaned_article = clean_text(news_article)
    sequence = tokenizer.texts_to_sequences([cleaned_article])
    padded_sequence = pad_sequences(
        sequence, maxlen=MAX_LEN, padding="post", truncating="post"
    )

    prediction = model.predict(padded_sequence, verbose=0)
    probability = prediction[0][0]

    influence = "Positive Influence" if probability > 0.5 else "Negative Influence"
    return f"{influence} (Probability: {probability:.1f})"


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
