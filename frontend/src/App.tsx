import { useState } from 'react'
import Checker from './pages/checker'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <Checker></Checker>
    </>
  )
}

export default App
