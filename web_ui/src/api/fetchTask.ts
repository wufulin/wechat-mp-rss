import http from './http'
import type { FetchTask, FetchTaskCreate } from '@/types/fetchTask'

interface FetchTaskListResult {
  list: FetchTask[]
  page: {
    offset: number
    limit: number
  }
  total: number
}

interface ActionResponse {
  code: number
  message: string
}

export const listFetchTasks = (params?: { offset?: number; limit?: number }) => {
  const apiParams = {
    offset: params?.offset || 0,
    limit: params?.limit || 10,
  }
  return http.get<FetchTaskListResult>('/wx/fetch_tasks', { params: apiParams })
}

export const getFetchTask = (id: string) => {
  return http.get<FetchTask>(`/wx/fetch_tasks/${id}`)
}

export const createFetchTask = (data: FetchTaskCreate) => {
  return http.post<FetchTask>('/wx/fetch_tasks', data)
}

export const updateFetchTask = (id: string, data: FetchTaskCreate) => {
  return http.put<FetchTask>(`/wx/fetch_tasks/${id}`, data)
}

export const deleteFetchTask = (id: string) => {
  return http.delete<ActionResponse>(`/wx/fetch_tasks/${id}`)
}

export const runFetchTask = (id: string) => {
  return http.get<{count: number}>(`/wx/fetch_tasks/${id}/run`)
}

export const reloadFetchJobs = () => {
  return http.put<ActionResponse>(`/wx/fetch_tasks/job/fresh`)
}
