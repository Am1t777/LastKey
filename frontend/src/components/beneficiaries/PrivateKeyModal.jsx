import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog'
import { Button } from '../ui/button'
import { Copy, Check } from 'lucide-react'

export default function PrivateKeyModal({ open, privateKey, onClose }) {
  const [copied, setCopied] = useState(false)
  const [confirmed, setConfirmed] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(privateKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Private Key Generated</DialogTitle>
          <DialogDescription>This is the ONLY time this key will be shown. Save it now — it cannot be recovered.</DialogDescription>
        </DialogHeader>
        <pre className="bg-muted p-3 rounded text-xs whitespace-pre-wrap break-all max-h-48 overflow-auto">{privateKey}</pre>
        <Button variant="outline" onClick={handleCopy} className="w-full">
          {copied ? <><Check className="h-4 w-4 mr-2" />Copied!</> : <><Copy className="h-4 w-4 mr-2" />Copy to Clipboard</>}
        </Button>
        <div className="flex items-center gap-2 mt-2">
          <input id="key-confirm" type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} className="h-4 w-4" />
          <label htmlFor="key-confirm" className="text-sm">I have saved this private key securely.</label>
        </div>
        <Button disabled={!confirmed} onClick={onClose} className="w-full">Close</Button>
      </DialogContent>
    </Dialog>
  )
}
