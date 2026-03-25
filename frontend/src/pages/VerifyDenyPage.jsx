import { useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function VerifyDenyPage() {
  const { token } = useParams()
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  const handleDeny = async () => {
    setStatus('loading')
    try {
      const { data } = await axios.post(`${API_URL}/api/verify/${token}/deny`)
      setStatus('success')
      setMessage(data.message)
    } catch (err) {
      setStatus('error')
      setMessage(err.response?.data?.detail || 'Denial failed.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader><CardTitle>Deny — Person is Alive</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {(status === 'idle' || status === 'loading') ? (
            <>
              <p className="text-sm text-muted-foreground">Click below to confirm this person is alive. Their timer will be reset.</p>
              <Button className="w-full" onClick={handleDeny} disabled={status === 'loading'}>
                {status === 'loading' ? 'Processing...' : 'Confirm — Person is Alive'}
              </Button>
            </>
          ) : (
            <p className={status === 'success' ? 'text-green-600' : 'text-destructive'}>{message}</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
