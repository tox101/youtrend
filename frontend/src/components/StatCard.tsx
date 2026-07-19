"use client";

import React from "react";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color: string;
  delay?: number;
}

export default function StatCard({ title, value, subtitle, icon: Icon, color, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      className="glass-card p-5"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.4 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
            {title}
          </p>
          <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs mt-1" style={{ color }}>
              {subtitle}
            </p>
          )}
        </div>
        <div
          className="flex items-center justify-center w-10 h-10 rounded-xl"
          style={{ background: `${color}20`, color }}
        >
          <Icon size={20} />
        </div>
      </div>
    </motion.div>
  );
}
