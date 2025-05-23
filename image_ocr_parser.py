 # image_handler.py
import pytesseract
from PIL import Image
import io
import re

def extract_info_from_image(image_bytes):
    # 開啟圖片
    image = Image.open(io.BytesIO(image_bytes))
    
    # OCR 文字辨識
    text = pytesseract.image_to_string(image, lang="eng+chi_tra")
    
    # 嘗試擷取資訊（你可以再調整這些規則）
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip() != ""]

    info = {
        "home_team": None,
        "away_team": None,
        "spread": None,
        "total": None
    }

    for line in lines:
        if "vs" in line:
            teams = line.split("vs")
            if len(teams) == 2:
                info["home_team"] = teams[0].strip()
                info["away_team"] = teams[1].strip()
        if "讓" in line or "+" in line or "-" in line:
            spread_match = re.search(r'[-+]?\d+\.\d+', line)
            if spread_match:
                info["spread"] = spread_match.group()
        if "大小" in line or "over" in line.lower() or "under" in line.lower():
            total_match = re.search(r'\d{3}\.?\d*', line)
            if total_match:
                info["total"] = total_match.group()

    return text, info