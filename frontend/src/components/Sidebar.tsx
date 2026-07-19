"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Trophy,
  Search,
  TrendingUp,
  Gem,
  Radar,
  Users,
  Bell,
  Settings,
  Moon,
  Sun,
  Menu,
  X,
  BarChart3,
  Zap,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "대시보드", icon: LayoutDashboard },
  { href: "/ranking", label: "랭킹", icon: Trophy },
  { href: "/trending", label: "트렌드 레이더", icon: TrendingUp },
  { href: "/hidden-gems", label: "숨은 보석", icon: Gem },
  { href: "/creator-radar", label: "크리에이터 레이더", icon: Users },
  { href: "/search", label: "검색", icon: Search },
  { href: "/compare", label: "국가별 비교", icon: BarChart3 },
  { href: "/alerts", label: "알림", icon: Bell },
  { href: "/settings", label: "설정", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  };

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="fixed top-4 left-4 z-50 p-2 rounded-lg lg:hidden"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}
        onClick={() => setMobileOpen(true)}
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      {/* Overlay for mobile */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-300
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        style={{
          width: collapsed ? 72 : 240,
          background: "var(--bg-secondary)",
          borderRight: "1px solid var(--border-color)",
        }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4" style={{ height: 64 }}>
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div
                className="flex items-center justify-center w-8 h-8 rounded-lg"
                style={{ background: "var(--gradient-primary)" }}
              >
                <Zap size={16} color="white" />
              </div>
              <span className="gradient-text font-bold text-sm tracking-tight">
                유튜브 인텔리전스
              </span>
            </div>
          )}
          {collapsed && (
            <div
              className="flex items-center justify-center w-8 h-8 rounded-lg mx-auto"
              style={{ background: "var(--gradient-primary)" }}
            >
              <Zap size={16} color="white" />
            </div>
          )}

          {/* Mobile close */}
          <button className="lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu">
            <X size={18} style={{ color: "var(--text-secondary)" }} />
          </button>

          {/* Desktop collapse toggle */}
          <button
            className="hidden lg:block"
            onClick={() => setCollapsed(!collapsed)}
            aria-label="Toggle sidebar"
          >
            <Menu size={16} style={{ color: "var(--text-secondary)" }} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 overflow-y-auto">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`nav-link ${isActive ? "active" : ""}`}
                    onClick={() => setMobileOpen(false)}
                    title={item.label}
                  >
                    <item.icon size={18} />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer / Theme toggle */}
        <div className="p-3 border-t" style={{ borderColor: "var(--border-color)" }}>
          <button
            className="nav-link w-full"
            onClick={toggleTheme}
            title={theme === "dark" ? "라이트 모드" : "다크 모드"}
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            {!collapsed && <span>{theme === "dark" ? "라이트 모드" : "다크 모드"}</span>}
          </button>
        </div>
      </motion.aside>
    </>
  );
}
