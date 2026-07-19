"use client";

import React from "react";
import { COUNTRIES, type CountryCode } from "@/lib/constants";

interface CountrySelectorProps {
  selected: CountryCode;
  onSelect: (code: CountryCode) => void;
  excludeCodes?: string[];
}

export default function CountrySelector({ selected, onSelect, excludeCodes = [] }: CountrySelectorProps) {
  const filteredCountries = COUNTRIES.filter((c) => !excludeCodes.includes(c.code));

  return (
    <div className="flex flex-wrap gap-2">
      {filteredCountries.map((c) => (
        <button
          key={c.code}
          className={`country-pill ${selected === c.code ? "active" : ""}`}
          onClick={() => onSelect(c.code as CountryCode)}
        >
          <span>{c.flag}</span>
          <span>{c.code}</span>
        </button>
      ))}
    </div>
  );
}
