// Enums
export type DealStatus = "pending" | "analyzing" | "completed" | "failed";
export type Verdict = "go" | "conditional_go" | "no_go" | "pending";
export type RiskLevel = "HIGH" | "MEDIUM" | "LOW";
export type TeamRole = "PM" | "FE" | "BE" | "MLE" | "DevOps";
export type UserRole = "admin" | "executive" | "sales";

// User
export interface UserResponse {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export interface UserCreate {
  email: string;
  name: string;
  role: UserRole;
}

// Deal
export interface DealCreate {
  title: string;
  raw_input?: string | null;
  notion_page_id?: string | null;
  created_by?: string | null;
}

export interface DealResponse {
  id: string;
  notion_page_id: string | null;
  title: string;
  raw_input: string | null;
  structured_data: Record<string, unknown> | null;
  status: DealStatus;
  current_step: string | null;
  error_message: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  creator: UserResponse | null;
  verdict: Verdict | null;
  total_score: number | null;
}

export interface DealListResponse {
  items: DealResponse[];
  total: number;
  offset: number;
  limit: number;
}

// Analysis
export interface ScoreDetail {
  criterion: string;
  score: number;
  weight: number;
  weighted_score: number;
  rationale: string | null;
}

export interface WorkBreakdownItem {
  area: string;
  is_reusable: boolean;
  reuse_ratio: number;
  effort_person_months: number;
  description: string;
}

export interface PhaseItem {
  name: string;
  duration_months: number;
  roles_needed: string[];
}

export interface CostBreakdown {
  labor_cost: number;
  infrastructure_cost: number;
  overhead_cost: number;
  total_cost: number;
  cost_calculation: string;
}

export interface Profitability {
  deal_amount: number;
  estimated_cost: number;
  expected_margin: number;
  margin_assessment: string;
}

export interface ResourceEstimate {
  work_breakdown: WorkBreakdownItem[] | null;
  phases: PhaseItem[] | null;
  team_composition:
    | {
        role: string;
        count: number;
        monthly_rate: number;
        duration_months?: number;
        assigned_members?: string[];
      }[]
    | null;
  duration_months: number | null;
  risk_buffer_ratio: number | null;
  duration_with_buffer: number | null;
  cost_breakdown: CostBreakdown | null;
  profitability: Profitability | null;
  // v1 backward compat
  total_cost: number | null;
  expected_margin: number | null;
  rationale: string | null;
}

export interface RiskItem {
  category: string;
  item: string;
  probability: RiskLevel | null;
  impact: RiskLevel | null;
  level: RiskLevel;
  evidence: string | null;
  description: string;
  mitigation: string | null;
}

export interface RiskInterdependency {
  risk_pair: string[];
  combined_effect: string;
  amplification: string;
}

export interface SimilarProject {
  project_name: string;
  similarity_score: number;
  industry: string | null;
  tech_stack: string[] | null;
  duration_months: number | null;
  result: string | null;
  lessons_learned: string | null;
}

export interface AnalysisResponse {
  id: string;
  deal_id: string;
  total_score: number | null;
  verdict: Verdict | null;
  scores: ScoreDetail[] | null;
  resource_estimate: ResourceEstimate | null;
  risks: RiskItem[] | null;
  risk_interdependencies: RiskInterdependency[] | null;
  similar_projects: SimilarProject[] | null;
  report_markdown: string | null;
  notion_saved_at: string | null;
  created_at: string;
}

export interface AnalysisTriggerResponse {
  deal_id: string;
  status: string;
  message: string;
}

// Notion
export interface NotionDeal {
  page_id: string;
  deal_info: string;
  customer_name: string | null;
  expected_amount: number | null;
  duration_months: number | null;
  date: string | null;
  author: string | null;
  status: string | null;
}

export interface NotionDealListResponse {
  deals: NotionDeal[];
}

export interface NotionSaveRequest {
  include_report?: boolean;
}

export interface NotionSaveResponse {
  success: boolean;
  decision_page_id: string | null;
  notion_page_url: string | null;
  saved_at: string | null;
}

// Project History
export interface NotionProjectHistory {
  page_id: string;
  project_name: string;
  summary: string | null;
  industry: string | null;
  tech_stack: string[];
  duration_months: number | null;
  planned_headcount: number | null;
  actual_headcount: number | null;
  contract_amount: number | null;
  is_embedded: boolean;
  needs_update: boolean;
  last_edited_time: string | null;
}

export interface ProjectHistoryListResponse {
  projects: NotionProjectHistory[];
  total: number;
  embedded_count: number;
}

export interface PageContentResponse {
  content: string;
}

export interface EmbedRequest {
  project_ids?: string[] | null;
}

export interface EmbedResponse {
  total: number;
  embedded: number;
  skipped: number;
  failed: number;
  errors: string[];
}

// Settings
export interface ScoringCriteriaResponse {
  id: string;
  name: string;
  weight: number;
  description: string | null;
  is_active: boolean;
  display_order: number;
  updated_at: string;
}

export interface WeightUpdateItem {
  id: string;
  weight: number;
}

export interface WeightUpdateRequest {
  weights: WeightUpdateItem[];
}

export interface ScoringCriteriaDefaultItem {
  name: string;
  weight: number;
  description: string | null;
  display_order: number;
}

export interface ScoringCriteriaDefaultsSave {
  items: ScoringCriteriaDefaultItem[];
}

export interface TeamMemberDefaultsSave {
  items: TeamMemberCreate[];
}

export interface CostItemDefaultsSave {
  items: CostItemCreate[];
}

export interface CompanySettingResponse {
  key: string;
  value: string;
  description: string | null;
  updated_at: string;
}

export interface CompanySettingUpsert {
  key: string;
  value: string;
  description?: string | null;
}

export interface CompanySettingBatchUpsert {
  items: CompanySettingUpsert[];
}

export interface TeamMemberResponse {
  id: string;
  name: string;
  role: TeamRole;
  monthly_rate: number;
  is_available: boolean;
  current_project: string | null;
  available_from: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamMemberCreate {
  name: string;
  role: TeamRole;
  monthly_rate: number;
  is_available?: boolean;
  current_project?: string | null;
  available_from?: string | null;
}

export interface TeamMemberUpdate {
  name?: string;
  role?: TeamRole;
  monthly_rate?: number;
  is_available?: boolean;
  current_project?: string | null;
  available_from?: string | null;
}

// Cost Items
export interface CostItemResponse {
  id: string;
  name: string;
  amount: number;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CostItemCreate {
  name: string;
  amount: number;
  description?: string | null;
}

export interface CostItemUpdate {
  name?: string;
  amount?: number;
  description?: string | null;
}

// Agent Logs
export type StepType =
  | "orchestrator_decision"
  | "worker_start"
  | "reasoning"
  | "tool_call"
  | "observation"
  | "worker_result";

export interface AgentLogResponse {
  id: string;
  deal_id: string;
  node_name: string;
  system_prompt: string | null;
  user_prompt: string | null;
  raw_output: string | null;
  parsed_output: Record<string, unknown> | null;
  error: string | null;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
  parent_log_id: string | null;
  step_type: StepType | null;
  step_index: number | null;
  tool_name: string | null;
  worker_name: string | null;
}

export interface AgentLogTreeNode extends AgentLogResponse {
  children: AgentLogTreeNode[];
}

export interface AgentLogTreeResponse {
  deal_id: string;
  logs: AgentLogTreeNode[];
  total_count: number;
  total_duration_ms: number | null;
}

// Prompts
export interface PromptResponse {
  name: string;
  version: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  output_schema: Record<string, unknown> | null;
}

export interface PromptUpdateRequest {
  system_prompt: string;
  user_prompt: string;
  version?: string | null;
  description?: string | null;
}
