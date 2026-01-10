import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../api'

export const useMe = () => {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.getMe,
  })
}

export const useLogin = () => {
  return useMutation({
    mutationFn: authApi.login,
  })
}

export const useRegister = () => {
  return useMutation({
    mutationFn: authApi.register,
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}
