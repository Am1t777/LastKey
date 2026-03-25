import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { formatDate } from '../../lib/utils'
import { useCheckin } from '../../hooks/useCheckin'
import { useQueryClient } from '@tanstack/react-query'

export default function NextCheckinCard({ user }) {
  const qc = useQueryClient()
  const { mutate: checkin, isPending, isSuccess, isError } = useCheckin()
  const nextDue = user?.last_check_in_at
    ? new Date(new Date(user.last_check_in_at).getTime() + user.check_in_interval_days * 86400000)
    : null
  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Next Check-in Due</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <p className="text-2xl font-bold">{nextDue ? formatDate(nextDue.toISOString()) : '—'}</p>
        {isSuccess && <p className="text-sm text-green-600">Check-in successful!</p>}
        {isError && <p className="text-sm text-destructive">Check-in failed. Try again.</p>}
        <Button size="sm" disabled={isPending} onClick={() => checkin()}>
          {isPending ? 'Checking in...' : 'Check In Now'}
        </Button>
      </CardContent>
    </Card>
  )
}
