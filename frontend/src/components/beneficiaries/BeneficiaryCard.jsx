import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Trash2 } from 'lucide-react'
import { Card, CardContent } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import ConfirmDeleteDialog from '../common/ConfirmDeleteDialog'
import { useDeleteBeneficiary } from '../../hooks/useBeneficiaries'

export default function BeneficiaryCard({ beneficiary }) {
  const navigate = useNavigate()
  const [showDelete, setShowDelete] = useState(false)
  const { mutate: deleteBeneficiary } = useDeleteBeneficiary()
  return (
    <>
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{beneficiary.name}</p>
            <p className="text-xs text-muted-foreground truncate">{beneficiary.email}</p>
          </div>
          <div className="flex items-center gap-2 ml-2">
            <Badge variant={beneficiary.has_key ? 'success' : 'outline'}>{beneficiary.has_key ? 'Key Generated' : 'No Key'}</Badge>
            <Button variant="ghost" size="icon" onClick={() => navigate(`/beneficiaries/${beneficiary.id}`)}><Eye className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" onClick={() => setShowDelete(true)}><Trash2 className="h-4 w-4 text-destructive" /></Button>
          </div>
        </CardContent>
      </Card>
      <ConfirmDeleteDialog open={showDelete} onOpenChange={setShowDelete} title="Delete Beneficiary"
        description={`Remove ${beneficiary.name}? All secret assignments for this beneficiary will be deleted.`}
        onConfirm={() => deleteBeneficiary(beneficiary.id)} />
    </>
  )
}
