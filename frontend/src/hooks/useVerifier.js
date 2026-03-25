import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as svc from '../services/verifierService'

export const useVerifier = () =>
  useQuery({
    queryKey: ['verifier'],
    queryFn: async () => {
      try { return await svc.getVerifier() }
      catch (e) { if (e.response?.status === 404) return null; throw e }
    },
  })

export function useSetVerifier() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.setVerifier, onSuccess: () => qc.invalidateQueries({ queryKey: ['verifier'] }) })
}

export function useDeleteVerifier() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.deleteVerifier, onSuccess: () => qc.invalidateQueries({ queryKey: ['verifier'] }) })
}
