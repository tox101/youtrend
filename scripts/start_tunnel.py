import subprocess
import re
import time
import os
import sys
import threading
import json

# Windows 콘솔 인코딩 에러 방지 설정
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TUNNEL_URL_FILE = os.path.join(PROJECT_ROOT, "tunnel_url.json")
ENV_FILE = os.path.join(PROJECT_ROOT, "frontend", ".env.production")

# cloudflared.exe 경로 탐색
cf_exe = os.path.join(PROJECT_ROOT, "cloudflared.exe")
if not os.path.exists(cf_exe):
    cf_exe = "./cloudflared.exe"
if not os.path.exists(cf_exe):
    print(f"[Tunnel] FATAL: cloudflared.exe not found")
    sys.exit(1)


def save_tunnel_url(url: str):
    """현재 활성 터널 URL을 JSON 파일에 저장하여 백엔드가 읽을 수 있도록 함"""
    api_url = f"{url}/api"
    data = {
        "tunnel_url": url,
        "api_url": api_url,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }
    try:
        with open(TUNNEL_URL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Tunnel] tunnel_url.json updated: {api_url}")
    except Exception as e:
        print(f"[Tunnel] Failed to write tunnel_url.json: {e}")

    # .env.production도 동시 업데이트
    try:
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(f"NEXT_PUBLIC_API_URL={api_url}\n")
        print(f"[Tunnel] .env.production updated.")
    except Exception as e:
        print(f"[Tunnel] Failed to write .env.production: {e}")


def deploy_to_firebase():
    """Firebase 빌드 & 배포 (백그라운드 스레드)"""
    print("\n[Deploy] Starting Next.js build and Firebase deploy in background...")
    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    
    print("[Deploy] Step 1/2: Building Next.js application...")
    build_proc = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8"
    )
    if build_proc.returncode != 0:
        print(f"[Deploy] WARNING: Next.js build failed:\n{build_proc.stderr}")
        return
    print("[Deploy] Next.js build completed successfully.")
        
    print("[Deploy] Step 2/2: Uploading/Deploying to Firebase Hosting...")
    deploy_proc = subprocess.run(
        ["firebase", "deploy", "--only", "hosting"],
        cwd=PROJECT_ROOT, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8"
    )
    if deploy_proc.returncode == 0:
        print("\n=========================================================================")
        print("[Deploy] SUCCESS: Dashboard deployed to Firebase with the latest API URL!")
        print("=========================================================================\n")
    else:
        print(f"[Deploy] WARNING: Firebase deployment failed:\n{deploy_proc.stderr}")


def start_tunnel() -> tuple:
    """cloudflared 프로세스를 시작하고 터널 URL을 감지. (proc, url) 반환"""
    print("[Tunnel] Starting cloudflared process...")
    try:
        proc = subprocess.Popen(
            [cf_exe, "tunnel", "--url", "http://localhost:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            bufsize=1
        )
    except Exception as e:
        print(f"[Tunnel] cloudflared.exe start failed: {e}")
        return None, None

    url_pattern = re.compile(r'https://[a-z0-9\-]+\.trycloudflare\.com')
    tunnel_url = None
    start_time = time.time()

    while time.time() - start_time < 30:
        if proc.poll() is not None:
            print("[Tunnel] WARNING: cloudflared process terminated early.")
            break
        line = proc.stderr.readline()
        if line:
            clean_line = line.strip()
            print(f"[cfLog] {clean_line}")
            match = url_pattern.search(clean_line)
            if match:
                tunnel_url = match.group(0)
                break
        else:
            time.sleep(0.1)

    return proc, tunnel_url


def run_forever():
    """
    핵심 무한 루프: cloudflared 프로세스를 감시하고,
    프로세스가 죽거나 터널이 끊기면 자동으로 재시작하고 새 URL을 감지합니다.
    """
    restart_count = 0
    MAX_BACKOFF = 30  # 최대 재시작 대기 시간(초)

    while True:
        proc, tunnel_url = start_tunnel()
        
        if tunnel_url:
            restart_count = 0  # 성공하면 백오프 리셋
            save_tunnel_url(tunnel_url)
            print(f"\n[Tunnel] ✅ Active URL: {tunnel_url}/api")
            print("[Tunnel] Tunnel is running. Monitoring for disconnection...\n")
            
            # 최초 1회 또는 URL 변경 시 Firebase 배포
            threading.Thread(target=deploy_to_firebase, daemon=True).start()
        else:
            print("[Tunnel] ⚠️ URL detection failed. Will retry...")

        # 프로세스 생존 감시 루프
        if proc and proc.poll() is None:
            try:
                while proc.poll() is None:
                    line = proc.stderr.readline()
                    if line:
                        clean_line = line.strip()
                        # 치명적 에러 감지 (터널 연결 끊김)
                        if any(kw in clean_line.lower() for kw in [
                            "connection timed out", 
                            "connection reset",
                            "quic handshake",
                            "failed to connect",
                            "context deadline exceeded",
                            "tunnel shut down"
                        ]):
                            print(f"[Tunnel] ⚠️ Connection issue detected: {clean_line}")
                        print(f"[cfLog] {clean_line}")
                    else:
                        time.sleep(0.2)
            except KeyboardInterrupt:
                print("\n[Tunnel] Ctrl+C received. Shutting down...")
                proc.terminate()
                proc.wait(timeout=5)
                return
        
        # 프로세스 종료됨 → 재시작 준비
        restart_count += 1
        backoff = min(5 * restart_count, MAX_BACKOFF)
        print(f"\n[Tunnel] 🔄 cloudflared process exited. Restarting in {backoff}s... (attempt #{restart_count})")
        
        # 죽은 프로세스 정리
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                pass
        
        time.sleep(backoff)


if __name__ == "__main__":
    print("=" * 60)
    print("[Tunnel] Cloudflare Quick Tunnel — Auto-Restart Guardian")
    print("=" * 60)
    run_forever()
