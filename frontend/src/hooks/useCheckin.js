import { useMutation, useQueryClient } from '@tanstack/react-query'
import { checkinAuthenticated } from '../services/checkinService'

export function useCheckin() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: checkinAuthenticated, onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }) })
}
