import http from './http'
export const uploadFile = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<{url: string}>('/wx/user/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
