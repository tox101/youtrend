"use client";

import { useEffect, useRef } from "react";
import { getApiBaseUrl, IS_CLOUD_DEPLOY } from "@/lib/api";

/**
 * 전역 Keep-Alive 핑 + 터널 URL 자동 복구 컴포넌트
 * 
 * 60초마다 백엔드에 헬스체크 요청을 보내 서버를 활성 상태로 유지합니다.
 * - 로컬 개발: Cloudflare 터널의 유휴 타임아웃을 방지하고, 핑 실패 시 localhost:8000을 통해
 *   최신 터널 URL을 자동으로 발견해 localStorage를 갱신합니다.
 * - 클라우드 배포(IS_CLOUD_DEPLOY): Render URL에 60초 주기로 핑을 보내 Render 무료 플랜의
 *   idle sleep을 방지합니다 (localhost/터널 복구는 수행하지 않음).
 * 
 * 이 컴포넌트는 UI를 렌더링하지 않으며, layout.tsx에 마운트되어
 * 앱 전체 수명 동안 백그라운드에서 작동합니다.
 */
const KEEP_ALIVE_INTERVAL = 60_000; // 60초 (기존 2분 → 1분으로 단축)
const RECOVERY_INTERVAL = 10_000;   // 복구 모드: 10초마다 재시도

export default function KeepAlive() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isRecoveryMode = useRef(false);

  useEffect(() => {
    const ping = async () => {
      const baseUrl = getApiBaseUrl();
      let success = false;

      // 1차: 현재 저장된 URL로 핑
      try {
        const res = await fetch(`${baseUrl}/admin/status`, {
          cache: "no-store",
          signal: AbortSignal.timeout(5000),
        });
        const ct = res.headers.get("content-type") || "";
        if (res.ok && ct.includes("application/json")) {
          success = true;
        }
      } catch {
        // 실패
      }

      // 2차: 실패 시 localhost 직접 핑 + 터널 URL 자동 복구 (로컬 개발 전용)
      if (!success && !IS_CLOUD_DEPLOY) {
        try {
          const res = await fetch("http://localhost:8000/api/admin/status", {
            cache: "no-store",
            signal: AbortSignal.timeout(3000),
          });
          const ct = res.headers.get("content-type") || "";
          if (res.ok && ct.includes("application/json")) {
            // localhost는 살아있음 → 터널 URL만 죽은 상태
            // 최신 터널 URL 자동 발견
            try {
              const tunnelRes = await fetch("http://localhost:8000/api/admin/tunnel-url", {
                cache: "no-store",
                signal: AbortSignal.timeout(3000),
              });
              if (tunnelRes.ok) {
                const data = await tunnelRes.json();
                if (data.api_url && data.api_url !== baseUrl) {
                  // 새 URL 발견! localStorage 자동 갱신
                  window.localStorage.setItem("NEXT_PUBLIC_API_URL", data.api_url);
                  console.log(`[KeepAlive] 터널 URL 자동 갱신: ${data.api_url}`);
                  success = true;
                }
              }
            } catch {
              // tunnel-url 엔드포인트 실패
            }
          }
        } catch {
          // localhost도 연결 불가 — 백엔드 서버 자체가 꺼진 상태
        }
      }

      // 복구 모드 전환: 실패 시 빠른 주기로, 성공 시 정상 주기로 복귀
      if (!success && !isRecoveryMode.current) {
        isRecoveryMode.current = true;
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(ping, RECOVERY_INTERVAL);
        console.log("[KeepAlive] 복구 모드 진입 (10초 주기)");
      } else if (success && isRecoveryMode.current) {
        isRecoveryMode.current = false;
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(ping, KEEP_ALIVE_INTERVAL);
        console.log("[KeepAlive] 정상 모드 복귀 (60초 주기)");
      }
    };

    // 최초 15초 후 첫 핑 (초기 로드 부하 방지)
    const initialTimeout = setTimeout(() => {
      ping();
      intervalRef.current = setInterval(ping, KEEP_ALIVE_INTERVAL);
    }, 15_000);

    return () => {
      clearTimeout(initialTimeout);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return null; // UI 없음 — 순수 백그라운드 작동
}
