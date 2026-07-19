export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

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
  const res = await fetch(
    `${API_BASE_URL}/ranking?country_code=${countryCode}&is_shorts=${isShorts}&period=${period}&limit=${limit}`
  );
  if (!res.ok) return [];
  return res.json();
};

export const fetchShortsRanking = async (
  countryCode: string,
  period: string = "daily",
  limit: number = 50
): Promise<VideoRank[]> => {
  const res = await fetch(
    `${API_BASE_URL}/shorts?country_code=${countryCode}&period=${period}&limit=${limit}`
  );
  if (!res.ok) return [];
  return res.json();
};

export const fetchLongformRanking = async (
  countryCode: string,
  period: string = "daily",
  limit: number = 50
): Promise<VideoRank[]> => {
  const res = await fetch(
    `${API_BASE_URL}/longform?country_code=${countryCode}&period=${period}&limit=${limit}`
  );
  if (!res.ok) return [];
  return res.json();
};

export const fetchVideoDetail = async (videoId: string): Promise<Video | null> => {
  const res = await fetch(`${API_BASE_URL}/videos/${videoId}`);
  if (!res.ok) return null;
  return res.json();
};

export const fetchHiddenGems = async (countryCode: string, isShorts?: boolean, limit: number = 20): Promise<Video[]> => {
  let url = `${API_BASE_URL}/videos/hidden-gems?country_code=${countryCode}&limit=${limit}`;
  if (isShorts !== undefined) {
    url += `&is_shorts=${isShorts}`;
  }
  const res = await fetch(url);
  if (!res.ok) return [];
  return res.json();
};

export const fetchCreatorRadar = async (countryCode: string, limit: number = 20): Promise<Channel[]> => {
  const res = await fetch(`${API_BASE_URL}/channels/creator-radar?country_code=${countryCode}&limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
};

export const fetchTrendRadar = async (countryCode: string, hours: number = 24, limit: number = 50): Promise<Video[]> => {
  const res = await fetch(`${API_BASE_URL}/trending?country_code=${countryCode}&hours=${hours}&limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
};

export const fetchCountryDiff = async (videoId: string): Promise<any[]> => {
  const res = await fetch(`${API_BASE_URL}/compare?video_id=${videoId}`);
  if (!res.ok) return [];
  return res.json();
};

export const fetchRankingHistory = async (videoId: string, limit: number = 30): Promise<RankingHistory[]> => {
  const res = await fetch(`${API_BASE_URL}/ranking/history/${videoId}?limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
};

export const fetchAIAnalysis = async (videoId: string): Promise<AIAnalysis | null> => {
  const res = await fetch(`${API_BASE_URL}/ai/${videoId}`);
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return res.json();
};

export const triggerAIAnalysis = async (videoId: string): Promise<AIAnalysis | null> => {
  const res = await fetch(`${API_BASE_URL}/ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId })
  });
  if (!res.ok) return null;
  return res.json();
};

export const fetchAlerts = async (limit: number = 10): Promise<Alert[]> => {
  const res = await fetch(`${API_BASE_URL}/alerts?limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
};

export const markAlertAsRead = async (alertId: number): Promise<Alert | null> => {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}/read`, { method: "POST" });
  if (!res.ok) return null;
  return res.json();
};

export interface Prediction {
  video_id: string;
  current_views: number;
  predicted_views_24h: number;
  confidence: number;
  model_type: string;
}

export const fetchPrediction = async (videoId: string): Promise<Prediction | null> => {
  const res = await fetch(`${API_BASE_URL}/prediction/${videoId}`);
  if (!res.ok) return null;
  return res.json();
};

export const triggerCrawlerManual = async (): Promise<{ status: string; message: string } | null> => {
  const res = await fetch(`${API_BASE_URL}/admin/run-crawler`, { method: "POST" });
  if (!res.ok) return null;
  return res.json();
};

export const triggerRankingManual = async (): Promise<{ status: string; message: string } | null> => {
  const res = await fetch(`${API_BASE_URL}/admin/run-ranking`, { method: "POST" });
  if (!res.ok) return null;
  return res.json();
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
  const res = await fetch(`${API_BASE_URL}/admin/status`);
  if (!res.ok) return null;
  return res.json();
};



