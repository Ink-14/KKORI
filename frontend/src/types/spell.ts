export type SpellErrorResponse = {
  error_type: string
  error_message: string
  // Unicode code point offsets; end_index is exclusive.
  start_index: number
  end_index: number
  rule_id: string
  detailed: string
}
