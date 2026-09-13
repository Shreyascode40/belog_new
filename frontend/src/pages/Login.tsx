import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/auth'
export default function Login(){
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [err,setErr]=useState('')
  const [loading,setLoading]=useState(false)
  const nav=useNavigate()
  const submit=async(e:any)=>{
    e.preventDefault()
    setErr('')
    const em=email.trim().toLowerCase()
    if(!em || !password){ setErr('Email and password are required'); return }
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)){ setErr('Enter a valid email'); return }
    setLoading(true)
    try{
      const r=await login(em,password)
      localStorage.setItem('access', r.tokens.access)
      localStorage.setItem('refresh', r.tokens.refresh)
      localStorage.setItem('role', r.data.role)
      localStorage.setItem('email', r.data.email)
      nav('/')
    } catch(e:any){
      const d=e.response?.data
      const msg=d?.message || d?.errors?.email?.[0] || d?.errors?.password?.[0] || d?.errors?.detail?.[0]
      if(d?.message==='Invalid credentials') setErr('Invalid email or password')
      else if(typeof msg==='string' && msg) setErr(msg)
      else if(typeof d==='string' && d.includes('<!DOCTYPE')) setErr('Server not reachable — is backend running on http://localhost:8000?')
      else setErr('Login failed — check email / password')
    } finally{ setLoading(false) }
  }
  return <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
    <form onSubmit={submit} noValidate className="bg-white p-8 rounded-2xl w-full max-w-sm flex flex-col gap-4">
      <h1 className="text-2xl font-bold">BE Logbook Login</h1>
      <p className="text-xs text-gray-500">HOD: hod@college.edu / pass1234 · Student: s1@student.edu / pass1234 · Faculty: guide1@college.edu / pass1234</p>
      <label className="text-xs font-medium">Email<input className="border p-2.5 rounded w-full mt-1" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@college.edu" autoComplete="email" /></label>
      <label className="text-xs font-medium">Password<input className="border p-2.5 rounded w-full mt-1" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" autoComplete="current-password" /></label>
      {err&&<div className="text-red-600 text-sm bg-red-50 border border-red-200 p-2.5 rounded">{err}</div>}
      <button disabled={loading} className="bg-blue-600 text-white p-2.5 rounded font-medium disabled:opacity-50">{loading?'Signing in...':'Login'}</button>
      <Link to="/register" className="text-sm text-blue-600 text-center">Create account</Link>
    </form>
  </div>
}
