import sys
import os

# 엔진 경로 설정 (실제 UE 환경에서 실행 시 필요)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from placement.placement_engine import PlacementEngine

def main():
    # 실제 사용 시에는 엔진 내 Python Terminal이나 명령줄로 호출
    engine = PlacementEngine()
    rules_path = os.path.abspath("scripts/placement/sample_rules.json")
    
    print(f"Attempting placement with: {rules_path}")
    success = engine.execute_placement(rules_path)
    
    if success:
        print("Result: SUCCESS")
    else:
        print("Result: FAILED (Rolled back)")

if __name__ == "__main__":
    main()