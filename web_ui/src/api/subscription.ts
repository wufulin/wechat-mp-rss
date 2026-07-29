import http from './http'

export interface Subscription {
  id: string
  mp_id: string
  name?: string
  mp_name: string
  mp_cover: string | null
  mp_intro: string | null
  status: number
  sync_time: string | number | null
  rss_url?: string
  article_count: number
  created_at?: string | null
  min_publish_time?: number | null
  max_publish_time?: number | null
}

export interface SubscriptionListResult {
  list: Subscription[]
  total: number
}

export interface AddSubscriptionParams {
  mp_name: string
  mp_id: string
  avatar: string
  mp_intro?: string
}

export interface WeChatArticleMetadata {
  id: string
  title: string
  author: string
  description: string
  topic_image: string
  mp_info: {
    mp_name: string
    logo: string
    biz: string
  }
}

interface SubscriptionMutationResult {
  id: string
  mp_name: string
  mp_cover: string
  mp_intro: string
  status: number
  created_at?: string
  updated_at?: string | null
  faker_id?: string
}

interface UpdateMpsResult {
  time_span: number
  list: unknown[]
  total: number
  status?: 'processing'
  message?: string
}

export interface MpItem {
  id?: string
  mp_id: string
  mp_name: string
  avatar: string
  mp_cover?: string
}

export const getSubscriptions = (params?: { page?: number; pageSize?: number; kw?: string }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10,
    kw: params?.kw || ""
  }
  return http.get<SubscriptionListResult>('/wx/mps', { params: apiParams })
}

export const getSubscriptionDetail = (mp_id: string) => {
  return http.get<Subscription>(`/wx/mps/${mp_id}`)
}

// 添加订阅公众号信息
export const addSubscription = (data: AddSubscriptionParams) => {
  return http.post<SubscriptionMutationResult>('/wx/mps', data)
}
export const getSubscriptionInfo = (url: string) => {
  return http.post<WeChatArticleMetadata>('/wx/mps/by_article', undefined, {
    params: { url }
  })
}

export const deleteMpApi = (mp_id: string) => {
  return http.delete<{message: string; id: string}>(`/wx/mps/${mp_id}`)
}

export const deleteSubscription = (mp_id: string) => {
  return http.delete<{message: string; id: string}>(`/wx/mps/${mp_id}`)
}

// 更新订阅公众号文章列表 
export const UpdateMps = (mp_id: string,params: { start_page?: number; end_page?: number }) => {
   const apiParams = {
    start_page: (params?.start_page || 0),
    end_page: params?.end_page || 1
  }
  return http.get<UpdateMpsResult>(`/wx/mps/update/${mp_id||'all'}?start_page=${apiParams.start_page}&end_page=${apiParams.end_page}`)
}

// 更新订阅公众号信息
export const updateSubscription = (mp_id: string, data: Partial<Subscription>) => {
  return http.put<SubscriptionMutationResult>(`/wx/mps/${mp_id}`, data)
}

export const searchBiz = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>(`/wx/mps/search/${kw}`,{ params: apiParams })
}

// 搜索公众号(不分页)
export const searchMps = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    kw:kw||"",
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>(`/wx/mps`,{ params: apiParams })
}
