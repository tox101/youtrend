"use client";

import React from "react";
import { PERIODS } from "@/lib/constants";

interface PeriodToggleProps {
  selected: string;
  onSelect: (period: string) => void;
}

export default function PeriodToggle({ selected, onSelect }: PeriodToggleProps) {
  return (
    <div className="period-toggle">
      {PERIODS.map((p) => (
        <button
          key={p.value}
          className={selected === p.value ? "active" : ""}
          onClick={() => onSelect(p.value)}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
