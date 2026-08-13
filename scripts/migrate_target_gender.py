"""
One-time migration: Add target_gender column to videos table in SQLite DB.
Then classify existing videos using keyword-based gender classification.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import sqlite3
import hashlib
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "youtube.db")

def classify_gender(title: str, description: str) -> str:
    """Classify target gender based on title + description keywords."""
    text = (title + " " + (description or "")).lower()
    
    score_female = 0
    score_male = 0
    
    # 여성 타겟 키워드
    keywords_female = [
        "뷰티", "메이크업", "화장", "스킨케어", "피부", "네일", "다이어트",
        "요가", "필라테스", "패션", "코디", "옷", "쇼핑", "하울", "언박싱",
        "육아", "임신", "출산", "베이비", "아기", "맘", "엄마", "레시피",
        "요리", "베이킹", "디저트", "홈카페", "인테리어", "집꾸미기",
        "로맨스", "드라마", "감성", "힐링", "명상", "ASMR", "asmr",
        "beauty", "makeup", "skincare", "fashion", "haul", "yoga",
        "pilates", "recipe", "cooking", "baking", "vlog", "브이로그",
        "grwm", "GRWM", "꿀팁", "셀프", "웨딩"
    ]
    for kw in keywords_female:
        if kw in text:
            score_female += 2
    
    # 남성 타겟 키워드
    keywords_male = [
        "게임", "리그오브레전드", "배틀그라운드", "오버워치", "fps",
        "자동차", "슈퍼카", "바이크", "오토바이", "튜닝", "드라이브",
        "축구", "야구", "농구", "격투기", "복싱", "mma", "ufc",
        "헬스", "벌크업", "근육", "운동", "웨이트", "크로스핏",
        "밀리터리", "군사", "무기", "전쟁", "서바이벌", "낚시",
        "코딩", "프로그래밍", "개발자", "테크", "IT", "기술",
        "주식", "코인", "비트코인", "투자", "부동산", "경제",
        "gaming", "game", "car", "sports", "football", "soccer",
        "basketball", "boxing", "workout", "gym", "tech", "crypto",
        "bitcoin", "stock", "trading", "전략", "리뷰"
    ]
    for kw in keywords_male:
        if kw in text:
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
    
    # Step 1: Add column if not exists
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN target_gender VARCHAR(20) DEFAULT '공통'")
        conn.commit()
        print("✅ Column 'target_gender' added successfully.")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("ℹ️  Column 'target_gender' already exists. Skipping ALTER.")
        else:
            print(f"⚠️  ALTER TABLE warning: {e}")
    
    # Step 2: Classify all existing videos
    cursor.execute("SELECT video_id, title, description FROM videos")
    rows = cursor.fetchall()
    print(f"\n📊 Classifying {len(rows)} videos by gender target...")
    
    counts = {"남성": 0, "여성": 0, "공통": 0}
    
    for video_id, title, description in rows:
        gender = classify_gender(title or "", description or "")
        counts[gender] += 1
        cursor.execute("UPDATE videos SET target_gender = ? WHERE video_id = ?", (gender, video_id))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Classification complete!")
    print(f"   남성 타겟: {counts['남성']}개")
    print(f"   여성 타겟: {counts['여성']}개")
    print(f"   공통: {counts['공통']}개")
    print(f"   총계: {sum(counts.values())}개")

if __name__ == "__main__":
    main()
