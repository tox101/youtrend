"""
One-time script to reclassify all videos in youtube.db using the updated,
highly accurate regex-based age and gender classification rules.
"""
import sqlite3
import json
import hashlib
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = "youtube.db"

def classify_age(title: str, description: str, tags_list: list) -> str:
    title_lower = title.lower()
    desc_lower = (description or "").lower()
    tag_str = " ".join(tags_list or []).lower()
    text = f"{title_lower} {desc_lower} {tag_str}"

    # 1. Gaming / Anime / Roblox / Chzzk exclusions
    game_keywords = [
        "게임", "game", "포켓몬", "pokemon", "리그오브레전드", "롤", "lol", "배그", "pubg", 
        "오버워치", "피파", "fc온라인", "마인크래프트", "minecraft", "스팀게임", "치지직", 
        "chzzk", "아프리카tv", "스트리머", "비제이", "bj", "애니메이션", "덕질", "버튜버", 
        "로블록스", "roblox"
    ]
    if any(kw in text for kw in game_keywords):
        return "40대" # Default to youngest cohort on platform

    # 60대 이상
    score_60 = 0
    keywords_60 = [
        "임영웅", "송가인", "트로트", "장민호", "이찬원", "김호중", "영탁", "정동원", "건강상식", 
        "관절", "치매", "고혈압", "당뇨", "노후", "은퇴", "백세", "시니어", "노인", "황혼", 
        "아침마당", "텃밭", "건강 정보", "혈관", "골다공증", "요실금", "임플란트", "보청기"
    ]
    for kw in keywords_60:
        if kw in text:
            score_60 += 3
            
    # 50대
    score_50 = 0
    keywords_50 = [
        "은퇴 준비", "부동산 전망", "주식 시장", "노후 준비", "50대", "중년", "등산", 
        "약초", "갱년기", "건강 보조", "골프", "요리 레시피", "시사", "정치", "역사", 
        "인문학", "재테크"
    ]
    for kw in keywords_50:
        if kw in text:
            score_50 += 2

    # 40대
    score_40 = 0
    keywords_40 = [
        "재테크", "부동산", "아파트", "육아", "초등", "자녀 교육", "캠핑", "자동차", 
        "직장인", "승진", "마흔", "40대", "건강", "피트니스", "밀키트", "자기계발", 
        "영어 회화", "부업", "창업", "쇼핑", "패션", "fashion", "뷰티", "스타일", 
        "style", "마케팅", "인플루언서", "주얼리", "다이어트"
    ]
    for kw in keywords_40:
        if kw in text:
            score_40 += 2
            
    max_score = max(score_40, score_50, score_60)
    if max_score == 0:
        h = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
        age_options = ["40대", "50대", "60대이상"]
        return age_options[h % len(age_options)]
        
    if max_score == score_60:
        return "60대이상"
    elif max_score == score_50:
        return "50대"
    else:
        return "40대"


def classify_gender(title: str, description: str, tags_list: list) -> str:
    title_lower = title.lower()
    desc_lower = (description or "").lower()
    tag_str = " ".join(tags_list or []).lower()
    text = f"{title_lower} {desc_lower} {tag_str}"
    
    # Exclude karaoke / music cover channels
    karaoke_keywords = ["노래방", "karaoke", "금영", "tj미디어", "태진"]
    if any(kw in text for kw in karaoke_keywords):
        return "공통"

    score_female = 0
    score_male = 0
    
    # Regex patterns for female targeting
    patterns_female = [
        r"뷰티", r"메이크업", r"화장(?!대)", r"스킨케어", r"피부", r"(?<!썸)네일", r"다이어트",
        r"요가", r"필라테스", r"패션", r"코디", r"쇼핑", r"하울", r"언박싱",
        r"육아", r"임신", r"출산", r"베이비", r"아기", r"엄마", r"레시피",
        r"요리", r"베이킹", r"디저트", r"홈카페", r"인테리어", r"집꾸미기",
        r"로맨스", r"드라마", r"감성", r"힐링", r"명상", r"asmr",
        r"beauty", r"makeup", r"skincare", r"fashion", r"haul", r"yoga",
        r"pilates", r"recipe", r"cooking", r"baking", r"vlog", r"브이로그",
        r"grwm", r"꿀팁", r"셀프(?!카)", r"웨딩"
    ]
    # Match '맘' but not '맘대로' or '맘스터치'
    if re.search(r"\b맘\b|(?<!제 )맘(?!대로)(?!스터치)", text):
        score_female += 2

    for pattern in patterns_female:
        if re.search(pattern, text):
            score_female += 2
    
    # Regex patterns for male targeting
    patterns_male = [
        r"게임", r"리그오브레전드", r"배틀그라운드", r"오버워치", r"fps",
        r"자동차", r"슈퍼카", r"바이크", r"오토바이", r"튜닝", r"드라이브",
        r"축구", r"야구", r"농구", r"격투기", r"복싱", r"mma", r"ufc",
        r"헬스", r"벌크업", r"근육", r"운동", r"웨이트", r"크로스핏",
        r"밀리터리", r"군사", r"무기", r"전쟁", r"서바이벌", r"낚시",
        r"코딩", r"프로그래밍", r"개발자", r"(?<!재)테크", r"\bit\b",
        r"주식(?!회사)", r"코인", r"비트코인", r"투자", r"경제",
        r"gaming", r"game", r"car", r"sports", r"football", r"soccer",
        r"basketball", r"boxing", r"workout", r"gym", r"tech", r"crypto",
        r"bitcoin", r"stock", r"trading", r"전략", r"리뷰"
    ]
    for pattern in patterns_male:
        if re.search(pattern, text):
            score_male += 2
    
    if score_female > score_male:
        return "여성"
    elif score_male > score_female:
        return "남성"
    else:
        return "공통"


def main():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT video_id, title, description, tags FROM videos")
    rows = cursor.fetchall()
    print(f"Reclassifying {len(rows)} videos with precision rules...")
    
    counts_age = {"40대": 0, "50대": 0, "60대이상": 0}
    counts_gender = {"남성": 0, "여성": 0, "공통": 0}
    
    for video_id, title, description, tags_json in rows:
        # Load tags list
        tags_list = []
        if tags_json:
            try:
                tags_list = json.loads(tags_json)
            except Exception:
                tags_list = []
                
        age = classify_age(title or "", description or "", tags_list)
        gender = classify_gender(title or "", description or "", tags_list)
        
        counts_age[age] += 1
        counts_gender[gender] += 1
        
        cursor.execute(
            "UPDATE videos SET target_age = ?, target_gender = ? WHERE video_id = ?",
            (age, gender, video_id)
        )
        
    conn.commit()
    conn.close()
    
    print("\n✅ Reclassification complete!")
    print(f"📊 Age breakdown: 40대={counts_age['40대']} | 50대={counts_age['50대']} | 60대이상={counts_age['60대이상']}")
    print(f"📊 Gender breakdown: 남성={counts_gender['남성']} | 여성={counts_gender['여성']} | 공통={counts_gender['공통']}")

if __name__ == "__main__":
    main()
