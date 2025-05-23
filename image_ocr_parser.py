import pytesseract
from PIL import Image
import re

def extract_betting_info_from_image(image_path):
    # 開啟圖片
    img = Image.open(image_path)

    # OCR 文字辨識（簡體 + 繁體）
    text = pytesseract.image_to_string(img, lang='chi_tra+eng')

    # 轉為一行一行
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    result = {
        "home_team": None,
        "away_team": None,
        "spread": None,
        "total_points": None,
        "raw_text": lines
    }

    # 嘗試抓出主客隊
    team_pattern = re.compile(r"(.+?)\s+vs\s+(.+)", re.IGNORECASE)
    for line in lines:
        match = team_pattern.search(line)
        if match:
            result["home_team"] = match.group(1).strip()
            result["away_team"] = match.group(2).strip()
            break

    # 嘗試抓讓分盤
    for line in lines:
        if "讓分" in line or "+" in line or "-" in line:
            spread_match = re.findall(r"[-+]?\d+\.\d+", line)
            if spread_match:
                result["spread"] = spread_match[0]
                break

    # 嘗試抓大小分
    for line in lines:
        if "大" in line or "小" in line or "over" in line.lower() or "under" in line.lower():
            total_match = re.findall(r"\d+\.\d+", line)
            if total_match:
                result["total_points"] = total_match[0]
                break

    return result