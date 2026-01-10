import { api } from '../../shared/api'
import type { ApiToken, ApiTokenCreate, ApiTokenUpdate, ApiTokenCreateResponse } from './types'

export const tokensApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }): Promise<ApiToken[]> => {
    const response = await api.get<ApiToken[]>('/tokens', { params })
    return response.data
  },
  get: async (uuid: string): Promise<ApiToken> => {
    const response = await api.get<ApiToken>(`/tokens/${uuid}`)
    return response.data
  },
  create: async (data: ApiTokenCreate): Promise<ApiTokenCreateResponse> => {
    const response = await api.post<ApiTokenCreateResponse>('/tokens', data)
    return response.data
  },
  update: async (uuid: string, data: ApiTokenUpdate): Promise<ApiToken> => {
    const response = await api.put<ApiToken>(`/tokens/${uuid}`, data)
    return response.data
  },
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/tokens/${uuid}`)
  },
}
