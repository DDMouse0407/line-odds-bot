
# modules/odds_analyzer.py

def analyze_odds_shift(game_data):
    """
    模擬分析賠率水位異常與誘導盤的邏輯。
    game_data = {
        "home_team": "湖人",
        "away_team": "勇士",
        "open_odds": -2.5,
        "current_odds": -1.0,
        "home_win_rate": 70.2
    }
    """
    messages = []
    shift = game_data["current_odds"] - game_data["open_odds"]

    if abs(shift) >= 1.0:
        messages.append("🔺 賠率大幅變動（異常水位）")

    if game_data["home_win_rate"] > 65 and shift > 0:
        messages.append("⚠️ 熱門隊賠率升高（疑似誘導盤）")

    return " / ".join(messages) if messages else "✅ 賠率無異常"
