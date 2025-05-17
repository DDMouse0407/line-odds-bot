# 模擬 AI 預測與誘導盤邏輯（日後可接 XGBoost）
import random

def analyze_and_predict(match, team, odds):
    reasons = [
        "主隊勝率高", "客隊主力球員受傷", "近期連勝", "讓分盤誘導明顯", "AI 模型預測勝率高", "對戰歷史佔優"
    ]
    ai_confidence = round(random.uniform(60, 75), 1)
    reason_sample = " + ".join(random.sample(reasons, 2))
    return f"{reason_sample} + AI 預測勝率 {ai_confidence}%"
