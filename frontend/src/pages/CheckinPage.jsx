import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { checkinByToken } from '../services/checkinService'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function CheckinPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('No check-in token provided.'); return }
    checkinByToken(token)
      .then(data => { setStatus('success'); setMessage(data.message) })
      .catch(err => { setStatus('error'); setMessage(err.response?.data?.detail || 'Check-in failed.') })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{status === 'loading' ? 'Checking in...' : status === 'success' ? 'Check-in Successful' : 'Check-in Failed'}</CardTitle>
        </CardHeader>
        <CardContent>
          {status === 'loading' ? <LoadingSpinner /> : (
            <p className={status === 'success' ? 'text-green-600' : 'text-destructive'}>{message}</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
