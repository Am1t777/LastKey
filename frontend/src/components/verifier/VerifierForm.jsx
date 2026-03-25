import { useState } from 'react'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import ErrorBanner from '../common/ErrorBanner'

export default function VerifierForm({ onSubmit, isLoading, defaultValues = {} }) {
  const [name, setName] = useState(defaultValues.name || '')
  const [email, setEmail] = useState(defaultValues.email || '')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!name || !email) { setError('Name and email are required.'); return }
    try { await onSubmit({ name, email }) }
    catch (err) { setError(err.response?.data?.detail || 'Failed to save verifier.') }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
      <ErrorBanner message={error} />
      <div className="space-y-1">
        <Label htmlFor="v-name">Name</Label>
        <Input id="v-name" value={name} onChange={e => setName(e.target.value)} placeholder="Trusted person's name" />
      </div>
      <div className="space-y-1">
        <Label htmlFor="v-email">Email</Label>
        <Input id="v-email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" />
      </div>
      <Button type="submit" disabled={isLoading}>{isLoading ? 'Saving...' : 'Save Verifier'}</Button>
    </form>
  )
}
