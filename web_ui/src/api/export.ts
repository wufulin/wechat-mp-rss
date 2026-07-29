import http from './http'

export interface ImportResult {
  message: string
  stats: {
    total?: number
    total_rows?: number
    imported: number
    updated: number
    skipped: number
  }
}

export const ExportOPML = () => {
  return http.get<string>('/wx/export/mps/opml', {
    params: {
      limit: 1000,
      offset: 0
    }
  })
}

export const ExportMPS = () => {
  return http.get<Blob>('/wx/export/mps/export', {
    params: { limit: 1000, offset: 0 },
    responseType: 'blob',
  });
};

export const ImportMPS = (formData: FormData) => {
  return http.post<ImportResult>('/wx/export/mps/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const ExportTags = () => {
  return http.get<Blob>('/wx/export/tags', {
    params: { limit: 1000, offset: 0 },
    responseType: 'blob',
  });
};

export const ImportTags = (formData: FormData) => {
  return http.post<ImportResult>('/wx/export/tags/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
