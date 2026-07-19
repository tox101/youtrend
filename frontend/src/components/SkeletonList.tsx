"use client";

import React from "react";

interface SkeletonProps {
  count?: number;
}

export function SkeletonCard() {
  return (
    <div className="glass-card p-4 flex items-center gap-4" style={{ pointerEvents: "none" }}>
      <div className="skeleton w-8 h-8 rounded-lg flex-shrink-0" />
      <div className="skeleton w-24 h-14 rounded-lg flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-4 w-3/4 rounded" />
        <div className="skeleton h-3 w-1/2 rounded" />
        <div className="skeleton h-3 w-1/3 rounded" />
      </div>
      <div className="flex-shrink-0 space-y-2">
        <div className="skeleton h-8 w-16 rounded-lg" />
        <div className="skeleton h-1 w-20 rounded" />
      </div>
    </div>
  );
}

export default function SkeletonList({ count = 10 }: SkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
