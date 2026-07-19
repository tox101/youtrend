"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Gem, Play } from "lucide-react";
import CountrySelector from "@/components/CountrySelector";
import SkeletonList from "@/components/SkeletonList";
import { fetchHiddenGems, type Video } from "@/lib/api";
import { formatViews, type CountryCode } from "@/lib/constants";

export default function HiddenGemsPage() {
  const [country, setCountry] = useState<CountryCode>("US");
  const [isShorts, setIsShorts] = useState<boolean | undefined>(undefined); // undefined: 전체, false: 롱폼, true: 쇼츠
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  const [hoveredVideo, setHoveredVideo] = useState<Video | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchHiddenGems(country, isShorts, 30);
        setVideos(data);
      } catch {
        setVideos([]);
      }
      setLoading(false);
    };
    load();
  }, [country, isShorts]);

  const handleThumbnailClick = (video: Video) => {
    const url = video.isShort
      ? `https://www.youtube.com/shorts/${video.video_id}`
      : `https://www.youtube.com/watch?v=${video.video_id}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePos({ x: e.clientX + 20, y: e.clientY + 20 });
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">숨은 보석 💎 (한·일 미출시 기획 탐지기)</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          해외에서 급상승 중이거나 꾸준히 흥행하고 있지만, 한국과 일본 트렌드에는 아직 유입되지 않은 미개척 콘텐츠입니다. 벤치마킹하여 국내용 기획으로 빠르게 활용해 보세요!
        </p>
      </motion.div>

      {/* KR, JP를 배제한 해외 국가 및 비디오 형식 필터 */}
      <div className="flex flex-wrap items-center gap-4 justify-between">
        <CountrySelector selected={country} onSelect={setCountry} excludeCodes={["KR", "JP"]} />
        
        {/* 비디오 형식 토글 */}
        <div className="period-toggle">
          <button className={isShorts === undefined ? "active" : ""} onClick={() => setIsShorts(undefined)}>
            전체
          </button>
          <button className={isShorts === false ? "active" : ""} onClick={() => setIsShorts(false)}>
            롱폼 영상
          </button>
          <button className={isShorts === true ? "active" : ""} onClick={() => setIsShorts(true)}>
            쇼츠
          </button>
        </div>
      </div>

      {loading ? (
        <SkeletonList count={6} />
      ) : videos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {videos.map((video, i) => {
            const likeRate = video.views > 0 ? ((video.likes / video.views) * 100).toFixed(1) : "0";
            const commentRate = video.views > 0 ? ((video.comments / video.views) * 100).toFixed(2) : "0";
            return (
              <motion.div
                key={video.video_id}
                className="glass-card p-4 text-decoration-none"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
              >
                <div
                  onClick={() => handleThumbnailClick(video)}
                  onMouseEnter={() => setHoveredVideo(video)}
                  onMouseLeave={() => setHoveredVideo(null)}
                  onMouseMove={handleMouseMove}
                  className="relative w-full h-36 rounded-lg overflow-hidden mb-3 group/thumb cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all duration-200"
                  style={{ background: "var(--bg-secondary)" }}
                  title="마우스 호버: 미리보기 / 클릭: 유튜브 재생"
                >
                  {video.thumbnail ? (
                    <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform duration-200" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs" style={{ color: "var(--text-secondary)" }}>이미지 없음</div>
                  )}

                  {/* Play Icon Overlay on Hover */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center transition-opacity duration-200">
                    <Play size={24} className="text-white fill-white" />
                  </div>

                  <span className="absolute top-2 right-2 px-2 py-1 text-[10px] font-bold rounded-lg bg-emerald-500/90 text-white flex items-center gap-1 z-10">
                    <Gem size={10} /> 숨은 보석
                  </span>
                  
                  {video.isShort && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-bold rounded bg-red-500 text-white z-10">SHORT</span>
                  )}
                </div>
                <h3 className="text-sm font-semibold line-clamp-2 mb-1 cursor-pointer" style={{ color: "var(--text-primary)" }} onClick={() => handleThumbnailClick(video)}>
                  {video.title}
                </h3>
                <p className="text-xs truncate mb-2" style={{ color: "var(--text-secondary)" }}>
                  {video.channel?.title || "알 수 없는 채널"}
                </p>
                <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                  <span>👁 {formatViews(video.views)}</span>
                  <span className="text-emerald-400 font-medium">👍 {likeRate}%</span>
                  <span className="text-amber-400 font-medium">💬 {commentRate}%</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <motion.div className="glass-card p-12 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Gem size={48} className="mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>한·일 미출시 숨은 보석이 아직 없습니다</p>
          <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>해외 파이프라인 수집 데이터를 축적 중입니다.</p>
        </motion.div>
      )}

      {/* Floating Hover Video Player Portal */}
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
