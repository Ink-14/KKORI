import { useState, useEffect, useRef } from 'react'
import './ScrollToTopButton.css'

function ScrollToTopButton() {
  const [visible, setVisible] = useState(false)
  const containerRef = useRef<Element | null>(null)

  useEffect(() => {
    const container = document.querySelector('.desktop-content') ?? window as unknown as Element
    containerRef.current = container

    function onScroll() {
      const scrollTop = container instanceof Window
        ? container.scrollY
        : (container as Element).scrollTop
      setVisible(scrollTop > 100)
    }

    container.addEventListener('scroll', onScroll)
    return () => container.removeEventListener('scroll', onScroll)
  }, [])

  if (!visible) return null

  return (
    <button
      className="scroll-to-top"
      onClick={() => {
        const container = containerRef.current
        if (!container) return
        if (container instanceof Window) {
          container.scrollTo({ top: 0, behavior: 'smooth' })
        } else {
          (container as Element).scrollTo({ top: 0, behavior: 'smooth' })
        }
      }}
      aria-label="맨 위로"
    >
      ↑
    </button>
  )
}

export default ScrollToTopButton
