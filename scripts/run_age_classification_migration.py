import sqlite3
import os
import hashlib

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "youtube.db"))
print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def classify_age(title: str, description: str) -> str:
    title_lower = title.lower()
    desc_lower = (description or "").lower()
    text = title_lower + " " + desc_lower
    
    # 60대 이상
    score_60 = 0
    keywords_60 = ["임영웅", "송가인", "트로트", "장민호", "이찬원", "김호중", "영탁", "정동원", "건강상식", "관절", "치매", "고혈압", "당뇨", "노후", "은퇴", "백세", "시니어", "노인", "황혼", "아침마당", "텃밭", "건강 정보", "혈관", "골다공증", "요실금", "임플란트", "보청기"]
    for kw in keywords_60:
        if kw in text:
            score_60 += 3
            
    # 50대
    score_50 = 0
    keywords_50 = ["은퇴 준비", "부동산 전망", "주식 시장", "노후 준비", "50대", "중년", "등산", "약초", "갱년기", "건강 보조", "골프", "요리 레시피", "트로트", "시사", "정치", "역사", "인문학", "재테크", "갱년기", "당뇨", "고혈압"]
    for kw in keywords_50:
        if kw in text:
            score_50 += 2

    # 40대
    score_40 = 0
    keywords_40 = ["재테크", "부동산", "아파트", "육아", "초등", "자녀 교육", "캠핑", "자동차", "직장인", "승진", "마흔", "40대", "건강", "피트니스", "밀키트", "인문학", "자기계발", "영어 회화", "부업", "창업"]
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

try:
    cursor.execute("SELECT video_id, title, description FROM videos")
    videos = cursor.fetchall()
    print(f"Total videos to classify: {len(videos)}")
    
    updated_count = 0
    for video_id, title, description in videos:
        age_group = classify_age(title, description)
        cursor.execute("UPDATE videos SET target_age = ? WHERE video_id = ?", (age_group, video_id))
        updated_count += 1
        
    conn.commit()
    print(f"Successfully classified and updated {updated_count} videos in database.")
    
    # Print distinct count after update
    cursor.execute("SELECT target_age, COUNT(*) FROM videos GROUP BY target_age")
    rows = cursor.fetchall()
    print("New distribution:")
    for row in rows:
        print(f"  {row[0]}: {row[1]}")
        
except Exception as e:
    print("Error during migration:", e)
finally:
    conn.close()
