import { useState } from 'react'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import ErrorBanner from '../common/ErrorBanner'

export default function SecretForm({ onSubmit, isLoading }) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [secretType, setSecretType] = useState('password')
  const [password, setPassword] = useState('')
  const [beneficiaryIds, setBeneficiaryIds] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!title || !content || !password) { setError('Title, content, and password are required.'); return }
    const ids = beneficiaryIds.split(',').map(s => s.trim()).filter(Boolean).map(Number).filter(n => !isNaN(n) && n > 0)
    try {
      await onSubmit({ title, content, secret_type: secretType, password, beneficiary_ids: ids })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create secret.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
      <ErrorBanner message={error} />
      <div className="space-y-1">
        <Label htmlFor="title">Title</Label>
        <Input id="title" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Gmail password" />
      </div>
      <div className="space-y-1">
        <Label htmlFor="content">Content</Label>
        <Textarea id="content" value={content} onChange={e => setContent(e.target.value)} placeholder="The secret content..." rows={4} />
      </div>
      <div className="space-y-1">
        <Label>Type</Label>
        <Select value={secretType} onValueChange={setSecretType}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {['password', 'note', 'document', 'file'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1">
        <Label htmlFor="password">Encryption Password</Label>
        <Input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Used to encrypt locally" />
      </div>
      <div className="space-y-1">
        <Label htmlFor="bids">Beneficiary IDs (comma-separated, optional)</Label>
        <Input id="bids" value={beneficiaryIds} onChange={e => setBeneficiaryIds(e.target.value)} placeholder="1, 2, 3" />
      </div>
      <Button type="submit" disabled={isLoading}>{isLoading ? 'Creating...' : 'Create Secret'}</Button>
    </form>
  )
}
