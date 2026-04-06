export interface SMSLog {
  message: string;
  prediction: string;
  confidence: number;
  source?: string;
  ground_truth?: string | null;
  created_at: string;
}

export interface Metrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  test_size: number;
  train_size: number;
  total_messages?: number;
  spam_count?: number;
  ham_count?: number;
  llm_count?: number;
  avg_confidence?: number;
  message?: string;
}
