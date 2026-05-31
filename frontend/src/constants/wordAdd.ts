// 새 태그 추가 시: 1) WORD_TAGS에 항목 추가  2) WORD_TAG_BADGE에 CSS 클래스 키 추가  3) wordAdd.css에 .wordadd-badge--{클래스} 스타일 추가
export const WORD_TAGS = ['고유명사', '일반명사', '종결어미'] as const

export type WordTag = (typeof WORD_TAGS)[number]

export const DEFAULT_WORD_TAG: WordTag = '고유명사'

export const WORD_TAG_BADGE: Record<WordTag, string> = {
  '고유명사': 'proper',
  '일반명사': 'common',
  '종결어미': 'ending',
}
