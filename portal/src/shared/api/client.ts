import axios, { AxiosInstance } from 'axios'
import { API_BASE_URL } from '../../config/api'
import type { Token } from '../types'

export const createApiClient = (): AxiosInstance => {
  const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Interceptor para adicionar token em todas as requisições
  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Interceptor para refresh automático de token
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      // Não tentar refresh em endpoints de autenticação (login, register, refresh)
      // Um 401 nesses endpoints significa credenciais inválidas, não token expirado
      const isAuthEndpoint = originalRequest?.url?.includes('/auth/login') ||
                            originalRequest?.url?.includes('/auth/register') ||
                            originalRequest?.url?.includes('/auth/refresh')

      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
        originalRequest._retry = true

        try {
          const refreshToken = localStorage.getItem('refresh_token')
          if (!refreshToken) {
            throw new Error('No refresh token')
          }

          const response = await axios.post<Token>(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data
          localStorage.setItem('access_token', access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`

          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }

      return Promise.reject(error)
    }
  )

  return api
}

export const api = createApiClient()
