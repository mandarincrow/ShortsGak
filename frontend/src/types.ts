export type AnalyzeRequest = {
  source: {
    vod_id: string;
  };
  keywords: string[];
  options: {
    bucket_size_seconds: number;
    keyword_options: {
      mode: "contains" | "exact";
      case_sensitive: boolean;
    };
    min_highlight_score: number;
    max_highlights: number;
  };
};

export type ExportDataset =
  | "summary"
  | "highlights"
  | "volume"
  | "keywords"
  | "parse_errors"
  | "all";

export type ExportFormat = "json" | "csv";

export type AnalyzeResponse = {
  summary: {
    total_messages: number;
    unique_users: number;
    start_time: string | null;
    end_time: string | null;
    vod_duration_sec: number;
    vod_duration_label: string;
    avg_messages_per_minute: number;
  };
  volume_series: Array<{
    bucket_start: string;
    bucket_start_offset_sec: number;
    bucket_start_offset_label: string;
    total_messages: number;
    unique_users: number;
  }>;
  keyword_series: Array<{
    bucket_start: string;
    bucket_start_offset_sec: number;
    bucket_start_offset_label: string;
    keyword: string;
    count: number;
  }>;
  highlights: Array<{
    start: string;
    start_offset_sec: number;
    start_offset_label: string;
    end: string;
    end_offset_sec: number;
    end_offset_label: string;
    score: number;
    peak_bucket: string;
    peak_offset_sec: number;
    peak_offset_label: string;
    peak_total_messages: number;
    representative_keyword: string | null;
  }>;
  parse_errors: Array<{
    file_path: string;
    line_number: number;
    reason: string;
    raw_line: string;
  }>;
  message: string;
};
