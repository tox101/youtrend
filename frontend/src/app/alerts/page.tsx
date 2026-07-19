"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bell, Eye } from "lucide-react";
import { fetchAlerts, markAlertAsRead, type Alert } from "@/lib/api";
import { formatDate } from "@/lib/constants";
import SkeletonList from "@/components/SkeletonList";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchAlerts(20);
      setAlerts(data);
    } catch {
      setAlerts([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleRead = async (id: number) => {
    try {
      await markAlertAsRead(id);
      // Update local state to avoid refetching
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === id ? { ...a, is_read: true } : a))
      );
    } catch (err) {
      // Graceful error
    }
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold gradient-text">알림</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Virality Score 폭발적 증가 및 Hidden Gem 자동 감지 알림
          </p>
        </div>
      </motion.div>

      {loading ? (
        <SkeletonList count={4} />
      ) : alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert, i) => (
            <motion.div
              key={alert.alert_id}
              className={`glass-card p-4 flex justify-between items-center border-l-4 ${
                alert.is_read ? "opacity-70 border-l-zinc-700" : "border-l-indigo-500"
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <div>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-zinc-800 mr-2" style={{ color: "var(--text-secondary)" }}>
                  {alert.type}
                </span>
                <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
                  {formatDate(alert.created_at)}
                </span>
                <p className="text-sm font-medium mt-1.5" style={{ color: "var(--text-primary)" }}>
                  {alert.message}
                </p>
              </div>
              {!alert.is_read && (
                <button
                  onClick={() => handleRead(alert.alert_id)}
                  className="px-3.5 py-1.5 rounded-lg border text-xs font-semibold hover:bg-zinc-800 transition"
                  style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                >
                  읽음 표시
                </button>
              )}
            </motion.div>
          ))}
        </div>
      ) : (
        <motion.div className="glass-card p-12 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Bell size={48} className="mx-auto mb-4 opacity-30" style={{ color: "var(--text-secondary)" }} />
          <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>알림 메시지가 없습니다</p>
          <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>Virality Score 95 이상 또는 랭킹 급상승 조건 충족 시 실시간으로 플래깅됩니다.</p>
        </motion.div>
      )}
    </div>
  );
}
