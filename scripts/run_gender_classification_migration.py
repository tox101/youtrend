import sqlite3
import os
import hashlib

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "youtube.db"))
print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def classify_gender(title: str, description: str) -> str:
    title_lower = title.lower()
    desc_lower = (description or "").lower()
    text = title_lower + " " + desc_lower
    
    # 여성 타겟 키워드
    female_keywords = ["메이크업", "화장품", "뷰티", "다이어트", "레시피", "요리", "네일", "룩북", "데일리룩", "스킨케어", "브이로그", "육아", "살림", "네일아트", "쇼핑하울", "악세사리", "임영웅", "트로트", "송가인"]
    female_score = sum(3 for kw in female_keywords if kw in text)
    
    # 남성 타겟 키워드
    male_keywords = ["게임", "리그오브레전드", "롤", "축구", "야구", "피파", "군대", "밀리터리", "it테크", "전자기기", "조립 pc", "헬스", "피트니스", "낚시", "캠핑", "자동차", "바이크", "정비"]
    male_score = sum(3 for kw in male_keywords if kw in text)
    
    if female_score == 0 and male_score == 0:
        h = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
        options = ["여성", "남성", "공통"]
        return options[h % len(options)]
        
    if female_score > male_score:
        return "여성"
    elif male_score > female_score:
        return "남성"
    else:
        return "공통"

try:
    cursor.execute("SELECT video_id, title, description FROM videos")
    videos = cursor.fetchall()
    print(f"Total videos to classify: {len(videos)}")
    
    updated_count = 0
    for video_id, title, description in videos:
        gender_group = classify_gender(title, description)
        cursor.execute("UPDATE videos SET target_gender = ? WHERE video_id = ?", (gender_group, video_id))
        updated_count += 1
        
    conn.commit()
    print(f"Successfully classified and updated {updated_count} videos in database.")
    
    # Print distinct count after update
    cursor.execute("SELECT target_gender, COUNT(*) FROM videos GROUP BY target_gender")
    rows = cursor.fetchall()
    print("New distribution:")
    for row in rows:
        print(f"  {row[0]}: {row[1]}")
        
except Exception as e:
    print("Error during migration:", e)
finally:
    conn.close()
