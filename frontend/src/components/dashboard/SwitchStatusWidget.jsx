import { Badge } from '../ui/badge'
const statusConfig = {
  active: { label: 'Active', variant: 'success' },
  reminder_sent: { label: 'Reminder Sent', variant: 'warning' },
  verifier_alerted: { label: 'Verifier Alerted', variant: 'danger' },
  released: { label: 'Released', variant: 'destructive' },
}
export default function SwitchStatusWidget({ status }) {
  const config = statusConfig[status] || { label: status, variant: 'secondary' }
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Dead man's switch status:</span>
      <Badge variant={config.variant}>{config.label}</Badge>
    </div>
  )
}
