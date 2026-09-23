// '??' (pas '||') : une VITE_API_URL vide en prod doit rester vide (chemins
// relatifs, même origine que nginx), seule l'absence de la variable (dev
// sans build) retombe sur le serveur local.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { token, ...opts } = {}) {
  const headers = { ...(opts.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...opts, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // corps non-JSON, on garde statusText
    }
    throw new ApiError(detail, res.status)
  }
  if (res.status === 204) return null
  return res.json()
}

export function login(username, password) {
  return request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
}

export function register(username, password) {
  return request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
}

export function getMe(token) {
  return request('/auth/me', { token })
}

export function listUsers(token, { status } = {}) {
  const params = status ? `?status=${status}` : ''
  return request(`/admin/users${params}`, { token })
}

export function approveUser(token, userId) {
  return request(`/admin/users/${userId}/approve`, { method: 'POST', token })
}

export function rejectUser(token, userId) {
  return request(`/admin/users/${userId}/reject`, { method: 'POST', token })
}

export function listInvoices(token, { page = 1, pageSize = 20, paymentStatus } = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize })
  if (paymentStatus) params.set('payment_status', paymentStatus)
  return request(`/invoices?${params}`, { token })
}

export function getInvoice(token, invoiceId) {
  return request(`/invoices/${invoiceId}`, { token })
}

export function listDocuments(token, { page = 1, pageSize = 20, docType } = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize })
  if (docType) params.set('doc_type', docType)
  return request(`/documents?${params}`, { token })
}

export function uploadDocument(token, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/upload', { method: 'POST', body: formData, token })
}

export function askChat(token, question) {
  return request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    token,
  })
}
