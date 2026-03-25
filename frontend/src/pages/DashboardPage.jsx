import { useQuery } from '@tanstack/react-query'
import { getMe } from '../services/authService'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'
import SwitchStatusWidget from '../components/dashboard/SwitchStatusWidget'
import NextCheckinCard from '../components/dashboard/NextCheckinCard'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { formatDateTime } from '../lib/utils'

export default function DashboardPage() {
  const { data: user, isLoading, error } = useQuery({ queryKey: ['me'], queryFn: getMe })
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBanner message="Failed to load user data." />
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <SwitchStatusWidget status={user.switch_status} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <NextCheckinCard user={user} />
        <Card>
          <CardHeader><CardTitle className="text-base">Account Info</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div><span className="text-muted-foreground">Name:</span> {user.name}</div>
            <div><span className="text-muted-foreground">Email:</span> {user.email}</div>
            <div><span className="text-muted-foreground">Check-in interval:</span> {user.check_in_interval_days} days</div>
            <div><span className="text-muted-foreground">Last check-in:</span> {formatDateTime(user.last_check_in_at)}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
