import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe } from '../services/authService'
import { updateInterval } from '../services/settingsService'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Button } from '../components/ui/button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

export default function SettingsPage() {
  const qc = useQueryClient()
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const [days, setDays] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  if (isLoading) return <LoadingSpinner />

  const handleSave = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)
    const n = Number(days)
    if (!n || n < 1 || n > 365) { setError('Enter a value between 1 and 365.'); return }
    setIsSaving(true)
    try {
      await updateInterval(n)
      await qc.invalidateQueries({ queryKey: ['me'] })
      setSuccess(true)
      setDays('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-4 max-w-sm">
      <h1 className="text-2xl font-bold">Settings</h1>
      <Card>
        <CardHeader><CardTitle className="text-base">Check-in Interval</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">Current interval: <strong>{user?.check_in_interval_days} days</strong></p>
          <form onSubmit={handleSave} className="space-y-3">
            <ErrorBanner message={error} />
            {success && <p className="text-sm text-green-600">Interval updated successfully.</p>}
            <div className="space-y-1">
              <Label htmlFor="interval">New Interval (days)</Label>
              <Input id="interval" type="number" min={1} max={365} value={days} onChange={e => setDays(e.target.value)} placeholder={String(user?.check_in_interval_days)} />
            </div>
            <Button type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save'}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
