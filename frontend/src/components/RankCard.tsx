import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Play } from "lucide-react";
import { formatViews, getScoreColor, getScoreBg } from "@/lib/constants";
import type { Video, VideoRank } from "@/lib/api";

interface RankCardProps {
  item: VideoRank;
  index: number;
}

export default function RankCard({ item, index }: RankCardProps) {
  const video = item.video;
  const rank = item.rank;
  const score = item.virality_score;

  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const rankClass =
    rank === 1
      ? "top-1"
      : rank === 2
        ? "top-2"
        : rank === 3
          ? "top-3"
          : "top-n";

  const handleThumbnailClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const url = video.isShort
      ? `https://www.youtube.com/shorts/${video.video_id}`
      : `https://www.youtube.com/watch?v=${video.video_id}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    // Offset relative to viewport for fixed position placement
    setMousePos({ x: e.clientX + 20, y: e.clientY + 20 });
  };

  return (
    <>
      <Link href={`/video?id=${video.video_id}`} style={{ textDecoration: "none" }}>
        <motion.div
          className="glass-card p-4 flex items-center gap-4 cursor-pointer"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.03, duration: 0.4 }}
        >
          {/* Rank badge */}
          <div className={`rank-badge ${rankClass}`}>
            {rank}
          </div>

          {/* Thumbnail */}
          <div
            onClick={handleThumbnailClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onMouseMove={handleMouseMove}
            className="relative flex-shrink-0 w-24 h-14 rounded-lg overflow-hidden group/thumb cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all duration-200"
            style={{ background: "var(--bg-secondary)" }}
            title="마우스 호버: 미리보기 / 클릭: 유튜브 재생"
          >
            {video.thumbnail ? (
              <img
                src={video.thumbnail}
                alt={video.title}
                className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform duration-200"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs" style={{ color: "var(--text-secondary)" }}>
                No Img
              </div>
            )}
            
            {/* Play Icon Overlay on Hover */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center transition-opacity duration-200">
              <Play size={18} className="text-white fill-white" />
            </div>

            {video.isShort && (
              <span className="absolute top-1 left-1 px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-500 text-white z-10">
                SHORT
              </span>
            )}
          </div>

          {/* Video info */}
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
              {video.title}
            </h3>
            <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
              {video.channel?.title || "알 수 없는 채널"}
            </p>
            <div className="flex items-center gap-3 mt-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
              <span>👁 {formatViews(video.views)}</span>
              <span>👍 {formatViews(video.likes)}</span>
              <span>💬 {formatViews(video.comments)}</span>
            </div>
          </div>

          {/* Score */}
          <div className="flex-shrink-0 text-right">
            <div
              className={`inline-block px-3 py-1.5 rounded-lg border text-sm font-bold ${getScoreBg(score)}`}
            >
              <span className={getScoreColor(score)}>{score.toFixed(1)}</span>
            </div>
            <div className="score-bar mt-2 w-20">
              <div className="score-bar-fill" style={{ width: `${score}%` }} />
            </div>
          </div>
        </motion.div>
      </Link>

      {/* Floating Hover Video Player Portal */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed pointer-events-none rounded-xl overflow-hidden shadow-2xl border z-[9999]"
            style={{
              left: mousePos.x,
              top: mousePos.y,
              width: video.isShort ? 350 : 560,
              height: video.isShort ? 622 : 315,
              background: "#000",
              borderColor: "var(--border-color)",
            }}
          >
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${video.video_id}?autoplay=1&mute=1&controls=0&rel=0&loop=1&playlist=${video.video_id}&showinfo=0&modestbranding=1`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              style={{ pointerEvents: "none" }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
