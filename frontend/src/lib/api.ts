declare const __API_BASE__: string

export function getApiBase(): Promise<string> {
  return Promise.resolve(__API_BASE__)
}
