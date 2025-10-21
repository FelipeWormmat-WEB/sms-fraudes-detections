export interface SMSLog {
  message: string;
  prediction: string;
  confidence: number;
  created_at: string;
}

export interface Metrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  test_size: number;
  train_size: number;
}
