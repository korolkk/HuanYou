export interface Trip {
  id: string
  code: string
  title: string
  subtitle?: string
  destination: string
  destinations_detail: string[]
  country: string
  province?: string
  city?: string
  category: string
  duration_days: number
  duration_nights?: number
  departure_city?: string
  best_season?: string
  price_adult?: number
  price_child?: number
  price_infant?: number
  single_room_supplement?: number
  price_includes: string[]
  price_excludes: string[]
  summary?: string
  highlights: string[]
  recommendation_reasons: string[]
  detailed_description?: string
  group_size_min: number
  group_size_max?: number
  departure_dates: string[]
  cover_image_url?: string
  image_urls: string[]
  brochure_url?: string
  is_featured: boolean
  status: string
  schedules: TripSchedule[]
  created_at: string
  updated_at: string
}

export interface TripSchedule {
  id: string
  trip_id: string
  day_number: number
  theme?: string
  schedule_type: string
  time_start?: string
  time_end?: string
  location?: string
  activity?: string
  description?: string
  meal_included?: string
  hotel_name?: string
  hotel_stars?: number
  hotel_description?: string
  transport_type?: string
  transport_detail?: string
  tips?: string
  image_urls: string[]
  sort_order: number
}

export interface Order {
  id: string
  order_code: string
  trip_id: string
  trip_title: string
  trip_destination: string
  departure_date?: string
  num_adults: number
  num_children: number
  num_infants: number
  total_price?: number
  paid_amount: number
  discount_amount: number
  participants?: any[]
  status: string
  payment_status: string
  contract_url?: string
  insurance_url?: string
  created_at: string
  updated_at: string
}

export interface ScriptSegment {
  timecode_start: string
  timecode_end: string
  duration_seconds: number
  segment_type: 'hook' | 'highlights' | 'detail' | 'cta'
  text: string
  image_ref?: string
  image_keyword?: string
  bgm_suggestion?: string
}

export interface VideoScript {
  id: string
  trip_id: string
  title?: string
  platform: string
  duration_seconds: number
  style?: string
  script_content: string
  segments: ScriptSegment[]
  script_json?: any
  hook_text?: string
  highlights_text?: string
  detail_text?: string
  cta_text?: string
  image_assignments?: any
  quality_score?: number
  engagement_score?: number
  accuracy_score?: number
  completeness_score?: number
  generation_version: number
  polish_iterations: number
  status: string
  capcut_draft_id?: string
  export_status: string
  exported_at?: string
  created_at: string
  updated_at?: string
}

export interface ScriptGenerateRequest {
  trip_id: string
  platform?: string
  duration_seconds?: number
  style?: string
}

export interface ScriptPolishRequest {
  focus_areas?: string[]
  target_segment_index?: number
}

export interface ScriptEvaluateResponse {
  quality_score: number
  engagement_score: number
  accuracy_score: number
  completeness_score: number
  passed: boolean
  feedback: string
}

export interface ScriptExportResponse {
  draft_id: string
  draft_name: string
  file_size_bytes: number
  platform_style: Record<string, unknown>
  instructions: string
}

export interface ScriptListResponse {
  id: string
  trip_id: string
  title?: string
  platform: string
  duration_seconds: number
  quality_score?: number
  status: string
  export_status: string
  created_at: string
}

export interface RecommendResult {
  trip_id: string
  title: string
  destination: string
  duration_days: number
  price_adult?: number
  highlights: string[]
  cover_image_url?: string
  match_score: number
  match_reasons: string[]
  match_tags: string[]
  category: string
}
