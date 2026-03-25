import { cn } from '../../lib/utils'
export default function LoadingSpinner({ fullScreen = false, className }) {
  const spinner = (
    <div className={cn('flex items-center justify-center p-8', className)}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  )
  if (fullScreen) return <div className="min-h-screen flex items-center justify-center">{spinner}</div>
  return spinner
}
