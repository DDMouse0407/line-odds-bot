
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

def train_models():
    nba_path = "data/nba/nba_history_2023_2024.csv"
    nba_df = pd.read_csv(nba_path)

    nba_df["home_win"] = (nba_df["home_score"] > nba_df["away_score"]).astype(int)
    nba_df["spread_result"] = ((nba_df["home_score"] - nba_df["away_score"]) > -2.5).astype(int)
    nba_df["over_result"] = ((nba_df["home_score"] + nba_df["away_score"]) > 220).astype(int)

    X = nba_df[["home_score", "away_score"]]

    def train(X, y):
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.3, random_state=42)
        model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
        model.fit(X_train, y_train)
        return model

    model_win = train(X, nba_df["home_win"])
    model_spread = train(X, nba_df["spread_result"])
    model_over = train(X, nba_df["over_result"])

    return model_win, model_spread, model_over
