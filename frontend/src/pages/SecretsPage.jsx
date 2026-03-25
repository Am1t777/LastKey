import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { useSecrets } from '../hooks/useSecrets'
import SecretCard from '../components/secrets/SecretCard'
import { Button } from '../components/ui/button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

export default function SecretsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useSecrets(page)
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Secrets</h1>
        <Link to="/secrets/new">
          <Button size="sm"><Plus className="h-4 w-4 mr-1" />New Secret</Button>
        </Link>
      </div>
      {isLoading && <LoadingSpinner />}
      {error && <ErrorBanner message="Failed to load secrets." />}
      {data?.items?.length === 0 && <p className="text-muted-foreground text-sm">No secrets yet. Create your first one.</p>}
      <div className="space-y-2">
        {(data?.items || []).map(s => <SecretCard key={s.id} secret={s} />)}
      </div>
      {data && (
        <div className="flex items-center gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span className="text-muted-foreground">Page {page}</span>
          <Button variant="outline" size="sm" disabled={!data.has_more} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}
    </div>
  )
}
