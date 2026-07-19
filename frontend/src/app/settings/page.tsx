"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings, Play, RefreshCw, Cpu } from "lucide-react";
import { triggerCrawlerManual, triggerRankingManual, fetchSystemStatus, type SystemStatus } from "@/lib/api";
import { formatDate } from "@/lib/constants";

export default function SettingsPage() {
  const [crawling, setCrawling] = useState(false);
  const [ranking, setRanking] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [sysStatus, setSysStatus] = useState<SystemStatus | null>(null);

  const loadStatus = async () => {
    try {
      const data = await fetchSystemStatus();
      setSysStatus(data);
    } catch {
      // Fail silently
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const runCrawler = async () => {
    setCrawling(true);
    setStatus("크롤러 수동 가동 요청을 서버에 전송 중...");
    try {
      const res = await triggerCrawlerManual();
      if (res && res.status === "success") {
        setStatus(`요청 완료: ${res.message}`);
        await loadStatus();
      } else {
        setStatus("크롤링 실행 요청에 실패했습니다.");
      }
    } catch (err) {
      setStatus("크롤러 실행 중 네트워크 오류가 발생했습니다.");
    }
    setCrawling(false);
  };

  const runRankingEngine = async () => {
    setRanking(true);
    setStatus("랭킹 엔진 재연산 수동 가동 요청을 서버에 전송 중...");
    try {
      const res = await triggerRankingManual();
      if (res && res.status === "success") {
        setStatus(`요청 완료: ${res.message}`);
        await loadStatus();
      } else {
        setStatus("랭킹 재연산 요청에 실패했습니다.");
      }
    } catch (err) {
      setStatus("랭킹 계산 처리 중 네트워크 오류가 발생했습니다.");
    }
    setRanking(false);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">설정</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          시스템 수동 동작 제어 및 환경 매개변수 설정
        </p>
      </motion.div>

      {/* System Status Dashboard widget */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          🟢 플랫폼 시스템 가동 현황
        </h2>
        {sysStatus ? (
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
              <p style={{ color: "var(--text-secondary)" }}>데이터베이스 연결</p>
              <p className="text-sm font-bold text-emerald-400">정상 (Connected)</p>
            </div>
            <div className="p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
              <p style={{ color: "var(--text-secondary)" }}>백그라운드 스케줄 주기</p>
              <p className="text-sm font-bold text-indigo-400">매 {sysStatus.scheduler_interval_minutes}분마다 자동 크롤링</p>
            </div>
            <div className="p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
              <p style={{ color: "var(--text-secondary)" }}>총 수집 영상 수 / 채널 수</p>
              <p className="text-sm font-bold text-violet-400">{sysStatus.total_videos.toLocaleString()}개 / {sysStatus.total_channels.toLocaleString()}개</p>
            </div>
            <div className="p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
              <p style={{ color: "var(--text-secondary)" }}>마지막 랭킹 연산 갱신</p>
              <p className="text-sm font-bold text-amber-400">{sysStatus.latest_rank_update ? formatDate(sysStatus.latest_rank_update) : "이력 없음"}</p>
            </div>
          </div>
        ) : (
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>시스템 현황 데이터를 받아오고 있습니다...</p>
        )}
      </div>

      {/* Control Actions */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          ⚙️ 시스템 관리자 원격 제어
        </h2>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          5분 주기를 기다리지 않고 강제로 데이터를 크롤링하거나 랭킹 가중치 스코어를 재계산할 수 있습니다.
        </p>

        <div className="flex flex-wrap gap-3 pt-2">
          <button
            onClick={runCrawler}
            disabled={crawling}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs text-white transition hover:opacity-90 disabled:opacity-50"
            style={{ background: "var(--gradient-primary)" }}
          >
            <Play size={14} className={crawling ? "animate-spin" : ""} />
            {crawling ? "수집 엔진 작동 중..." : "크롤러 즉시 가동 (Playwright/API)"}
          </button>

          <button
            onClick={runRankingEngine}
            disabled={ranking}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
          >
            <RefreshCw size={14} className={ranking ? "animate-spin" : ""} />
            {ranking ? "연산 중..." : "랭킹 및 Virality Score 재산출"}
          </button>
        </div>
      </div>


      {/* AI Configuration */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          🤖 로컬 인공지능 매개변수
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] uppercase font-bold mb-1.5" style={{ color: "var(--text-secondary)" }}>
              AI 제공자 (AI Provider)
            </label>
            <input
              type="text"
              disabled
              value="LM Studio"
              className="w-full px-3.5 py-2 rounded-lg border text-xs cursor-not-allowed opacity-60"
              style={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase font-bold mb-1.5" style={{ color: "var(--text-secondary)" }}>
              로컬 모델 명칭
            </label>
            <input
              type="text"
              disabled
              value="Qwen AgentWorld 35B A3B UD"
              className="w-full px-3.5 py-2 rounded-lg border text-xs cursor-not-allowed opacity-60"
              style={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
            />
          </div>
        </div>
      </div>

      {/* Status Notice */}
      {status && (
        <motion.div
          className="p-4 rounded-xl border text-xs"
          style={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex gap-2 items-center">
            <Cpu size={14} className="text-indigo-400" />
            <span>{status}</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}
