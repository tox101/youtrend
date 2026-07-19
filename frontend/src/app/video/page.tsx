"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  TrendingUp,
  Eye,
  ThumbsUp,
  MessageSquare,
  Clock,
  BarChart3,
  Sparkles,
  Target,
  Lightbulb,
  Users,
  Film,
  Zap,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  fetchVideoDetail,
  fetchAIAnalysis,
  triggerAIAnalysis,
  fetchPrediction,
  fetchRankingHistory,
  type Video,
  type AIAnalysis,
  type Prediction,
  type RankingHistory,
} from "@/lib/api";
import { formatViews, formatDate } from "@/lib/constants";

function VideoDetailContent() {
  const searchParams = useSearchParams();
  const videoId = searchParams.get("id") || "";

  const [video, setVideo] = useState<Video | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<RankingHistory[]>([]);
  const [loadingAI, setLoadingAI] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!videoId) return;
    const load = async () => {
      setLoading(true);
      const [v, a, p, h] = await Promise.all([
        fetchVideoDetail(videoId),
        fetchAIAnalysis(videoId),
        fetchPrediction(videoId),
        fetchRankingHistory(videoId, 30),
      ]);
      setVideo(v);
      setAnalysis(a);
      setPrediction(p);
      setHistory(h);
      setLoading(false);
    };
    load();
  }, [videoId]);

  const handleTriggerAI = async () => {
    if (!videoId) return;
    setLoadingAI(true);
    const result = await triggerAIAnalysis(videoId);
    if (result) setAnalysis(result);
    setLoadingAI(false);
  };

  if (!videoId) {
    return (
      <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
        <Film size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-lg font-semibold">올바르지 않은 접근입니다</p>
        <p className="text-sm mt-2">비디오 ID 파라미터가 유실되었습니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-1/2 rounded" />
        <div className="skeleton h-64 w-full rounded-xl" />
        <div className="skeleton h-48 w-full rounded-xl" />
      </div>
    );
  }

  if (!video) {
    return (
      <div className="glass-card p-12 text-center" style={{ color: "var(--text-secondary)" }}>
        <Film size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-lg font-semibold">비디오를 찾을 수 없습니다</p>
        <p className="text-sm mt-2">올바른 비디오 ID를 확인해주세요: <code>{videoId}</code></p>
      </div>
    );
  }

  const aiSections = analysis
    ? [
        { icon: Sparkles, title: "왜 인기인가?", content: analysis.why_popular, color: "#f59e0b" },
        { icon: Target, title: "핵심 성공요인", content: analysis.key_success_factors, color: "#6366f1" },
        { icon: Users, title: "예상 시청자", content: analysis.target_audience, color: "#8b5cf6" },
        { icon: Film, title: "유사 콘텐츠", content: analysis.similar_contents, color: "#10b981" },
        { icon: TrendingUp, title: "24시간 예측", content: analysis.prediction_24h, color: "#ef4444" },
        { icon: Lightbulb, title: "개선 아이디어", content: analysis.improvement_ideas, color: "#f97316" },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Video Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex gap-6">
        <div className="relative w-80 h-44 rounded-xl overflow-hidden flex-shrink-0" style={{ background: "var(--bg-secondary)" }}>
          {video.thumbnail ? (
            <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">No Image</div>
          )}
          {video.isShort && (
            <span className="absolute top-2 left-2 px-2 py-1 text-xs font-bold bg-red-500 text-white rounded">SHORT</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-extrabold leading-tight" style={{ color: "var(--text-primary)" }}>
            {video.title}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            {video.channel?.title || "Unknown Channel"}
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
            <span className="flex items-center gap-1"><Eye size={14} /> {formatViews(video.views)}</span>
            <span className="flex items-center gap-1"><ThumbsUp size={14} /> {formatViews(video.likes)}</span>
            <span className="flex items-center gap-1"><MessageSquare size={14} /> {formatViews(video.comments)}</span>
            <span className="flex items-center gap-1"><Clock size={14} /> {formatDate(video.publish_time)}</span>
          </div>
        </div>
      </motion.div>

      {/* Prediction + Ranking History Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* XGBoost Prediction Card */}
        <motion.div className="glass-card p-5" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={18} style={{ color: "#6366f1" }} />
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              🤖 XGBoost 24시간 조회수 예측
            </h2>
          </div>
          {prediction ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-xl" style={{ background: "var(--bg-secondary)" }}>
                  <p className="text-[10px] uppercase font-bold" style={{ color: "var(--text-secondary)" }}>현재 조회수</p>
                  <p className="text-xl font-bold text-indigo-400">{formatViews(prediction.current_views)}</p>
                </div>
                <div className="p-3 rounded-xl" style={{ background: "var(--bg-secondary)" }}>
                  <p className="text-[10px] uppercase font-bold" style={{ color: "var(--text-secondary)" }}>24시간 예측 조회수</p>
                  <p className="text-xl font-bold text-emerald-400">{formatViews(prediction.predicted_views_24h)}</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-secondary)" }}>
                <span>예측 모델: <span className="font-semibold text-violet-400">{prediction.model_type === "xgboost" ? "XGBoost Regressor" : "Math Growth Curve"}</span></span>
                <span>신뢰도: <span className={`font-bold ${prediction.confidence >= 0.7 ? "text-emerald-400" : "text-amber-400"}`}>{(prediction.confidence * 100).toFixed(0)}%</span></span>
              </div>
              {/* Confidence Bar */}
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${prediction.confidence * 100}%` }} />
              </div>
            </div>
          ) : (
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>예측 데이터를 가져오지 못했습니다.</p>
          )}
        </motion.div>

        {/* Ranking History Chart */}
        <motion.div className="glass-card p-5" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} style={{ color: "#8b5cf6" }} />
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              📈 랭킹 &amp; Virality Score 시계열 히스토리
            </h2>
          </div>
          {history.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="recorded_at" tick={{ fontSize: 9, fill: "var(--text-secondary)" }} tickFormatter={(v) => new Date(v).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "var(--text-secondary)" }} />
                <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 11 }} />
                <Area type="monotone" dataKey="virality_score" stroke="#8b5cf6" fillOpacity={1} fill="url(#scoreGrad)" name="Virality Score" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>시계열 데이터를 수집 중입니다.</p>
          )}
        </motion.div>
      </div>

      {/* AI Analysis Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Brain size={20} style={{ color: "#6366f1" }} />
            <h2 className="text-lg font-bold gradient-text">AI 인공지능 분석 리포트</h2>
          </div>
          {!analysis && (
            <button
              onClick={handleTriggerAI}
              disabled={loadingAI}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white disabled:opacity-50"
              style={{ background: "var(--gradient-primary)" }}
            >
              <Zap size={14} className={loadingAI ? "animate-spin" : ""} />
              {loadingAI ? "Qwen 35B 추론 중..." : "AI 분석 실행 (Qwen 35B)"}
            </button>
          )}
        </div>

        {analysis ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {aiSections.map((section, i) => (
              <motion.div
                key={section.title}
                className="glass-card p-5"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg" style={{ background: `${section.color}20`, color: section.color }}>
                    <section.icon size={16} />
                  </div>
                  <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{section.title}</h3>
                </div>
                <p className="text-xs leading-relaxed whitespace-pre-line" style={{ color: "var(--text-secondary)" }}>
                  {section.content}
                </p>
              </motion.div>
            ))}
          </div>
        ) : !loadingAI ? (
          <div className="glass-card p-8 text-center" style={{ color: "var(--text-secondary)" }}>
            <Brain size={36} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">아직 AI 분석이 수행되지 않았습니다.</p>
            <p className="text-xs mt-1">위의 &quot;AI 분석 실행&quot; 버튼을 클릭하면 로컬 Qwen 35B 모델이 자동으로 이 비디오를 분석합니다.</p>
          </div>
        ) : (
          <div className="glass-card p-8 text-center" style={{ color: "var(--text-secondary)" }}>
            <div className="animate-spin mx-auto mb-3 w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full" />
            <p className="text-sm">Qwen AgentWorld 35B 모델에서 분석 중입니다...</p>
            <p className="text-xs mt-1">로컬 추론에 약 10~30초 소요됩니다.</p>
          </div>
        )}

        {analysis && (
          <p className="text-[10px] mt-3 text-right" style={{ color: "var(--text-secondary)" }}>
            분석 생성일: {formatDate(analysis.analyzed_at)} • 모델: Qwen AgentWorld 35B A3B UD (로컬 LM Studio)
          </p>
        )}
      </div>
    </div>
  );
}

export default function VideoDetailPage() {
  return (
    <Suspense fallback={
      <div className="space-y-4">
        <div className="skeleton h-8 w-1/2 rounded" />
        <div className="skeleton h-64 w-full rounded-xl" />
        <div className="skeleton h-48 w-full rounded-xl" />
      </div>
    }>
      <VideoDetailContent />
    </Suspense>
  );
}
