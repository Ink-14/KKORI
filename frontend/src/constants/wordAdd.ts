export const WORD_TAGS = ['고유명사', '일반명사'] as const

export type WordTag = (typeof WORD_TAGS)[number]

export const DEFAULT_WORD_TAG: WordTag = '고유명사'
