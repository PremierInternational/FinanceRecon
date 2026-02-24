export interface CompareStats {
  total_records: number
  matched_records: number
  match_percentage: number
}

export interface CompareResult {
  stats: CompareStats
  columns: string[]
  rows: Record<string, unknown>[]
  download_token: string
}

export interface Profile {
  match_keys_first: string[]
  match_keys_second: string[]
  compare_col_first: string
  compare_col_second: string
  tolerance_type: string
  tolerance_value: number | null
}

export interface ProfilesMap {
  [name: string]: Profile
}
