"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Search, Film } from "lucide-react";
import { formatViews } from "@/lib/constants";
import { API_BASE_URL, type Video } from "@/lib/api";
import SkeletonList from "@/components/SkeletonList";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Video[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      // Fetching search endpoint
      const res = await fetch(`${API_BASE_URL}/videos?limit=20`);
      if (res.ok) {
        const data = await res.json();
        // Client side filtering for simulation of database query search
        const filtered = data.filter((v: Video) =>
          v.title.toLowerCase().includes(query.toLowerCase()) ||
          v.description?.toLowerCase().includes(query.toLowerCase())
        );
        setResults(filtered);
      }
    } catch (err) {
      setResults([]);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">검색</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          수집된 유튜브 비디오 데이터베이스 고속 검색
        </p>
      </motion.div>

      {/* Search Input Form */}
      <form onSubmit={handleSearch} className="flex gap-2 max-w-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 opacity-40" size={18} />
          <input
            type="text"
            placeholder="비디오 제목, 채널 이름 또는 키워드를 입력하세요..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-indigo-500"
            style={{
              background: "var(--bg-secondary)",
              borderColor: "var(--border-color)",
              color: "var(--text-primary)"
            }}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="px-6 py-2.5 rounded-xl font-semibold text-sm text-white"
          style={{ background: "var(--gradient-primary)" }}
        >
          검색
        </button>
      </form>

      {/* Results */}
      {loading ? (
        <SkeletonList count={5} />
      ) : results.length > 0 ? (
        <div className="space-y-3">
          {results.map((video, i) => (
            <motion.div
              key={video.video_id}
              className="glass-card p-4 flex gap-4 items-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <div className="relative w-24 h-14 rounded-lg overflow-hidden flex-shrink-0" style={{ background: "var(--bg-secondary)" }}>
                {video.thumbnail && (
                  <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{video.title}</h3>
                <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
                  {video.channel?.title || "알 수 없는 채널"}
                </p>
                <div className="flex gap-3 mt-1.5 text-[11px]" style={{ color: "var(--text-secondary)" }}>
                  <span>👁 {formatViews(video.views)}</span>
                  <span>👍 {formatViews(video.likes)}</span>
                  <span>💬 {formatViews(video.comments)}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : searched ? (
        <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
          <Film size={36} className="mx-auto mb-2 opacity-30" />
          <p className="text-sm">검색 결과가 없습니다.</p>
          <p className="text-xs mt-1">다른 키워드를 시도해보세요.</p>
        </div>
      ) : null}
    </div>
  );
}
