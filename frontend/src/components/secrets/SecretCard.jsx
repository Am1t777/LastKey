import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trash2, Eye } from 'lucide-react'
import { Card, CardContent } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import ConfirmDeleteDialog from '../common/ConfirmDeleteDialog'
import { useDeleteSecret } from '../../hooks/useSecrets'
import { formatDate } from '../../lib/utils'

export default function SecretCard({ secret }) {
  const navigate = useNavigate()
  const [showDelete, setShowDelete] = useState(false)
  const { mutate: deleteSecret } = useDeleteSecret()
  return (
    <>
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{secret.title}</p>
              <p className="text-xs text-muted-foreground">{formatDate(secret.created_at)}</p>
            </div>
            <Badge variant="outline">{secret.secret_type}</Badge>
          </div>
          <div className="flex items-center gap-1 ml-2">
            <Button variant="ghost" size="icon" onClick={() => navigate(`/secrets/${secret.id}`)}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setShowDelete(true)}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </CardContent>
      </Card>
      <ConfirmDeleteDialog open={showDelete} onOpenChange={setShowDelete} title="Delete Secret"
        description={`Delete "${secret.title}"? This cannot be undone.`}
        onConfirm={() => deleteSecret(secret.id)} />
    </>
  )
}
