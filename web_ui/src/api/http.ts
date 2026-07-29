import axios, { type AxiosRequestConfig } from 'axios'
import { getToken } from '@/utils/auth'
import { Message } from '@/utils/message'
// 创建axios实例
const axiosInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + 'api/v1/',
  timeout: 100000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 请求拦截器
axiosInstance.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
axiosInstance.interceptors.response.use(
  response => {
    // 处理标准响应格式
    if (response.data?.code === 0) {
      return response.data?.data||response.data?.detail||response.data||response
    }
    if(response.data?.code==401){
      window.location.href = "/login"
      return Promise.reject("未登录或登录已过期，请重新登录。")
    }
    const data=response.data?.detail||response.data
    const errorMsg = data?.message || '请求失败'
    // 对于 40402（刷新限制），不显示错误消息，让调用方自己处理
    if(response.headers['content-type']==='application/json' && data?.code !== 40402) {
      Message.error(errorMsg)
    }else{
      return response.data
    }
    return Promise.reject(response.data)
  },
  error => {
     if(error.status==401 || error?.response?.status === 401){
      window.location.href = "/login"
    } 
    // console.log(error)
    // 统一错误处理
    // 对于 404 错误，返回原始 error 对象，让调用方可以检查 status
    if (error?.response?.status === 404) {
      return Promise.reject(error)
    }
    // Message.error(errorMsg)
    return Promise.reject(error)
  }
)

interface HttpClient {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
}

// Each method declares the interceptor's post-transform return type explicitly.
// The first Axios generic describes the wire payload; the second is the value
// returned after the response interceptor unwraps AxiosResponse.
const http: HttpClient = {
  get: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    axiosInstance.get<unknown, T>(url, config),
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    axiosInstance.delete<unknown, T>(url, config),
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
    axiosInstance.post<unknown, T, unknown>(url, data, config),
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
    axiosInstance.put<unknown, T, unknown>(url, data, config),
  patch: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
    axiosInstance.patch<unknown, T, unknown>(url, data, config),
}

export default http
