"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, ShieldAlert } from "lucide-react";
import CountrySelector from "@/components/CountrySelector";
import SkeletonList from "@/components/SkeletonList";
import { fetchCreatorRadar, type Channel } from "@/lib/api";
import { formatViews, type CountryCode } from "@/lib/constants";

export default function CreatorRadarPage() {
  const [country, setCountry] = useState<CountryCode>("KR");
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchCreatorRadar(country, 30);
        setChannels(data);
      } catch {
        setChannels([]);
      }
      setLoading(false);
    };
    load();
  }, [country]);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-extrabold gradient-text">크리에이터 레이더 📡</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          구독자 수 대비 비디오 평균 조회수 폭발력이 높은 성장형 크리에이터 추천
        </p>
      </motion.div>

      <CountrySelector selected={country} onSelect={setCountry} />

      {loading ? (
        <SkeletonList count={6} />
      ) : channels.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {channels.map((channel, i) => {
            const avgViews = channel.video_count > 0 ? Math.round(channel.view_count / channel.video_count) : 0;
            return (
              <motion.div
                key={channel.channel_id}
                className="glass-card p-5 flex flex-col justify-between"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
              >
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-12 h-12 rounded-full overflow-hidden flex-shrink-0" style={{ background: "var(--bg-secondary)" }}>
                      {channel.thumbnail_url ? (
                        <img src={channel.thumbnail_url} alt={channel.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-lg font-bold">
                          {channel.title.charAt(0)}
                        </div>
                      )}
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                        {channel.title}
                      </h3>
                      <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        {channel.custom_url || `@${channel.channel_id}`}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs line-clamp-2 mb-4" style={{ color: "var(--text-secondary)" }}>
                    {channel.description || "채널 설명이 제공되지 않았습니다."}
                  </p>
                </div>
                <div className="border-t pt-3" style={{ borderColor: "var(--border-color)" }}>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-[10px]" style={{ color: "var(--text-secondary)" }}>구독자</p>
                      <p className="text-xs font-bold text-indigo-400">{formatViews(channel.subscriber_count)}</p>
                    </div>
                    <div>
                      <p className="text-[10px]" style={{ color: "var(--text-secondary)" }}>총 조회수</p>
                      <p className="text-xs font-bold text-violet-400">{formatViews(channel.view_count)}</p>
                    </div>
                    <div>
                      <p className="text-[10px]" style={{ color: "var(--text-secondary)" }}>비디오당 평균</p>
                      <p className="text-xs font-bold text-amber-400">{formatViews(avgViews)}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <motion.div className="glass-card p-12 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Users size={48} className="mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>급상승 크리에이터가 없습니다</p>
          <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>구독자 10만 이하의 급성장 크리에이터가 발견되면 노출됩니다.</p>
        </motion.div>
      )}
    </div>
  );
}
