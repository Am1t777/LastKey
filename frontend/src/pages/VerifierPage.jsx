import { useVerifier, useSetVerifier, useDeleteVerifier } from '../hooks/useVerifier'
import VerifierForm from '../components/verifier/VerifierForm'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

export default function VerifierPage() {
  const { data: verifier, isLoading, error } = useVerifier()
  const { mutateAsync: setVerifier, isPending: isSetting } = useSetVerifier()
  const { mutate: deleteVerifier } = useDeleteVerifier()
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBanner message="Failed to load verifier." />
  return (
    <div className="space-y-4 max-w-lg">
      <h1 className="text-2xl font-bold">Trusted Verifier</h1>
      <p className="text-sm text-muted-foreground">Your trusted verifier will be contacted if you miss a check-in. They confirm your death/incapacitation to release secrets to beneficiaries.</p>
      {verifier ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{verifier.name}</CardTitle>
              <div className="flex gap-1">
                {verifier.has_confirmed && <Badge variant="success">Confirmed</Badge>}
                {verifier.has_denied && <Badge variant="secondary">Denied</Badge>}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">{verifier.email}</p>
            <Button variant="destructive" size="sm" onClick={() => deleteVerifier()}>Remove Verifier</Button>
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground">No trusted verifier set.</p>
      )}
      <div className="pt-2">
        <h2 className="text-lg font-semibold mb-3">{verifier ? 'Update Verifier' : 'Set Verifier'}</h2>
        <VerifierForm defaultValues={verifier || {}} onSubmit={setVerifier} isLoading={isSetting} />
      </div>
    </div>
  )
}
