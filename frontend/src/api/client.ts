import axios from 'axios'
const client = axios.create({ baseURL: 'http://localhost:8000' })
client.interceptors.request.use(c => {
  const t = localStorage.getItem('access')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})
client.interceptors.response.use(r=>r, async err => {
  const url=err.config?.url||''
  if (err.response?.status===401 && localStorage.getItem('refresh') && !url.includes('/auth/login/') && !url.includes('/auth/register/') && !url.includes('/auth/token/refresh/')) {
    try {
      const res = await axios.post('http://localhost:8000/api/v1/auth/token/refresh/', { refresh: localStorage.getItem('refresh') })
      localStorage.setItem('access', res.data.access)
      err.config.headers.Authorization = `Bearer ${res.data.access}`
      return axios(err.config)
    } catch { localStorage.clear(); location.href='/login' }
  }
  return Promise.reject(err)
})
export default client
