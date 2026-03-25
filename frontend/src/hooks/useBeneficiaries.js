import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as svc from '../services/beneficiariesService'

export const useBeneficiaries = () => useQuery({ queryKey: ['beneficiaries'], queryFn: svc.listBeneficiaries })
export const useBeneficiary = (id) => useQuery({ queryKey: ['beneficiaries', id], queryFn: () => svc.getBeneficiary(id), enabled: !!id })
export const useBeneficiarySecrets = (id) => useQuery({ queryKey: ['beneficiaries', id, 'secrets'], queryFn: () => svc.listBeneficiarySecrets(id), enabled: !!id })

export function useCreateBeneficiary() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.createBeneficiary, onSuccess: () => qc.invalidateQueries({ queryKey: ['beneficiaries'] }) })
}

export function useUpdateBeneficiary() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ id, data }) => svc.updateBeneficiary(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['beneficiaries'] }) })
}

export function useDeleteBeneficiary() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.deleteBeneficiary, onSuccess: () => qc.invalidateQueries({ queryKey: ['beneficiaries'] }) })
}

export function useGenerateKey() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: svc.generateKey, onSuccess: () => qc.invalidateQueries({ queryKey: ['beneficiaries'] }) })
}
