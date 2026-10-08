import {
  LearnerProfile,
  GoalState,
  GoalCatalogItem,
  AssessmentItem,
  AssessmentAttempt,
  KnowledgeState,
  GapReport,
  LearningRecommendation,
  Roadmap,
  DashboardData,
  TutorResponse
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // System Health
  getHealth: () => request<{ status: string; gemini_model: string }>('/api/health'),

  // Profile Baseline
  getProfile: () => request<LearnerProfile>('/api/profile'),
  updateProfile: (profile: Partial<LearnerProfile>) =>
    request<LearnerProfile>('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(profile),
    }),

  // Goal Discovery
  getGoal: () => request<GoalState | null>('/api/goal'),
  getGoalCatalog: () => request<GoalCatalogItem[]>('/api/goal/catalog'),
  extractGoal: (user_prompt: string) =>
    request<{
      extracted: Record<string, any>;
      goal_state: GoalState;
      source: string;
      model: string;
      error?: string;
    }>('/api/goal/extract', {
      method: 'POST',
      body: JSON.stringify({ user_prompt }),
    }),
  selectGoal: (goal_id: string, target_role?: string, timeline_months?: number, weekly_hours?: number) =>
    request<GoalState>('/api/goal/select', {
      method: 'POST',
      body: JSON.stringify({ goal_id, target_role, timeline_months, weekly_hours }),
    }),

  // Skill Graph
  getSkillGraph: (goal_id: string) => request<any>(`/api/skill-graph/${goal_id}`),

  // Diagnostic Assessment
  getAssessment: () => request<AssessmentItem[]>('/api/assessment'),
  submitAttempt: (item_id: string, answer: string) =>
    request<AssessmentAttempt>('/api/assessment/attempt', {
      method: 'POST',
      body: JSON.stringify({ item_id, answer }),
    }),
  completeAssessment: (attempts?: Array<{ item_id: string; answer: string }>) =>
    request<{
      status: string;
      scored_attempts_count: number;
      knowledge_states: KnowledgeState[];
      gap_report: GapReport;
      roadmap_v1: Roadmap;
    }>('/api/assessment/complete', {
      method: 'POST',
      body: JSON.stringify({ attempts }),
    }),

  // Knowledge & Gaps
  getKnowledge: () => request<KnowledgeState[]>('/api/knowledge'),
  getGaps: () => request<GapReport | null>('/api/gaps'),
  getRecommendations: (skill_id?: string) =>
    request<LearningRecommendation[]>(
      skill_id ? `/api/recommendations?skill_id=${encodeURIComponent(skill_id)}` : '/api/recommendations'
    ),

  // Roadmap
  getRoadmap: (version?: number) =>
    request<Roadmap | null>(version ? `/api/roadmap?version=${version}` : '/api/roadmap'),
  getRoadmapVersions: () => request<Record<number, Roadmap>>('/api/roadmap/versions'),
  generateRoadmap: (goal_id?: string, generation_reason?: string) =>
    request<Roadmap>('/api/roadmap/generate', {
      method: 'POST',
      body: JSON.stringify({ goal_id, generation_reason }),
    }),

  // AI Tutor & Feedback
  tutorChat: (query: string) =>
    request<TutorResponse>('/api/tutor/chat', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
  submitFeedback: (message: string, type?: string, target_id?: string) =>
    request<Roadmap>('/api/feedback', {
      method: 'POST',
      body: JSON.stringify({ message, type, target_id }),
    }),

  // Dashboard Telemetry
  getDashboard: () => request<DashboardData>('/api/dashboard'),

  // Presets & Reset
  loadPreset: (preset_id: string) =>
    request<{ status: string; preset: string; profile: LearnerProfile; goal_state: GoalState }>(
      `/api/presets/load/${preset_id}`,
      { method: 'POST' }
    ),
  resetState: () => request<{ status: string; message: string }>('/api/presets/reset', { method: 'POST' }),
};
