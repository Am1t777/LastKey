import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import { decryptSecretAsOwner } from '../../lib/crypto'
import ErrorBanner from '../common/ErrorBanner'

export default function DecryptDialog({ open, onOpenChange, secret }) {
  const [password, setPassword] = useState('')
  const [plaintext, setPlaintext] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleDecrypt = async () => {
    setError('')
    setIsLoading(true)
    try {
      const result = await decryptSecretAsOwner(password, secret.owner_encrypted_key, secret.encrypted_content, secret.encryption_iv, secret.encryption_tag)
      setPlaintext(result)
    } catch {
      setError('Decryption failed. Check your password.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => { setPassword(''); setPlaintext(''); setError(''); onOpenChange(false) }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader><DialogTitle>Decrypt Secret</DialogTitle></DialogHeader>
        <ErrorBanner message={error} />
        {!plaintext ? (
          <div className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="dec-pw">Password</Label>
              <Input id="dec-pw" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Encryption password" onKeyDown={e => e.key === 'Enter' && handleDecrypt()} />
            </div>
            <Button onClick={handleDecrypt} disabled={isLoading || !password}>{isLoading ? 'Decrypting...' : 'Decrypt'}</Button>
          </div>
        ) : (
          <div className="space-y-3">
            <Label>Decrypted Content</Label>
            <pre className="bg-muted p-3 rounded text-sm whitespace-pre-wrap break-all max-h-64 overflow-auto">{plaintext}</pre>
            <Button variant="outline" onClick={handleClose}>Close</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
