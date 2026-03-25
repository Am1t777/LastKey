import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getRelease } from '../services/releaseService'
import { decryptSecretAsBeneficiary } from '../lib/crypto'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import { Button } from '../components/ui/button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

export default function ReleasePage() {
  const { token } = useParams()
  const { data, isLoading, error } = useQuery({ queryKey: ['release', token], queryFn: () => getRelease(token) })
  const [privateKey, setPrivateKey] = useState('')
  const [decrypted, setDecrypted] = useState([])
  const [decryptError, setDecryptError] = useState('')
  const [isDecrypting, setIsDecrypting] = useState(false)

  const handleDecrypt = async () => {
    setDecryptError('')
    setIsDecrypting(true)
    try {
      const results = await Promise.all(
        (data.secrets || []).map(async (s) => {
          try {
            const plaintext = await decryptSecretAsBeneficiary(privateKey, s.encrypted_key, s.encrypted_content, s.encryption_iv, s.encryption_tag)
            return { ...s, plaintext }
          } catch {
            return { ...s, plaintext: null, decryptError: 'Failed to decrypt this secret.' }
          }
        }),
      )
      setDecrypted(results)
    } catch {
      setDecryptError('Decryption failed. Ensure you pasted the correct private key.')
    } finally {
      setIsDecrypting(false)
    }
  }

  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>
  if (error) return <div className="min-h-screen flex items-center justify-center p-4"><ErrorBanner message="Invalid or expired release link." /></div>

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold">Inherited Secrets</h1>
        <p className="text-sm text-muted-foreground">Paste your private key below to decrypt the secrets left to you.</p>
        {decrypted.length === 0 && (
          <div className="space-y-3">
            <ErrorBanner message={decryptError} />
            <div className="space-y-1">
              <Label htmlFor="pk">Your Private Key (PEM format)</Label>
              <Textarea id="pk" value={privateKey} onChange={e => setPrivateKey(e.target.value)} placeholder={"-----BEGIN PRIVATE KEY-----\n..."} rows={6} className="font-mono text-xs" />
            </div>
            <Button onClick={handleDecrypt} disabled={isDecrypting || !privateKey}>
              {isDecrypting ? 'Decrypting...' : 'Decrypt Secrets'}
            </Button>
          </div>
        )}
        {decrypted.length > 0 && (
          <div className="space-y-4">
            {decrypted.map((s, i) => (
              <Card key={i}>
                <CardHeader><CardTitle className="text-base">{s.title}</CardTitle></CardHeader>
                <CardContent>
                  {s.decryptError
                    ? <p className="text-destructive text-sm">{s.decryptError}</p>
                    : <pre className="bg-muted p-3 rounded text-sm whitespace-pre-wrap break-all">{s.plaintext}</pre>}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
