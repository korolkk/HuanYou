import client from './client'

export const authApi = {
  login: (phone: string, password: string) =>
    client.post('/auth/login', { phone, password }).then(r => r.data),

  register: (data: { phone: string; name: string; password: string; role: string }) =>
    client.post('/auth/register', data).then(r => r.data),

  getMe: () =>
    client.get('/auth/me').then(r => r.data),

  updateMe: (data: Record<string, unknown>) =>
    client.put('/auth/me', data).then(r => r.data),

  changePassword: (oldPassword: string, newPassword: string) =>
    client.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
}

export const tripApi = {
  list: (params?: Record<string, unknown>) =>
    client.get('/shop/trips', { params }).then(r => r.data),

  get: (id: string) =>
    client.get(`/shop/trips/${id}`).then(r => r.data),

  create: (data: Record<string, unknown>) =>
    client.post('/shop/trips', data).then(r => r.data),

  update: (id: string, data: Record<string, unknown>) =>
    client.put(`/shop/trips/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    client.delete(`/shop/trips/${id}`),
}

export const orderApi = {
  myOrders: (params?: Record<string, unknown>) =>
    client.get('/user/orders', { params }).then(r => r.data),

  create: (data: Record<string, unknown>) =>
    client.post('/user/orders', data).then(r => r.data),

  get: (id: string) =>
    client.get(`/user/orders/${id}`).then(r => r.data),

  submitFeedback: (orderId: string, data: Record<string, unknown>) =>
    client.post(`/user/orders/${orderId}/feedback`, data).then(r => r.data),
}

export const agentApi = {
  chat: (message: string, sessionId?: string) =>
    client.post('/agent/chat', null, { params: { message, session_id: sessionId } }).then(r => r.data),
}

export const scriptApi = {
  list: (params?: Record<string, unknown>) =>
    client.get('/shop/scripts', { params }).then(r => r.data),

  get: (id: string) =>
    client.get(`/shop/scripts/${id}`).then(r => r.data),

  generate: (data: { trip_id: string; platform?: string; duration_seconds?: number; style?: string }) =>
    client.post('/shop/scripts/generate', data).then(r => r.data),

  polish: (id: string, data: { focus_areas?: string[]; target_segment_index?: number }) =>
    client.post(`/shop/scripts/${id}/polish`, data).then(r => r.data),

  evaluate: (id: string) =>
    client.post(`/shop/scripts/${id}/evaluate`).then(r => r.data),

  exportCapcut: (id: string, data?: { include_images?: boolean; resolution?: string }) =>
    client.post(`/shop/scripts/${id}/export/capcut`, data || {}, {
      responseType: 'blob',
      timeout: 60000,
    }).then(r => {
      const disposition = r.headers['content-disposition'] || ''
      const match = disposition.match(/filename="?(.+?)"?$/i)
      const filename = match?.[1] || 'capcut_draft.zip'
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url; a.download = filename
      a.click(); URL.revokeObjectURL(url)
      return { filename, draft_id: r.headers['x-draft-id'] || '' }
    }),

  getExportStatus: (id: string) =>
    client.get(`/shop/scripts/${id}/export/capcut/status`).then(r => r.data),
}

export const importApi = {
  uploadFile: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/shop/import/trip-file', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    }).then(r => r.data)
  },

  downloadTemplate: () =>
    client.get('/shop/import/template/trip-import', { responseType: 'blob' }).then(r => {
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url; a.download = 'huanyou_trip_import_template.xlsx'
      a.click(); URL.revokeObjectURL(url)
    }),
}
