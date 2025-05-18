import pandas as pd
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import joblib

# 載入模擬資料
nba_path = "data/nba/nba_history_2023_2024.csv"
nba_df = pd.read_csv(nba_path)

# 建立目標欄位
nba_df["home_win"] = (nba_df["home_score"] > nba_df["away_score"]).astype(int)
nba_df["spread_result"] = ((nba_df["home_score"] - nba_df["away_score"]) > -2.5).astype(int)
nba_df["over_result"] = ((nba_df["home_score"] + nba_df["away_score"]) > 220).astype(int)

# 特徵欄位
X = nba_df[["home_score", "away_score"]]

# 模型與儲存資料夾
os.makedirs("models", exist_ok=True)

def train_and_save(X, y, filename):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)
    joblib.dump(model, f"models/{filename}")
    print(f"✅ 模型已儲存：models/{filename}")

# 訓練並儲存三個模型
train_and_save(X, nba_df["home_win"], "model_home_win.pkl")
train_and_save(X, nba_df["spread_result"], "model_spread.pkl")
train_and_save(X, nba_df["over_result"], "model_over.pkl")
