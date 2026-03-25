import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { useCreateBeneficiary, useBeneficiaries } from '../hooks/useBeneficiaries'
import BeneficiaryCard from '../components/beneficiaries/BeneficiaryCard'
import BeneficiaryForm from '../components/beneficiaries/BeneficiaryForm'
import { Button } from '../components/ui/button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

export default function BeneficiariesPage() {
  const [showForm, setShowForm] = useState(false)
  const { data: beneficiaries, isLoading, error } = useBeneficiaries()
  const { mutateAsync: createBeneficiary, isPending } = useCreateBeneficiary()
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Beneficiaries</h1>
        <Button size="sm" onClick={() => setShowForm(v => !v)}>
          {showForm ? <><X className="h-4 w-4 mr-1" />Cancel</> : <><Plus className="h-4 w-4 mr-1" />Add</>}
        </Button>
      </div>
      {showForm && (
        <BeneficiaryForm onSubmit={async (data) => { await createBeneficiary(data); setShowForm(false) }} isLoading={isPending} />
      )}
      {isLoading && <LoadingSpinner />}
      {error && <ErrorBanner message="Failed to load beneficiaries." />}
      {beneficiaries?.length === 0 && <p className="text-muted-foreground text-sm">No beneficiaries yet.</p>}
      <div className="space-y-2">
        {(beneficiaries || []).map(b => <BeneficiaryCard key={b.id} beneficiary={b} />)}
      </div>
    </div>
  )
}
