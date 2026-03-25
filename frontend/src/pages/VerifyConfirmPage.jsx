import { useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Button } from '../components/ui/button'
import ErrorBanner from '../components/common/ErrorBanner'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function VerifyConfirmPage() {
  const { token } = useParams()
  const [confirmationText, setConfirmationText] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  const handleConfirm = async () => {
    setError('')
    setStatus('loading')
    try {
      await axios.post(`${API_URL}/api/verify/${token}/confirm`, { confirmation_text: confirmationText })
      setStatus('success')
    } catch (err) {
      setStatus('idle')
      setError(err.response?.data?.detail || 'Confirmation failed.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader><CardTitle>Confirm Incapacitation</CardTitle></CardHeader>
        <CardContent>
          {status === 'success' ? (
            <p className="text-green-600">Thank you. Beneficiaries will be notified and given access to the secrets.</p>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Type the full name of the person exactly as it appears in their account to confirm.</p>
              <ErrorBanner message={error} />
              <div className="space-y-1">
                <Label htmlFor="confirm-text">Full Name</Label>
                <Input id="confirm-text" value={confirmationText} onChange={e => setConfirmationText(e.target.value)} placeholder="Type their full name" />
              </div>
              <Button className="w-full" disabled={status === 'loading' || !confirmationText} onClick={handleConfirm}>
                {status === 'loading' ? 'Confirming...' : 'Confirm'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
