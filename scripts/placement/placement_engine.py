import unreal
import json
import os

class PlacementEngine:
    """
    AutoScene-UE의 핵심 배치 엔진.
    JSON 규칙을 읽어 에셋을 레벨에 배치하며, 실패 시 롤백 기능을 제공합니다.
    """
    def __init__(self):
        self.placed_actors = []  # 세션 중 배치된 액터 추적 (롤백용)
        self.is_rolling_back = False

    def load_rules(self, json_path):
        """JSON 규칙 파일을 로드합니다."""
        if not os.path.exists(json_path):
            unreal.log_error(f"❌ [PlacementEngine] 규칙 파일을 찾을 수 없습니다: {json_path}")
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            unreal.log_error(f"❌ [PlacementEngine] JSON 파싱 에러: {str(e)}")
            return None

    def apply_transform(self, actor, transform_data):
        """액터에 위치, 회전, 스케일을 적용합니다."""
        try:
            loc = transform_data.get('location', [0, 0, 0])
            rot = transform_data.get('rotation', [0, 0, 0])
            scale = transform_data.get('scale', [1, 1, 1])

            actor.set_actor_location(unreal.Vector(loc[0], loc[1], loc[2]), False, False)
            actor.set_actor_rotation(unreal.Rotator(rot[0], rot[1], rot[2]), False)
            actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]), False)
        except Exception as e:
            raise RuntimeError(f"Transform 적용 실패: {str(e)}")

    def rollback(self):
        """배치 중 오류 발생 시, 현재 세션에서 배치된 모든 액터를 삭제합니다."""
        unreal.log_warning("⚠️ [PlacementEngine] 에러 감지! 롤백을 시작합니다...")
        self.is_rolling_action = True
        for actor in self.placed_actors:
            if actor and not actor.is_folderized(): # 유효성 검사
                unreal.EditorLevelLibrary.destroy_actor(actor)
        self.placed_actors = []
        unreal.log("✅ [PlacementEngine] 롤백 완료. 레벨 상태를 복구했습니다.")

    def execute_placement(self, json_path):
        """배치 프로세스 실행 메인 루프."""
        rules = self.load_rules(json_path)
        if not rules:
            return False

        unreal.log("🚀 [PlacementEngine] 배치 작업을 시작합니다.")
        
        try:
            for entry in rules.get('placements', []):
                asset_path = entry.get('asset_path')
                transform_info = entry.param if 'param' in entry else entry # 스키마 대응
                
                # 1. 에셋 로드 확인
                asset = unreal.EditorAssetLibrary.load_asset(asset_path)
                if not asset:
                    raise RuntimeError(f"에셋을 찾을 수 없음: {asset_path}")

                # 2. 액터 스폰 (기존 에셋 기반)
                # Note: 실제 환경에서는 Actor 클래스나 Blueprint를 지정해야 함
                new_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                    unreal.Actor, 
                    unreal.Vector(0,0,0), 
                    unreal.Rotator(0,0,0)
                )
                
                if not new_actor:
                    raise RuntimeError(f"액터 스폰 실패: {asset_path}")

                # 3. 트랜스폼 적용
                self.apply_transform(new_actor, entry['transform'])
                
                # 4. 추적 리스트에 추가 (롤백용)
                self.placed_action_track(new_actor)
                
                unreal.log(f"✅ 배치 완료: {asset_path}")

            unreal.log("✨ [PlacementEngine] 모든 배치가 성공적으로 완료되었습니다.")
            return True

        except Exception as e:
            unreal.log_error(f"❌ [PlacementEngine] 작업 중단됨: {str(e)}")
            self.rollback()
            return False

    def placed_action_track(self, actor):
        """배치된 액터를 추적 리스트에 기록합니다."""
        self.placed_actors.append(actor)