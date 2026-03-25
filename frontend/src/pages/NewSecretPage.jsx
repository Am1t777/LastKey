import { useNavigate } from 'react-router-dom'
import SecretForm from '../components/secrets/SecretForm'
import { useCreateSecret } from '../hooks/useSecrets'

export default function NewSecretPage() {
  const navigate = useNavigate()
  const { mutateAsync: createSecret, isPending } = useCreateSecret()
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">New Secret</h1>
      <SecretForm onSubmit={async (data) => { await createSecret(data); navigate('/secrets') }} isLoading={isPending} />
    </div>
  )
}
