import { useState } from 'react'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import ErrorBanner from '../common/ErrorBanner'

export default function BeneficiaryForm({ onSubmit, isLoading, defaultValues = {} }) {
  const [name, setName] = useState(defaultValues.name || '')
  const [email, setEmail] = useState(defaultValues.email || '')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!name || !email) { setError('Name and email are required.'); return }
    try { await onSubmit({ name, email }) }
    catch (err) { setError(err.response?.data?.detail || 'Failed.') }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
      <ErrorBanner message={error} />
      <div className="space-y-1">
        <Label htmlFor="b-name">Name</Label>
        <Input id="b-name" value={name} onChange={e => setName(e.target.value)} placeholder="Full name" />
      </div>
      <div className="space-y-1">
        <Label htmlFor="b-email">Email</Label>
        <Input id="b-email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" />
      </div>
      <Button type="submit" disabled={isLoading}>{isLoading ? 'Saving...' : 'Save'}</Button>
    </form>
  )
}
