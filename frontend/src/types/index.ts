export interface LearnerProfile {
  learner_id: string;
  name: string;
  email: string;
  current_role: string;
  interests: string[];
  self_reported_skills: Record<string, number>;
  previous_learning: string[];
  weekly_hours: number;
  timeline_months: number;
  content_preferences: string[];
  interaction_preferences?: Record<string, any>;
}

export interface GoalState {
  goal_id: string;
  target_role: string;
  timeline_months: number;
  weekly_hours: number;
  target_proficiency_by_skill: Record<string, number>;
  active: boolean;
}

export interface GoalCatalogItem {
  goal_id: string;
  title: string;
  target_role: string;
  description: string;
  recommended_weekly_hours: number;
  recommended_timeline_months: number;
  target_proficiency_by_skill: Record<string, number>;
}

export interface AssessmentItem {
  item_id: string;
  skill_id: string;
  concept_id: string;
  difficulty: string;
  question_type: string;
  prompt: string;
  code_snippet?: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  evidence_weight: number;
}

export interface AssessmentAttempt {
  attempt_id: string;
  learner_id: string;
  goal_id: string;
  item_id: string;
  skill_id: string;
  answer: string;
  correct: boolean;
}

export interface KnowledgeState {
  skill_id: string;
  skill_name: string;
  self_reported_score: number;
  demonstrated_score: number;
  target_score: number;
  status: 'adequate' | 'needs_improvement' | 'weak' | 'unassessed';
  attempts_count: number;
  success_rate: number;
}

export interface SkillGapItem {
  skill_id: string;
  skill_name: string;
  self_reported: number;
  demonstrated: number;
  target: number;
  gap: number;
  status: string;
  is_prerequisite_bottleneck: boolean;
}

export interface GapReport {
  goal_id: string;
  target_role: string;
  comparison_data: SkillGapItem[];
  weak_skills: string[];
  needs_improvement_skills: string[];
  adequate_skills: string[];
  unresolved_prerequisites: string[];
}

export interface LearningRecommendation {
  resource_id: string;
  title: string;
  resource_type: string;
  provider: string;
  url: string;
  relevance_score: number;
  matched_skills: string[];
  reason: string;
  estimated_effort_hours: number;
  prerequisite_status: string;
  priority: number;
}

export interface Milestone {
  milestone_id: string;
  title: string;
  description: string;
  success_criteria: string[];
  assessment_ids: string[];
  project_ids: string[];
  completed: boolean;
}

export interface Stage {
  stage_id: string;
  title: string;
  objective: string;
  prerequisite_stage_ids: string[];
  estimated_hours: number;
  milestone: Milestone;
  skill_targets: string[];
  resources: LearningRecommendation[];
  completion_status: 'not_started' | 'in_progress' | 'completed';
  rationale: string;
}

export interface Roadmap {
  roadmap_id: string;
  learner_id: string;
  goal_id: string;
  version: number;
  generated_at: string;
  generation_reason: string;
  total_estimated_hours: number;
  stages: Stage[];
  rationale: string[];
  adaptation_diff?: Record<string, string>;
}

export interface DashboardData {
  learner_name: string;
  target_role: string;
  timeline_months: number;
  weekly_hours: number;
  progress_percentage: number;
  skills_assessed_count: number;
  weak_prerequisites_count: number;
  streak_days: number;
  current_xp: number;
  knowledge_states: KnowledgeState[];
  gap_report?: GapReport;
  current_roadmap?: Roadmap;
  chat_history: Array<{ role: string; content: string }>;
}

export interface TutorResponse {
  reply: string;
  source: string;
  model: string;
  is_adaptation: boolean;
  adaptation_diff?: Record<string, string>;
}
