import pandas as pd
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import joblib

# 模擬真實歷史數據（請用實際資料取代）
data = {
    "home_score": [110, 98, 120, 115, 101],
    "away_score": [105, 102, 115, 117, 95],
    "spread": [-2.5, -1.5, -4.0, -3.5, -2.0],
    "over_under": [220.5, 215.0, 225.0, 218.5, 212.0],
}
nba_df = pd.DataFrame(data)

# 建立標籤欄位
nba_df["home_win"] = (nba_df["home_score"] > nba_df["away_score"]).astype(int)
nba_df["spread_cover"] = ((nba_df["home_score"] - nba_df["away_score"]) > nba_df["spread"]).astype(int)
nba_df["total_over"] = ((nba_df["home_score"] + nba_df["away_score"]) > nba_df["over_under"]).astype(int)

# 特徵
X = nba_df[["home_score", "away_score", "spread", "over_under"]]

# 確保資料夾存在
os.makedirs("/mnt/data/models", exist_ok=True)

# 訓練模型並儲存
def train_and_save(y, filename):
    y = y.astype(int)  # 確保標籤為整數
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)
    joblib.dump(model, f"/mnt/data/models/{filename}")

train_and_save(nba_df["home_win"], "model_home_win.pkl")
train_and_save(nba_df["spread_cover"], "model_spread_cover.pkl")
train_and_save(nba_df["total_over"], "model_total_over.pkl")
