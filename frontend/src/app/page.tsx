"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Eye,
  ThumbsUp,
  Flame,
  Trophy,
  Gem,
  Users,
  Globe,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import StatCard from "@/components/StatCard";
import CountrySelector from "@/components/CountrySelector";
import RankCard from "@/components/RankCard";
import SkeletonList from "@/components/SkeletonList";
import { fetchRanking, fetchSystemStatus, type VideoRank, type SystemStatus } from "@/lib/api";
import { COUNTRIES, formatViews, type CountryCode } from "@/lib/constants";

// Mock dashboard stats (replaced with live data once crawler populates DB)
const MOCK_STATS = {
  totalCountries: 8,
  avgViralScore: 62.4,
  hotAlerts: 12,
};

// Mock chart data for the area chart
const MOCK_TREND_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  KR: Math.floor(Math.random() * 80 + 20),
  US: Math.floor(Math.random() * 90 + 30),
  JP: Math.floor(Math.random() * 60 + 15),
  IN: Math.floor(Math.random() * 70 + 25),
}));

// Mock country comparison bar chart
const MOCK_COUNTRY_BAR = COUNTRIES.map((c) => ({
  country: c.flag + " " + c.code,
  longform: Math.floor(Math.random() * 50 + 20),
  shorts: Math.floor(Math.random() * 50 + 10),
}));

export default function DashboardPage() {
  const [country, setCountry] = useState<CountryCode>("KR");
  const [longformRanks, setLongformRanks] = useState<VideoRank[]>([]);
  const [shortsRanks, setShortsRanks] = useState<VideoRank[]>([]);
  const [loading, setLoading] = useState(true);
  const [sysStatus, setSysStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [lf, sh, status] = await Promise.all([
          fetchRanking(country, false, "daily", 10),
          fetchRanking(country, true, "daily", 10),
          fetchSystemStatus(),
        ]);
        setLongformRanks(lf);
        setShortsRanks(sh);
        setSysStatus(status);
      } catch {
        // Graceful fallback
      }
      setLoading(false);
    };
    load();
  }, [country]);

  return (
    <div className="space-y-8">
      {/* Header with Live System Status Badges */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-extrabold gradient-text">대시보드</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            유튜브 글로벌 인텔리전스 플랫폼 — 실시간 트렌드 모니터링
          </p>
        </div>

        {/* Live System Health Badge */}
        <div className="flex items-center gap-2">
          {sysStatus ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>시스템 정상 가동 중</span>
              <span style={{ color: "var(--text-secondary)" }}>|</span>
              <span style={{ color: "var(--text-secondary)" }}>수집 주기: {sysStatus.scheduler_interval_minutes}분</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span>시스템 상태 감지 중</span>
            </div>
          )}
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="수집 영상 수"
          value={sysStatus ? formatViews(sysStatus.total_videos) : "0"}
          subtitle="실시간 DB 적재량"
          icon={Eye}
          color="#6366f1"
          delay={0}
        />
        <StatCard
          title="수집 국가"
          value={MOCK_STATS.totalCountries}
          subtitle="8개국 실시간"
          icon={Globe}
          color="#8b5cf6"
          delay={0.1}
        />
        <StatCard
          title="평균 Virality Score"

          value={MOCK_STATS.avgViralScore}
          subtitle="상위 10% 기준"
          icon={Flame}
          color="#f59e0b"
          delay={0.2}
        />
        <StatCard
          title="알림"
          value={MOCK_STATS.hotAlerts}
          subtitle="미확인 알림"
          icon={TrendingUp}
          color="#ef4444"
          delay={0.3}
        />
      </div>

      {/* Country Selector */}
      <CountrySelector selected={country} onSelect={setCountry} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Area Chart */}
        <motion.div
          className="glass-card p-5"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            📈 24시간 Virality Score 추이
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={MOCK_TREND_DATA}>
              <defs>
                <linearGradient id="gradientKR" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientUS" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
              <YAxis tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-color)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Area type="monotone" dataKey="KR" stroke="#6366f1" fillOpacity={1} fill="url(#gradientKR)" />
              <Area type="monotone" dataKey="US" stroke="#8b5cf6" fillOpacity={1} fill="url(#gradientUS)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Country Comparison Bar */}
        <motion.div
          className="glass-card p-5"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            🌍 국가별 인기 영상 수
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={MOCK_COUNTRY_BAR}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="country" tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
              <YAxis tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-color)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="longform" fill="#6366f1" radius={[4, 4, 0, 0]} name="롱폼 영상" />
              <Bar dataKey="shorts" fill="#a855f7" radius={[4, 4, 0, 0]} name="쇼츠" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Ranking Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Longform Top 10 */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Trophy size={18} style={{ color: "#6366f1" }} />
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              롱폼 영상 Top 10
            </h2>
          </div>
          {loading ? (
            <SkeletonList count={5} />
          ) : longformRanks.length > 0 ? (
            <div className="space-y-3">
              {longformRanks.map((r, i) => (
                <RankCard key={r.id} item={r} index={i} />
              ))}
            </div>
          ) : (
            <div className="glass-card p-8 text-center" style={{ color: "var(--text-secondary)" }}>
              <Trophy size={32} className="mx-auto mb-2 opacity-40" />
              <p className="text-sm">데이터 수집 중입니다. 잠시만 기다려주세요.</p>
              <p className="text-xs mt-1">크롤러 실행 후 랭킹이 여기에 표시됩니다.</p>
            </div>
          )}
        </div>

        {/* Shorts Top 10 */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Flame size={18} style={{ color: "#ef4444" }} />
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              쇼츠 Top 10
            </h2>
          </div>
          {loading ? (
            <SkeletonList count={5} />
          ) : shortsRanks.length > 0 ? (
            <div className="space-y-3">
              {shortsRanks.map((r, i) => (
                <RankCard key={r.id} item={r} index={i} />
              ))}
            </div>
          ) : (
            <div className="glass-card p-8 text-center" style={{ color: "var(--text-secondary)" }}>
              <Flame size={32} className="mx-auto mb-2 opacity-40" />
              <p className="text-sm">Shorts 데이터를 아직 수집하지 못했습니다.</p>
              <p className="text-xs mt-1">Playwright 크롤러가 5분 주기로 수집합니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
