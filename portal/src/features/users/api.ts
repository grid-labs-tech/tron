import { api } from '../../shared/api'
import type { User, UserCreate } from './types'

export const usersApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }): Promise<User[]> => {
    const response = await api.get<User[]>('/users', { params })
    return response.data
  },
  get: async (uuid: string): Promise<User> => {
    const response = await api.get<User>(`/users/${uuid}`)
    return response.data
  },
  create: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/users', data)
    return response.data
  },
  update: async (uuid: string, data: Partial<UserCreate & { is_active?: boolean; role?: string }>): Promise<User> => {
    const response = await api.put<User>(`/users/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/users/${uuid}`)
  },
}
