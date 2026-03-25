import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as svc from '../services/secretsService'

export const useSecrets = (page = 1) =>
  useQuery({ queryKey: ['secrets', page], queryFn: () => svc.listSecrets(page) })

export const useSecret = (id) =>
  useQuery({ queryKey: ['secrets', id], queryFn: () => svc.getSecret(id), enabled: !!id })

export function useCreateSecret() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.createSecret, onSuccess: () => qc.invalidateQueries({ queryKey: ['secrets'] }) })
}

export function useUpdateSecret() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ id, data }) => svc.updateSecret(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['secrets'] }) })
}

export function useDeleteSecret() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.deleteSecret, onSuccess: () => qc.invalidateQueries({ queryKey: ['secrets'] }) })
}

export function useAssignSecret() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ id, data }) => svc.assignSecret(id, data), onSuccess: (_, { id }) => qc.invalidateQueries({ queryKey: ['secrets', id] }) })
}
