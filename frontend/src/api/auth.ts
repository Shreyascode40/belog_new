import client from './client'
export const login = (email:string,password:string)=> client.post('/api/v1/auth/login/',{email,password}).then(r=>r.data)
export const register = (data:any)=> client.post('/api/v1/auth/register/',data).then(r=>r.data)
export const me = ()=> client.get('/api/v1/auth/me/').then(r=>r.data)
