export type SpellErrorResponse = {
  error_type: string
  error_message: string
  start_index: number
  end_index: number
  rule_id: string
  detailed: string
}
