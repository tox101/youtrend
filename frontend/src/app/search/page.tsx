"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  Film, 
  SlidersHorizontal, 
  Check, 
  Tv, 
  Clock, 
  Calendar, 
  Sparkles, 
  TrendingUp, 
  Users, 
  Play 
} from "lucide-react";
import { formatViews } from "@/lib/constants";
import { fetchFilteredVideos, type Video } from "@/lib/api";
import { COUNTRIES, type CountryCode } from "@/lib/constants";
import SkeletonList from "@/components/SkeletonList";

type AgeGroup = "all" | "40대" | "50대이상";
type GenderGroup = "전체" | "남성" | "여성" | "공통";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [targetAge, setTargetAge] = useState<AgeGroup>("all");
  const [targetGender, setTargetGender] = useState<GenderGroup>("전체");
  const [countryFilter, setCountryFilter] = useState<string>("");
  const [category, setCategory] = useState<string>(""); // "", "video", "shorts", "channel"
  const [duration, setDuration] = useState<string>(""); // "", "under_3", "3_to_20", "over_20"
  const [publishDate, setPublishDate] = useState<string>(""); // "", "today", "this_week", "this_month"
  const [features, setFeatures] = useState<string>(""); // "", "live", "4k", "hd"
  const [sortBy, setSortBy] = useState<string>("relevance"); // "relevance", "popularity"

  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Video[]>([]);
  const [searched, setSearched] = useState(false);

  const [hoveredVideo, setHoveredVideo] = useState<Video | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Trigger search on query change or filter change
  const executeSearch = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const data = await fetchFilteredVideos({
        q: query || undefined,
        target_age: targetAge !== "all" ? targetAge : undefined,
        target_gender: targetGender !== "전체" ? targetGender : undefined,
        country_code: countryFilter || undefined,
        category: category || undefined,
        duration: duration || undefined,
        publish_date: publishDate || undefined,
        features: features || undefined,
        sort_by: sortBy,
        limit: 100
      });
      setResults(data);
    } catch (err) {
      setResults([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    // Auto-search when any filter changes
    if (query.trim() || targetAge !== "all" || targetGender !== "전체" || countryFilter || category || duration || publishDate || features || sortBy !== "relevance") {
      executeSearch();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, targetAge, targetGender, countryFilter, category, duration, publishDate, features, sortBy]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch();
  };

  const handleThumbnailClick = (video: Video) => {
    const url = video.isShort
      ? `https://www.youtube.com/shorts/${video.video_id}`
      : `https://www.youtube.com/watch?v=${video.video_id}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePos({ x: e.clientX + 20, y: e.clientY + 20 });
  };

  const resetAllFilters = () => {
    setTargetAge("all");
    setTargetGender("전체");
    setCountryFilter("");
    setCategory("");
    setDuration("");
    setPublishDate("");
    setFeatures("");
    setSortBy("relevance");
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">검색 및 트렌드 분류</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          연령대 시청층 분석 및 유튜브 알고리즘 맞춤형 정밀 검색 필터링
        </p>
      </motion.div>

      {/* Target Age Pill Selection */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider mr-2" style={{ color: "var(--text-secondary)" }}>
          타겟 연령층:
        </span>
        {(["all", "40대", "50대이상"] as const).map((age) => (
          <button
            key={age}
            id={`age-btn-${age}`}
            className={`country-pill ${targetAge === age ? "active" : ""}`}
            onClick={() => setTargetAge(age)}
          >
            {age === "all" ? "전체 연령대" : age === "50대이상" ? "50대 이상" : age}
          </button>
        ))}
      </div>

      {/* Target Gender Pill Selection */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider mr-2" style={{ color: "var(--text-secondary)" }}>
          성별 타겟:
        </span>
        {(["전체", "남성", "여성", "공통"] as const).map((gender) => {
          const genderIcons: Record<string, string> = { "전체": "👥", "남성": "♂️", "여성": "♀️", "공통": "⚧" };
          const genderColors: Record<string, string> = { "전체": "", "남성": "border-blue-500 text-blue-400", "여성": "border-pink-500 text-pink-400", "공통": "border-purple-500 text-purple-400" };
          return (
            <button
              key={gender}
              id={`gender-btn-${gender}`}
              className={`country-pill ${targetGender === gender ? "active" : ""} ${targetGender === gender ? genderColors[gender] : ""}`}
              onClick={() => setTargetGender(gender)}
            >
              <span>{genderIcons[gender]}</span>
              <span>{gender}</span>
            </button>
          );
        })}
      </div>

      {/* Country Filter Selector */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider mr-2" style={{ color: "var(--text-secondary)" }}>
          국가 필터:
        </span>
        <button
          className={`country-pill ${countryFilter === "" ? "active" : ""}`}
          onClick={() => setCountryFilter("")}
        >
          <span>🌐</span>
          <span>전체</span>
        </button>
        {COUNTRIES.map((c) => (
          <button
            key={c.code}
            className={`country-pill ${countryFilter === c.code ? "active" : ""}`}
            onClick={() => setCountryFilter(c.code)}
          >
            <span>{c.flag}</span>
            <span>{c.code}</span>
          </button>
        ))}
      </div>

      {/* Quick Filter: Upload Date */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider mr-2" style={{ color: "var(--text-secondary)" }}>
          <Calendar size={12} className="inline-block mr-1 text-pink-400" />
          업로드 시점:
        </span>
        <button
          className={`country-pill ${publishDate === "" ? "active" : ""}`}
          onClick={() => setPublishDate("")}
        >
          전체 기간
        </button>
        {[
          { label: "오늘", val: "today" },
          { label: "이번 주", val: "this_week" },
          { label: "이번 달", val: "this_month" },
        ].map((item) => (
          <button
            key={item.val}
            id={`quick-date-${item.val}`}
            className={`country-pill ${publishDate === item.val ? "active" : ""}`}
            onClick={() => setPublishDate(publishDate === item.val ? "" : item.val)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Quick Filter: Content Type (영상 / Shorts) */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider mr-2" style={{ color: "var(--text-secondary)" }}>
          <Film size={12} className="inline-block mr-1 text-cyan-400" />
          콘텐츠 형식:
        </span>
        <button
          className={`country-pill ${category === "" ? "active" : ""}`}
          onClick={() => setCategory("")}
        >
          전체 형식
        </button>
        {[
          { label: "🎬 일반 영상", val: "video" },
          { label: "⚡ Shorts", val: "shorts" },
        ].map((item) => (
          <button
            key={item.val}
            id={`quick-cat-${item.val}`}
            className={`country-pill ${category === item.val ? "active" : ""}`}
            onClick={() => setCategory(category === item.val ? "" : item.val)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Search Input and Filters Toggle */}
      <form onSubmit={handleSubmit} className="flex gap-2 max-w-2xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 opacity-40" size={18} />
          <input
            id="search-input-field"
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
          type="button"
          id="toggle-filters-btn"
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-2.5 rounded-xl border font-medium text-sm flex items-center gap-2 transition-all ${
            showFilters ? "bg-indigo-600 border-indigo-600 text-white" : ""
          }`}
          style={!showFilters ? {
            background: "var(--bg-secondary)",
            borderColor: "var(--border-color)",
            color: "var(--text-primary)"
          } : {}}
        >
          <SlidersHorizontal size={16} />
          <span>필터</span>
        </button>
        <button
          type="submit"
          id="search-submit-btn"
          className="px-6 py-2.5 rounded-xl font-semibold text-sm text-white"
          style={{ background: "var(--gradient-primary)" }}
        >
          검색
        </button>
      </form>

      {/* YouTube Style Search Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div 
              className="glass-card p-5 grid grid-cols-2 md:grid-cols-5 gap-6 text-sm"
              style={{ background: "var(--bg-secondary)" }}
            >
              {/* 구분 (Category) */}
              <div className="space-y-3">
                <div className="font-bold flex items-center gap-1.5 border-b pb-1.5" style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
                  <Tv size={14} className="text-indigo-400" />
                  구분
                </div>
                <div className="flex flex-col gap-2">
                  {[
                    { label: "동영상", val: "video" },
                    { label: "Shorts 동영상", val: "shorts" },
                    { label: "채널", val: "channel" }
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      id={`filter-cat-${item.val}`}
                      onClick={() => setCategory(category === item.val ? "" : item.val)}
                      className={`text-left py-1 hover:text-white transition flex items-center justify-between ${
                        category === item.val ? "text-indigo-400 font-bold" : "text-gray-400"
                      }`}
                    >
                      <span>{item.label}</span>
                      {category === item.val && <Check size={14} />}
                    </button>
                  ))}
                </div>
              </div>

              {/* 길이 (Length) */}
              <div className="space-y-3">
                <div className="font-bold flex items-center gap-1.5 border-b pb-1.5" style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
                  <Clock size={14} className="text-purple-400" />
                  길이
                </div>
                <div className="flex flex-col gap-2">
                  {[
                    { label: "3분 미만", val: "under_3" },
                    { label: "3~20분", val: "3_to_20" },
                    { label: "20분 초과", val: "over_20" }
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      id={`filter-len-${item.val}`}
                      onClick={() => setDuration(duration === item.val ? "" : item.val)}
                      className={`text-left py-1 hover:text-white transition flex items-center justify-between ${
                        duration === item.val ? "text-purple-400 font-bold" : "text-gray-400"
                      }`}
                    >
                      <span>{item.label}</span>
                      {duration === item.val && <Check size={14} />}
                    </button>
                  ))}
                </div>
              </div>

              {/* 업로드 날짜 (Upload date) */}
              <div className="space-y-3">
                <div className="font-bold flex items-center gap-1.5 border-b pb-1.5" style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
                  <Calendar size={14} className="text-pink-400" />
                  업로드 날짜
                </div>
                <div className="flex flex-col gap-2">
                  {[
                    { label: "오늘", val: "today" },
                    { label: "이번 주", val: "this_week" },
                    { label: "이번 달", val: "this_month" }
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      id={`filter-date-${item.val}`}
                      onClick={() => setPublishDate(publishDate === item.val ? "" : item.val)}
                      className={`text-left py-1 hover:text-white transition flex items-center justify-between ${
                        publishDate === item.val ? "text-pink-400 font-bold" : "text-gray-400"
                      }`}
                    >
                      <span>{item.label}</span>
                      {publishDate === item.val && <Check size={14} />}
                    </button>
                  ))}
                </div>
              </div>

              {/* 기능별 (Features) */}
              <div className="space-y-3">
                <div className="font-bold flex items-center gap-1.5 border-b pb-1.5" style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
                  <Sparkles size={14} className="text-amber-400" />
                  기능별
                </div>
                <div className="flex flex-col gap-2">
                  {[
                    { label: "라이브", val: "live" },
                    { label: "4K", val: "4k" },
                    { label: "HD", val: "hd" }
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      id={`filter-feat-${item.val}`}
                      onClick={() => setFeatures(features === item.val ? "" : item.val)}
                      className={`text-left py-1 hover:text-white transition flex items-center justify-between ${
                        features === item.val ? "text-amber-400 font-bold" : "text-gray-400"
                      }`}
                    >
                      <span>{item.label}</span>
                      {features === item.val && <Check size={14} />}
                    </button>
                  ))}
                </div>
              </div>

              {/* 우선순위 (Sort by) */}
              <div className="space-y-3">
                <div className="font-bold flex items-center gap-1.5 border-b pb-1.5" style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}>
                  <TrendingUp size={14} className="text-emerald-400" />
                  우선순위
                </div>
                <div className="flex flex-col gap-2">
                  {[
                    { label: "관련성", val: "relevance" },
                    { label: "인기도", val: "popularity" }
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      id={`filter-sort-${item.val}`}
                      onClick={() => setSortBy(item.val)}
                      className={`text-left py-1 hover:text-white transition flex items-center justify-between ${
                        sortBy === item.val ? "text-emerald-400 font-bold" : "text-gray-400"
                      }`}
                    >
                      <span>{item.label}</span>
                      {sortBy === item.val && <Check size={14} />}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Reset Filters Bar */}
            <div className="flex justify-end mt-2">
              <button 
                type="button" 
                onClick={resetAllFilters} 
                className="text-xs hover:text-indigo-400 transition" 
                style={{ color: "var(--text-secondary)" }}
              >
                필터 초기화
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Section */}
      {loading ? (
        <SkeletonList count={5} />
      ) : results.length > 0 ? (
        <div className="space-y-2">
          {/* Results count header */}
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
              총 {results.length}개 결과
            </span>
          </div>

          {results.map((video, i) => {
            // Render channel result card (horizontal row)
            if (video.is_channel) {
              return (
                <motion.div
                  key={`chan-${video.video_id}`}
                  className="glass-card p-3 flex items-center gap-4"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i * 0.02, 1) }}
                >
                  {/* Rank Badge */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                    i === 0 ? "bg-amber-500/20 text-amber-400 border border-amber-500/40" :
                    i === 1 ? "bg-gray-400/20 text-gray-300 border border-gray-400/40" :
                    i === 2 ? "bg-orange-600/20 text-orange-400 border border-orange-600/40" :
                    "bg-white/5 border border-white/10"
                  }`} style={i > 2 ? { color: "var(--text-secondary)" } : {}}>
                    {i + 1}
                  </div>

                  {/* Channel Avatar */}
                  <div 
                    className="w-12 h-12 rounded-full overflow-hidden border-2 border-indigo-500 flex-shrink-0"
                    style={{ background: "var(--bg-secondary)" }}
                  >
                    {video.thumbnail ? (
                      <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xs font-bold bg-indigo-900">
                        {video.title.charAt(0)}
                      </div>
                    )}
                  </div>

                  {/* Channel Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                      {video.title}
                    </h3>
                    <p className="text-xs text-indigo-400 font-semibold">
                      @{video.channel?.custom_url || "channel"}
                    </p>
                  </div>

                  {/* Channel Stats */}
                  <div className="flex-shrink-0 flex items-center gap-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <div className="text-center">
                      <span className="block font-bold text-sm" style={{ color: "var(--text-primary)" }}>{formatViews(video.subscriber)}</span>
                      <span>구독자</span>
                    </div>
                    <div className="text-center">
                      <span className="block font-bold text-sm" style={{ color: "var(--text-primary)" }}>{formatViews(video.views)}</span>
                      <span>총 조회수</span>
                    </div>
                  </div>
                </motion.div>
              );
            }

            // Render normal video result card (horizontal row with rank)
            const likeRate = video.views > 0 ? ((video.likes / video.views) * 100).toFixed(1) : "0";
            const commentRate = video.views > 0 ? ((video.comments / video.views) * 100).toFixed(2) : "0";

            return (
              <motion.div
                key={video.video_id}
                className="glass-card p-3 flex items-center gap-3 cursor-pointer hover:border-indigo-500/50 transition-all duration-200"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.02, 1) }}
              >
                {/* Rank Badge */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                  i === 0 ? "bg-amber-500/20 text-amber-400 border border-amber-500/40" :
                  i === 1 ? "bg-gray-400/20 text-gray-300 border border-gray-400/40" :
                  i === 2 ? "bg-orange-600/20 text-orange-400 border border-orange-600/40" :
                  "bg-white/5 border border-white/10"
                }`} style={i > 2 ? { color: "var(--text-secondary)" } : {}}>
                  {i + 1}
                </div>

                {/* Thumbnail */}
                <div
                  onClick={() => handleThumbnailClick(video)}
                  onMouseEnter={() => setHoveredVideo(video)}
                  onMouseLeave={() => setHoveredVideo(null)}
                  onMouseMove={handleMouseMove}
                  className="relative flex-shrink-0 w-28 h-16 rounded-lg overflow-hidden group/thumb cursor-pointer hover:ring-2 hover:ring-indigo-500 transition-all duration-200"
                  style={{ background: "var(--bg-secondary)" }}
                  title="마우스 호버: 미리보기 / 클릭: 유튜브 재생"
                >
                  {video.thumbnail ? (
                    <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform duration-200" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[10px]" style={{ color: "var(--text-secondary)" }}>
                      이미지 없음
                    </div>
                  )}

                  {/* Play Overlay */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center transition-opacity duration-200">
                    <Play size={16} className="text-white fill-white" />
                  </div>

                  {video.isShort && (
                    <span className="absolute top-1 left-1 px-1.5 py-0.5 text-[8px] font-bold rounded bg-red-500 text-white z-10">SHORT</span>
                  )}
                </div>

                {/* Video Info */}
                <div className="flex-1 min-w-0">
                  <h3 
                    onClick={() => handleThumbnailClick(video)}
                    className="text-sm font-semibold truncate cursor-pointer hover:text-indigo-400 transition" 
                    style={{ color: "var(--text-primary)" }}
                  >
                    {video.title}
                  </h3>
                  <p className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>
                    {video.channel?.title || "알 수 없는 채널"}
                  </p>
                </div>

                {/* Badges */}
                <div className="flex-shrink-0 flex items-center gap-1.5">
                  {video.target_gender && video.target_gender !== "공통" && (
                    <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded-md text-white ${
                      video.target_gender === "남성" ? "bg-blue-500/80" : "bg-pink-500/80"
                    }`}>
                      {video.target_gender === "남성" ? "♂️" : "♀️"} {video.target_gender}
                    </span>
                  )}
                  {video.target_age && video.target_age !== "all" && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-indigo-500/80 text-white">
                      🎯 {video.target_age}
                    </span>
                  )}
                </div>

                {/* Stats */}
                <div className="flex-shrink-0 flex items-center gap-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                  <span>👁 {formatViews(video.views)}</span>
                  <span className="text-emerald-400 font-medium">👍 {likeRate}%</span>
                  <span className="text-amber-400 font-medium">💬 {commentRate}%</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : searched ? (
        <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
          <Film size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            검색 결과가 없습니다
          </p>
          <p className="text-sm mt-2">
            다른 키워드나 연령대/필터 조합을 시도해보세요.
          </p>
        </div>
      ) : (
        <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
          <Search size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            원하는 키워드를 입력해 보세요
          </p>
          <p className="text-sm mt-2">
            연령대 필터와 유튜브 필터를 조합하여 타겟 시청자 기획안을 도출할 수 있습니다.
          </p>
        </div>
      )}

      {/* Hover Preview Mini Player Portal */}
      <AnimatePresence>
        {hoveredVideo && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed pointer-events-none rounded-xl overflow-hidden shadow-2xl border z-[9999]"
            style={{
              left: mousePos.x,
              top: mousePos.y,
              width: hoveredVideo.isShort ? 350 : 560,
              height: hoveredVideo.isShort ? 622 : 315,
              background: "#000",
              borderColor: "var(--border-color)",
            }}
          >
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${hoveredVideo.video_id}?autoplay=1&mute=1&controls=0&rel=0&loop=1&playlist=${hoveredVideo.video_id}&showinfo=0&modestbranding=1`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              style={{ pointerEvents: "none" }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
