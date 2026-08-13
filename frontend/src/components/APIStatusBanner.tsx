"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { WifiOff, Wifi, Save, RefreshCw, CheckCircle } from "lucide-react";

// ─── 현재 API URL을 런타임에 읽어오는 헬퍼 ────────────────────────────────
function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const saved = window.localStorage.getItem("NEXT_PUBLIC_API_URL");
    if (saved) return saved;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
}

// 연결 확인 주기 (ms)
const CHECK_INTERVAL_OFFLINE = 5_000;   // 끊겼을 때: 5초마다 재시도 (빠른 복구)
const CHECK_INTERVAL_ONLINE  = 30_000;  // 연결됐을 때: 30초마다 헬스체크 (조기 감지)

export default function APIStatusBanner() {
  const [status, setStatus] = useState<"online" | "offline" | "checking">("checking");
  const [isChecking, setIsChecking] = useState(false);
  const [apiUrl, setApiUrl] = useState("");
  const [inputUrl, setInputUrl] = useState("");
  const [justRecovered, setJustRecovered] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // ── 연결 확인 함수 ────────────────────────────────────────────────────────
  const checkConnection = useCallback(async (silent = false) => {
    if (!silent) setStatus("checking");
    setIsChecking(true);

    // 이전 요청 취소
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const urlsToTry = [];
    urlsToTry.push(getApiBaseUrl());
    
    if (process.env.NEXT_PUBLIC_API_URL && urlsToTry.indexOf(process.env.NEXT_PUBLIC_API_URL) === -1) {
      urlsToTry.push(process.env.NEXT_PUBLIC_API_URL);
    }
    
    const localhostUrl = "http://localhost:8000/api";
    if (urlsToTry.indexOf(localhostUrl) === -1) {
      urlsToTry.push(localhostUrl);
    }

    let successUrl = null;

    // Phase 1: 기존 URL 목록으로 시도
    for (const baseUrl of urlsToTry) {
      try {
        const itemController = new AbortController();
        const id = setTimeout(() => itemController.abort(), 5000);
        const res = await fetch(`${baseUrl}/admin/status`, {
          signal: itemController.signal,
          cache: "no-store",
        });
        clearTimeout(id);

        const contentType = res.headers.get("content-type") || "";
        if (res.ok && contentType.includes("application/json")) {
          successUrl = baseUrl;
          break;
        }
      } catch {
        // 다음 URL 탐색
      }
    }

    // Phase 2: 모든 URL 실패 → localhost를 통해 최신 터널 URL 자동 발견
    if (!successUrl) {
      try {
        const tunnelController = new AbortController();
        const tid = setTimeout(() => tunnelController.abort(), 3000);
        const tunnelRes = await fetch("http://localhost:8000/api/admin/tunnel-url", {
          signal: tunnelController.signal,
          cache: "no-store",
        });
        clearTimeout(tid);

        if (tunnelRes.ok) {
          const tunnelData = await tunnelRes.json();
          if (tunnelData.api_url && urlsToTry.indexOf(tunnelData.api_url) === -1) {
            // 새로 발견된 터널 URL로 헬스체크 시도
            try {
              const newController = new AbortController();
              const nid = setTimeout(() => newController.abort(), 5000);
              const newRes = await fetch(`${tunnelData.api_url}/admin/status`, {
                signal: newController.signal,
                cache: "no-store",
              });
              clearTimeout(nid);
              const ct = newRes.headers.get("content-type") || "";
              if (newRes.ok && ct.includes("application/json")) {
                successUrl = tunnelData.api_url;
              }
            } catch {
              // 새 터널 URL도 실패
            }
          }
        }
      } catch {
        // localhost도 연결 불가 — 서버 자체가 꺼진 상태
      }
    }

    if (successUrl) {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("NEXT_PUBLIC_API_URL", successUrl);
      }
      setApiUrl(successUrl);
      setInputUrl(successUrl);
      
      setStatus(prev => {
        if (prev === "offline") {
          setJustRecovered(true);
          setTimeout(() => setJustRecovered(false), 3000);
        }
        return "online";
      });
      setIsChecking(false);
      scheduleNext(CHECK_INTERVAL_ONLINE);
    } else {
      setStatus("offline");
      setIsChecking(false);
      scheduleNext(CHECK_INTERVAL_OFFLINE);
    }
  }, []);

  // ── 다음 체크 스케줄 ──────────────────────────────────────────────────────
  const scheduleNext = (interval: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => checkConnection(true), interval);
  };

  // ── 초기 마운트 ───────────────────────────────────────────────────────────
  useEffect(() => {
    const url = getApiBaseUrl();
    setApiUrl(url);
    setInputUrl(url);
    checkConnection();

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [checkConnection]);

  // ── URL 저장 및 즉시 재연결 ───────────────────────────────────────────────
  const handleSave = () => {
    if (typeof window === "undefined") return;
    let url = inputUrl.trim();
    if (!url) return;
    // /api 미포함 시 자동 보정
    if (!url.includes("/api")) url = url.replace(/\/$/, "") + "/api";
    localStorage.setItem("NEXT_PUBLIC_API_URL", url);
    setApiUrl(url);
    // 페이지 리로드 없이 즉시 재연결 시도
    window.location.reload();
  };

  // ── 렌더링 ────────────────────────────────────────────────────────────────

  // 연결 복구 직후 — 초록 배지만 잠깐 표시
  if (justRecovered) {
    return (
      <div className="mb-4 p-3 rounded-xl border border-emerald-500/30 flex items-center gap-3 animate-fade-in"
        style={{ background: "rgba(16,185,129,0.08)" }}>
        <CheckCircle size={16} className="text-emerald-400 flex-shrink-0" />
        <p className="text-xs font-semibold text-emerald-400">API 서버 연결 복구됨 ✅</p>
      </div>
    );
  }

  // 연결 정상 — 배너 숨김
  if (status === "online") return null;

  // 최초 확인 중 — 조용히 숨김 (깜빡임 방지)
  if (status === "checking") return null;

  // 연결 끊김 배너
  return (
    <div
      className="mb-6 p-4 rounded-xl border border-red-500/30 backdrop-blur-md"
      style={{ background: "rgba(239,68,68,0.08)" }}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* 상태 설명 */}
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-red-500/20 text-red-400 flex-shrink-0 mt-0.5">
            <WifiOff size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-red-400">백엔드 API 서버 연결 끊김</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              로컬 서버가 꺼져 있거나 Cloudflare 터널 URL이 만료되었습니다.
              <br />
              <span className="text-gray-500">
                새 URL을 입력하거나, <code className="text-indigo-400">start.bat</code>를 실행하면 자동으로 갱신됩니다.
                {" "}5초마다 자동으로 재연결을 시도합니다.
              </span>
            </p>
          </div>
        </div>

        {/* 입력 + 버튼 */}
        <div className="flex items-center gap-2 w-full md:w-auto flex-shrink-0">
          <input
            id="api-url-input"
            type="text"
            placeholder="https://xxxx.trycloudflare.com/api"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSave()}
            className="flex-1 md:w-80 px-3 py-1.5 rounded-lg border text-xs text-white focus:outline-none focus:border-indigo-500"
            style={{
              background: "var(--bg-secondary)",
              borderColor: "rgba(239,68,68,0.35)",
            }}
          />
          <button
            id="api-url-save-btn"
            onClick={handleSave}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 transition-all flex-shrink-0"
          >
            <Save size={13} />
            적용
          </button>
          <button
            id="api-reconnect-btn"
            onClick={() => checkConnection()}
            disabled={isChecking}
            className="p-1.5 rounded-lg border text-gray-400 hover:text-white transition disabled:opacity-40 flex-shrink-0"
            style={{ borderColor: "var(--border-color)", background: "var(--bg-secondary)" }}
            title="지금 재연결 시도"
          >
            <RefreshCw size={14} className={isChecking ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* 자동 재시도 인디케이터 */}
      <div className="mt-3 flex items-center gap-2">
        <Wifi size={11} className="text-gray-500" />
        <p className="text-[10px] text-gray-500">
          5초마다 자동 재연결 시도 중
          <span className="inline-block ml-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="inline-block w-1 h-1 rounded-full bg-gray-500 mx-0.5"
                style={{
                  animation: `pulse 1.2s ease-in-out ${i * 0.4}s infinite`,
                }}
              />
            ))}
          </span>
        </p>
      </div>
    </div>
  );
}
