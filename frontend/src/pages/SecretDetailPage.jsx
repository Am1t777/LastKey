import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useSecret } from '../hooks/useSecrets'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import DecryptDialog from '../components/secrets/DecryptDialog'
import AssignDialog from '../components/secrets/AssignDialog'
import { formatDateTime } from '../lib/utils'

export default function SecretDetailPage() {
  const { id } = useParams()
  const { data: secret, isLoading, error } = useSecret(id)
  const [showDecrypt, setShowDecrypt] = useState(false)
  const [showAssign, setShowAssign] = useState(false)
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBanner message="Failed to load secret." />
  if (!secret) return null
  return (
    <div className="space-y-4 max-w-lg">
      <h1 className="text-2xl font-bold">{secret.title}</h1>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Secret Details</CardTitle>
            <Badge variant="outline">{secret.secret_type}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div><span className="text-muted-foreground">Created:</span> {formatDateTime(secret.created_at)}</div>
          <div><span className="text-muted-foreground">Updated:</span> {formatDateTime(secret.updated_at)}</div>
          <div className="pt-2 flex gap-2">
            <Button size="sm" onClick={() => setShowDecrypt(true)}>Decrypt</Button>
            <Button size="sm" variant="outline" onClick={() => setShowAssign(true)}>Assign to Beneficiary</Button>
          </div>
        </CardContent>
      </Card>
      <DecryptDialog open={showDecrypt} onOpenChange={setShowDecrypt} secret={secret} />
      <AssignDialog open={showAssign} onOpenChange={setShowAssign} secretId={secret.id} />
    </div>
  )
}
