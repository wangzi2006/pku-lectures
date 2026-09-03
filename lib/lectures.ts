import topicsConfig from '@/config/topics.json';

export type Lecture = {
  id: string;
  status: 'pending' | 'published' | 'rejected' | 'maybe';
  title: string;
  titleZh?: string | null;
  speaker: string;
  startAt: string;
  endAt?: string | null;
  location: string;
  campus: '校内' | '校外' | '线上';
  distanceKm?: number | null;
  topic: string;
  subtopics: string[];
  flags: string[];
  summary: string;
  reason: string;
  sourceName: string;
  sourceUrl: string;
  registrationUrl?: string | null;
  verifiedAt: string;
  qualityScore?: number;
  undergradScore?: number;
  confidence?: number;
  reviewNotes?: string;
  region?: string;
};

export type LectureSource = {
  id: string;
  name: string;
  url: string;
  kind: 'event-list' | 'mixed' | 'review-archive' | 'wechat';
  tier: number;
  topics: string[];
  enabled: boolean;
  reviewMining: boolean;
  notes: string;
  ownerApproved?: boolean;
  transport?: string;
  feedId?: string;
};

const aliases = topicsConfig.aliases as Record<string, string[]>;
export const topicOrder = ['全部', ...topicsConfig.order];

export function lectureTopics(lecture: Lecture) {
  const raw = [lecture.topic, ...lecture.subtopics];
  const expanded = raw.flatMap((value) =>
    aliases[value] || value.split(/[/、，,]/).map((part) => part.trim()),
  );
  return [...new Set(expanded.filter((value) => topicsConfig.order.includes(value)))];
}

export function formatLectureDate(iso: string) {
  const date = new Date(iso);
  const weekday = new Intl.DateTimeFormat('zh-CN', {
    weekday: 'short',
    timeZone: 'Asia/Shanghai',
  }).format(date);
  const month = new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    timeZone: 'Asia/Shanghai',
  }).format(date);
  const day = new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    timeZone: 'Asia/Shanghai',
  }).format(date);
  const time = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Shanghai',
  }).format(date);
  return { day, month, time, weekday };
}

export function distanceLabel(lecture: Lecture) {
  if (lecture.campus === '线上') return '线上';
  if (lecture.region) return lecture.region;
  if (lecture.campus === '校内') return '北大校内';
  return lecture.distanceKm == null
    ? '校外 · 距离待核验'
    : `校外约 ${lecture.distanceKm.toFixed(1)} km`;
}
