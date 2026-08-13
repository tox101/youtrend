// ─── API URL — localStorage 우선, 없으면 env, 없으면 localhost fallback ──────
export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const saved = window.localStorage.getItem("NEXT_PUBLIC_API_URL");
    if (saved) return saved;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
}

// 하위 호환을 위해 상수도 유지
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// ─── 터널 URL 자동 복구: localhost를 통해 현재 활성 터널 URL을 조회 ────
async function discoverTunnelUrl(): Promise<string | null> {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 3000);
    const res = await fetch("http://localhost:8000/api/admin/tunnel-url", {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(id);
    if (!res.ok) return null;
    const data = await res.json();
    if (data.api_url) {
      // 새 터널 URL을 localStorage에 저장하여 즉시 반영
      if (typeof window !== "undefined") {
        window.localStorage.setItem("NEXT_PUBLIC_API_URL", data.api_url);
      }
      return data.api_url;
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Resilient Fetch: 자가 치유(Self-Healing) + 터널 URL 자동 복구 ────
async function resilientFetch(path: string, options?: RequestInit): Promise<Response> {
  const urlsToTry: string[] = [];
  
  // 1순위: 현재 브라우저 상태 (localStorage 또는 환경 변수 기본값)
  urlsToTry.push(getApiBaseUrl());
  
  // 2순위: 환경 변수에 정의된 최신 빌드 타임 URL (localStorage가 만료되었을 때를 대비)
  if (process.env.NEXT_PUBLIC_API_URL && urlsToTry.indexOf(process.env.NEXT_PUBLIC_API_URL) === -1) {
    urlsToTry.push(process.env.NEXT_PUBLIC_API_URL);
  }
  
  // 3순위: 순수 로컬 개발망 주소
  const localhostUrl = "http://localhost:8000/api";
  if (urlsToTry.indexOf(localhostUrl) === -1) {
    urlsToTry.push(localhostUrl);
  }

  let lastError = null;

  // Phase 1: 기존 URL 목록으로 시도
  for (const baseUrl of urlsToTry) {
    const url = `${baseUrl}${path}`;
    try {
      const itemController = new AbortController();
      const id = setTimeout(() => itemController.abort(), 5000);
      const res = await fetch(url, { 
        cache: "no-store", 
        ...options,
        signal: itemController.signal 
      });
      clearTimeout(id);
      
      const contentType = res.headers.get("content-type") || "";
      
      if (res.ok && contentType.includes("application/json")) {
        // 성공 시, 현재 연결 성공한 Base URL을 localStorage에 저장하여 자가 보정
        if (typeof window !== "undefined") {
          window.localStorage.setItem("NEXT_PUBLIC_API_URL", baseUrl);
        }
        return res;
      } else {
        lastError = new Error(`Invalid response content-type: ${contentType}`);
      }
    } catch (err) {
      lastError = err;
    }
  }

  // Phase 2: 모든 URL 실패 → localhost를 통해 최신 터널 URL 자동 발견
  const discoveredUrl = await discoverTunnelUrl();
  if (discoveredUrl && urlsToTry.indexOf(discoveredUrl) === -1) {
    try {
      const itemController = new AbortController();
      const id = setTimeout(() => itemController.abort(), 5000);
      const res = await fetch(`${discoveredUrl}${path}`, {
        cache: "no-store",
        ...options,
        signal: itemController.signal,
      });
      clearTimeout(id);

      const contentType = res.headers.get("content-type") || "";
      if (res.ok && contentType.includes("application/json")) {
        if (typeof window !== "undefined") {
          window.localStorage.setItem("NEXT_PUBLIC_API_URL", discoveredUrl);
        }
        return res;
      }
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error("All API endpoints failed");
}


export interface Channel {
  channel_id: string;
  title: string;
  description?: string;
  custom_url?: string;
  thumbnail_url?: string;
  view_count: number;
  subscriber_count: number;
  video_count: number;
  country_code: string;
  last_updated: string;
}

export interface Video {
  video_id: string;
  title: string;
  description?: string;
  country_code: string;
  language?: string;
  publish_time: string;
  duration?: string;
  thumbnail?: string;
  tags?: string[];
  category?: string;
  isShort: boolean;
  views: number;
  likes: number;
  comments: number;
  subscriber: number;
  last_updated: string;
  channel?: Channel;
  target_age?: string;
  target_gender?: string;
  is_channel?: boolean;
}

export interface VideoRank {
  id: number;
  video_id: string;
  rank: number;
  virality_score: number;
  is_shorts: boolean;
  period: string;
  country_code: string;
  rank_date: string;
  updated_at: string;
  video: Video;
}

export interface RankingHistory {
  id: number;
  video_id: string;
  rank: number;
  virality_score: number;
  views: number;
  likes: number;
  comments: number;
  country_code: string;
  recorded_at: string;
}

export interface AIAnalysis {
  video_id: string;
  why_popular: string;
  key_success_factors: string;
  target_audience: string;
  similar_contents: string;
  prediction_24h: string;
  improvement_ideas: string;
  analyzed_at: string;
}

export interface Alert {
  alert_id: number;
  video_id: string;
  type: string;
  message: string;
  is_read: boolean;
  created_at: string;
  video: Video;
}


export const fetchRanking = async (
  countryCode: string,
  isShorts: boolean,
  period: string = "daily",
  limit: number = 50
): Promise<VideoRank[]> => {
  try {
    const res = await resilientFetch(`/ranking?country_code=${countryCode}&is_shorts=${isShorts}&period=${period}&limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchShortsRanking = async (
  countryCode: string,
  period: string = "daily",
  limit: number = 50
): Promise<VideoRank[]> => {
  try {
    const res = await resilientFetch(`/shorts?country_code=${countryCode}&period=${period}&limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchLongformRanking = async (
  countryCode: string,
  period: string = "daily",
  limit: number = 50
): Promise<VideoRank[]> => {
  try {
    const res = await resilientFetch(`/longform?country_code=${countryCode}&period=${period}&limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchVideoDetail = async (videoId: string): Promise<Video | null> => {
  try {
    const res = await resilientFetch(`/videos/${videoId}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export interface SearchFilters {
  q?: string;
  target_age?: string;
  target_gender?: string;
  country_code?: string;
  category?: string;
  duration?: string;
  publish_date?: string;
  features?: string;
  sort_by?: string;
  limit?: number;
}

export const fetchFilteredVideos = async (filters: SearchFilters): Promise<Video[]> => {
  const params = new URLSearchParams();
  if (filters.q) params.append("q", filters.q);
  if (filters.target_age) params.append("target_age", filters.target_age);
  if (filters.target_gender) params.append("target_gender", filters.target_gender);
  if (filters.country_code) params.append("country_code", filters.country_code);
  if (filters.category) params.append("category", filters.category);
  if (filters.duration) params.append("duration", filters.duration);
  if (filters.publish_date) params.append("publish_date", filters.publish_date);
  if (filters.features) params.append("features", filters.features);
  if (filters.sort_by) params.append("sort_by", filters.sort_by);
  if (filters.limit) params.append("limit", String(filters.limit));
  try {
    const res = await resilientFetch(`/videos?${params.toString()}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchHiddenGems = async (countryCode: string, isShorts?: boolean, limit: number = 20): Promise<Video[]> => {
  let path = `/videos/hidden-gems?country_code=${countryCode}&limit=${limit}`;
  if (isShorts !== undefined) path += `&is_shorts=${isShorts}`;
  try {
    const res = await resilientFetch(path);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchCreatorRadar = async (countryCode: string, limit: number = 20): Promise<Channel[]> => {
  try {
    const res = await resilientFetch(`/channels/creator-radar?country_code=${countryCode}&limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchTrendRadar = async (countryCode: string, hours: number = 24, limit: number = 50): Promise<Video[]> => {
  try {
    const res = await resilientFetch(`/trending?country_code=${countryCode}&hours=${hours}&limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchCountryDiff = async (videoId: string): Promise<any[]> => {
  try {
    const res = await resilientFetch(`/compare?video_id=${videoId}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchRankingHistory = async (videoId: string, limit: number = 30): Promise<RankingHistory[]> => {
  try {
    const res = await resilientFetch(`/ranking/history/${videoId}?limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const fetchAIAnalysis = async (videoId: string): Promise<AIAnalysis | null> => {
  try {
    const res = await resilientFetch(`/ai/${videoId}`);
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export const triggerAIAnalysis = async (videoId: string): Promise<AIAnalysis | null> => {
  try {
    const res = await resilientFetch(`/ai`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id: videoId })
    });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export const fetchAlerts = async (limit: number = 10): Promise<Alert[]> => {
  try {
    const res = await resilientFetch(`/alerts?limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
};

export const markAlertAsRead = async (alertId: number): Promise<Alert | null> => {
  try {
    const res = await resilientFetch(`/alerts/${alertId}/read`, { method: "POST" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export interface Prediction {
  video_id: string;
  current_views: number;
  predicted_views_24h: number;
  confidence: number;
  model_type: string;
}

export const fetchPrediction = async (videoId: string): Promise<Prediction | null> => {
  try {
    const res = await resilientFetch(`/prediction/${videoId}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export const triggerCrawlerManual = async (): Promise<{ status: string; message: string } | null> => {
  try {
    const res = await resilientFetch(`/admin/run-crawler`, { method: "POST" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export const triggerRankingManual = async (): Promise<{ status: string; message: string } | null> => {
  try {
    const res = await resilientFetch(`/admin/run-ranking`, { method: "POST" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

export interface SystemStatus {
  status: string;
  database_health: string;
  total_videos: number;
  total_channels: number;
  latest_rank_update: string | null;
  scheduler_interval_minutes: number;
}

export const fetchSystemStatus = async (): Promise<SystemStatus | null> => {
  try {
    const res = await resilientFetch(`/admin/status`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};



