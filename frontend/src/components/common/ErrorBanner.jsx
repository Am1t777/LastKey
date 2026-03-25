export default function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
      {message}
    </div>
  )
}
