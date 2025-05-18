import pandas as pd
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import joblib

# 資料路徑（已下載的真實數據）
nba_df = pd.read_csv("data/nba/nba_history_2023_2024.csv")

# 建立目標欄位
nba_df["home_win"] = (nba_df["home_score"] > nba_df["away_score"]).astype(int)
nba_df["spread_cover"] = ((nba_df["home_score"] - nba_df["away_score"]) > nba_df["spread"]).astype(int)
nba_df["total_over"] = ((nba_df["home_score"] + nba_df["away_score"]) > nba_df["over_under"]).astype(int)

# 特徵欄位
X = nba_df[["home_score", "away_score", "spread", "over_under"]]

# 建立資料夾
os.makedirs("models", exist_ok=True)

def train_and_save(y, filename):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)
    joblib.dump(model, f"models/{filename}")
    print(f"✅ 模型已儲存：models/{filename}")

# 訓練三個模型
train_and_save(nba_df["home_win"], "model_home_win.pkl")
train_and_save(nba_df["spread_cover"], "model_spread_cover.pkl")
train_and_save(nba_df["total_over"], "model_total_over.pkl")
