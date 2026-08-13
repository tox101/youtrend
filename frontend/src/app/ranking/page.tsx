"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Trophy } from "lucide-react";
import CountrySelector from "@/components/CountrySelector";
import PeriodToggle from "@/components/PeriodToggle";
import RankCard from "@/components/RankCard";
import SkeletonList from "@/components/SkeletonList";
import { fetchRanking, type VideoRank } from "@/lib/api";
import { type CountryCode } from "@/lib/constants";

export default function RankingPage() {
  const [country, setCountry] = useState<CountryCode>("KR");
  const [period, setPeriod] = useState("daily");
  const [isShorts, setIsShorts] = useState(false);
  const [limit, setLimit] = useState(100);
  const [ranks, setRanks] = useState<VideoRank[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchRanking(country, isShorts, period, limit);
        setRanks(data);
      } catch {
        setRanks([]);
      }
      setLoading(false);
    };
    load();
  }, [country, period, isShorts, limit]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">랭킹</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          국가별 롱폼 영상 / 쇼츠 인기 순위
        </p>
      </motion.div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <CountrySelector selected={country} onSelect={setCountry} />
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <PeriodToggle selected={period} onSelect={setPeriod} />

        {/* Shorts / Longform Toggle */}
        <div className="period-toggle">
          <button className={!isShorts ? "active" : ""} onClick={() => setIsShorts(false)}>
            롱폼 영상
          </button>
          <button className={isShorts ? "active" : ""} onClick={() => setIsShorts(true)}>
            쇼츠
          </button>
        </div>

        {/* Limit Toggle */}
        <div className="period-toggle">
          <button className={limit === 50 ? "active" : ""} onClick={() => setLimit(50)}>
            Top 50
          </button>
          <button className={limit === 100 ? "active" : ""} onClick={() => setLimit(100)}>
            Top 100
          </button>
        </div>
      </div>

      {/* Ranking List */}
      {loading ? (
        <SkeletonList count={10} />
      ) : ranks.length > 0 ? (
        <div className="space-y-3">
          {ranks.map((r, i) => (
            <RankCard key={r.id} item={r} index={i} />
          ))}
        </div>
      ) : (
        <motion.div
          className="glass-card p-12 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Trophy size={48} className="mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            랭킹 데이터가 존재하지 않습니다
          </p>
          <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>
            조건에 부합하는 분석 데이터가 아직 집계되지 않았습니다.
          </p>
        </motion.div>
      )}
    </div>
  );
}
