import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/auth'
export default function Login(){
  const [email,setEmail]=useState('hod@college.edu')
  const [password,setPassword]=useState('pass1234')
  const [err,setErr]=useState('')
  const nav=useNavigate()
  const submit=async(e:any)=>{
    e.preventDefault()
    try{
      const r=await login(email,password)
      localStorage.setItem('access', r.tokens.access)
      localStorage.setItem('refresh', r.tokens.refresh)
      localStorage.setItem('role', r.data.role)
      localStorage.setItem('email', r.data.email)
      nav('/')
    } catch(e:any){ setErr(e.response?.data?.message||'Login failed') }
  }
  return <div className="min-h-screen flex items-center justify-center bg-slate-900">
    <form onSubmit={submit} className="bg-white p-8 rounded-2xl w-full max-w-sm flex flex-col gap-4">
      <h1 className="text-2xl font-bold">BE Logbook Login</h1>
      <p className="text-xs text-gray-500">HOD: hod@college.edu / pass1234 | Student: s1@student.edu / pass1234 | Faculty: guide1@college.edu / pass1234</p>
      <input className="border p-2 rounded" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/>
      <input className="border p-2 rounded" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password"/>
      {err&&<div className="text-red-600 text-sm">{err}</div>}
      <button className="bg-blue-600 text-white p-2 rounded">Login</button>
      <Link to="/register" className="text-sm text-blue-600 text-center">Create account</Link>
    </form>
  </div>
}
