import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import ErrorBanner from '../common/ErrorBanner'
import { useAssignSecret } from '../../hooks/useSecrets'
import { useBeneficiaries } from '../../hooks/useBeneficiaries'

export default function AssignDialog({ open, onOpenChange, secretId }) {
  const [beneficiaryId, setBeneficiaryId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { data: beneficiaries } = useBeneficiaries()
  const { mutateAsync: assign, isPending } = useAssignSecret()

  const handleAssign = async () => {
    setError('')
    try {
      await assign({ id: secretId, data: { beneficiary_id: Number(beneficiaryId), password } })
      onOpenChange(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Assignment failed.')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Assign to Beneficiary</DialogTitle></DialogHeader>
        <ErrorBanner message={error} />
        <div className="space-y-4">
          <div className="space-y-1">
            <Label>Beneficiary</Label>
            <Select value={beneficiaryId} onValueChange={setBeneficiaryId}>
              <SelectTrigger><SelectValue placeholder="Select beneficiary..." /></SelectTrigger>
              <SelectContent>
                {(beneficiaries || []).map(b => (
                  <SelectItem key={b.id} value={String(b.id)}>{b.name} ({b.email})</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="assign-pw">Encryption Password</Label>
            <Input id="assign-pw" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Secret's encryption password" />
          </div>
          <Button onClick={handleAssign} disabled={isPending || !beneficiaryId || !password}>
            {isPending ? 'Assigning...' : 'Assign'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
