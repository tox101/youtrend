"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, Globe, ShieldAlert } from "lucide-react";
import { fetchCountryDiff } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function ComparePage() {
  const [videoId, setVideoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoId.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await fetchCountryDiff(videoId.trim());
      setComparison(data);
    } catch (err) {
      setComparison([]);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">국가별 비교 🌍</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          특정 유튜브 비디오의 국가별 실시간 순위 및 Virality Score 비교 분석
        </p>
      </motion.div>

      {/* Video ID Input */}
      <form onSubmit={handleCompare} className="flex gap-2 max-w-md">
        <input
          type="text"
          placeholder="유튜브 비디오 ID를 입력하세요 (예: dQw4w9WgXcQ)"
          className="flex-1 px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-indigo-500"
          style={{
            background: "var(--bg-secondary)",
            borderColor: "var(--border-color)",
            color: "var(--text-primary)"
          }}
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
        />
        <button
          type="submit"
          className="px-6 py-2.5 rounded-xl font-semibold text-sm text-white"
          style={{ background: "var(--gradient-primary)" }}
        >
          비교
        </button>
      </form>

      {loading ? (
        <div className="glass-card p-12 text-center skeleton" />
      ) : comparison.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Comparison Matrix Table */}
          <motion.div className="glass-card p-5" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              📊 국가별 실시간 인기 순위 현황
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b" style={{ borderColor: "var(--border-color)", color: "var(--text-secondary)" }}>
                    <th className="py-2.5 font-semibold">국가</th>
                    <th className="py-2.5 font-semibold">순위</th>
                    <th className="py-2.5 font-semibold">Virality Score</th>
                    <th className="py-2.5 font-semibold">갱신일</th>
                  </tr>
                </thead>
                <tbody style={{ color: "var(--text-primary)" }}>
                  {comparison.map((item, idx) => (
                    <tr key={idx} className="border-b" style={{ borderColor: "var(--border-color)" }}>
                      <td className="py-3 font-medium">{item.country_name} ({item.country_code})</td>
                      <td className="py-3">
                        {item.rank ? (
                          <span className="font-bold text-indigo-400">{item.rank}위</span>
                        ) : (
                          <span style={{ color: "var(--text-secondary)" }}>차트 아웃</span>
                        )}
                      </td>
                      <td className="py-3 font-semibold">
                        {item.virality_score !== null ? `${item.virality_score.toFixed(1)}점` : "-"}
                      </td>
                      <td className="py-3" style={{ color: "var(--text-secondary)" }}>
                        {item.rank_date || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Bar Chart Visualization */}
          <motion.div className="glass-card p-5" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              📈 국가별 Virality Score 차트
            </h2>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={comparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="country_code" tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "var(--text-secondary)" }} />
                <Tooltip
                  contentStyle={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="virality_score" fill="#6366f1" radius={[4, 4, 0, 0]} name="Virality Score" />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      ) : searched ? (
        <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
          <Globe size={36} className="mx-auto mb-2 opacity-30" />
          <p className="text-sm">입력한 비디오 ID의 국가별 순위 기록을 찾을 수 없습니다.</p>
          <p className="text-xs mt-1">올바른 비디오 ID를 사용하거나 랭킹 파이프라인 작동 후 다시 시도해 주세요.</p>
        </div>
      ) : null}
    </div>
  );
}
