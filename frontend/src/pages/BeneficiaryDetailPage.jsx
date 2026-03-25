import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useBeneficiary, useBeneficiarySecrets, useGenerateKey } from '../hooks/useBeneficiaries'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'
import PrivateKeyModal from '../components/beneficiaries/PrivateKeyModal'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'

export default function BeneficiaryDetailPage() {
  const { id } = useParams()
  const { data: beneficiary, isLoading, error } = useBeneficiary(id)
  const { data: secrets } = useBeneficiarySecrets(id)
  const { mutateAsync: generateKey, isPending } = useGenerateKey()
  const [privateKey, setPrivateKey] = useState(null)
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBanner message="Failed to load beneficiary." />
  if (!beneficiary) return null

  const handleGenerate = async () => {
    try {
      const result = await generateKey(beneficiary.id)
      setPrivateKey(result.private_key)
    } catch (err) {
      alert(err.response?.data?.detail || 'Key generation failed.')
    }
  }

  return (
    <div className="space-y-4 max-w-lg">
      <h1 className="text-2xl font-bold">{beneficiary.name}</h1>
      <Card>
        <CardHeader><CardTitle className="text-base">Details</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div><span className="text-muted-foreground">Email:</span> {beneficiary.email}</div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Key:</span>
            <Badge variant={beneficiary.has_key ? 'success' : 'outline'}>{beneficiary.has_key ? 'Generated' : 'Not generated'}</Badge>
          </div>
          {!beneficiary.has_key && (
            <Button size="sm" disabled={isPending} onClick={handleGenerate}>
              {isPending ? 'Generating...' : 'Generate RSA Key'}
            </Button>
          )}
        </CardContent>
      </Card>
      {secrets && secrets.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Assigned Secrets</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {secrets.map(s => <li key={s.id} className="text-muted-foreground">{s.title}</li>)}
            </ul>
          </CardContent>
        </Card>
      )}
      {privateKey && <PrivateKeyModal open={!!privateKey} privateKey={privateKey} onClose={() => setPrivateKey(null)} />}
    </div>
  )
}
