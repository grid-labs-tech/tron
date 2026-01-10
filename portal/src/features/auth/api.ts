import { api } from '../../shared/api'
import type { LoginRequest, RefreshTokenRequest, UpdateProfileRequest, User, UserCreate, Token } from './types'

export const authApi = {
  login: async (data: LoginRequest): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', data)
    return response.data
  },
  register: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },
  refresh: async (data: RefreshTokenRequest): Promise<Token> => {
    const response = await api.post<Token>('/auth/refresh', data)
    return response.data
  },
  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },
  updateProfile: async (data: UpdateProfileRequest): Promise<User> => {
    const response = await api.put<User>('/auth/me', data)
    return response.data
  },
}
