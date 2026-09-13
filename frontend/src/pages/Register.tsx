import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/auth'
export default function Register(){
  const [form,setForm]=useState({username:'',email:'',password:'',role:'student'})
  const [err,setErr]=useState('')
  const [fieldErr,setFieldErr]=useState<Record<string,string>>({})
  const [loading,setLoading]=useState(false)
  const nav=useNavigate()
  const validate=()=>{
    const fe:Record<string,string>={}
    const em=form.email.trim().toLowerCase()
    if(!em) fe.email='Email is required'
    else if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) fe.email='Enter a valid email'
    if(!form.password) fe.password='Password is required'
    else if(form.password.length<6) fe.password='Password must be at least 6 characters'
    if(form.username && form.username.length<3) fe.username='Username must be at least 3 characters'
    if(!['student','faculty','hod','reviewer'].includes(form.role)) fe.role='Invalid role'
    setFieldErr(fe)
    return Object.keys(fe).length===0
  }
  const submit=async(e:any)=>{
    e.preventDefault()
    setErr('')
    if(!validate()) return
    setLoading(true)
    try{
      const payload={username:(form.username.trim()||form.email.trim().toLowerCase().split('@')[0]), email:form.email.trim().toLowerCase(), password:form.password, role:form.role}
      const r=await register(payload)
      localStorage.setItem('access',r.tokens.access)
      localStorage.setItem('refresh',r.tokens.refresh)
      localStorage.setItem('role',r.data.role)
      localStorage.setItem('email',r.data.email)
      nav(r.data.role==='student'?'/cover':'/')
    }catch(e:any){
      const d=e.response?.data
      if(typeof d==='string' && d.includes('<!DOCTYPE')){
        setErr('Server error — is backend running on http://localhost:8000?')
      } else if(d?.errors){
        const fe:Record<string,string>={}
        for(const k of Object.keys(d.errors)){ const v=d.errors[k]; fe[k]=Array.isArray(v)?v[0]:String(v) }
        setFieldErr(fe)
        setErr(d.message || fe.email || fe.username || 'Registration failed')
      } else {
        setErr(d?.message || 'Registration failed — email may already exist, try Login.')
      }
    } finally{ setLoading(false) }
  }
  return <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
    <form onSubmit={submit} noValidate className="bg-white p-6 rounded-xl w-full max-w-sm flex flex-col gap-3">
      <h1 className="text-xl font-bold">Create Account</h1>
      <label className="text-xs font-medium">Username <span className="text-gray-400 font-normal">(optional — auto from email)</span><input className="border p-2.5 rounded w-full mt-1" placeholder="s1" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/>{fieldErr.username&&<span className="text-xs text-red-600">{fieldErr.username}</span>}</label>
      <label className="text-xs font-medium">Email *<input className="border p-2.5 rounded w-full mt-1" placeholder="you@college.edu" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>{fieldErr.email&&<span className="text-xs text-red-600">{fieldErr.email}</span>}</label>
      <label className="text-xs font-medium">Password *<input className="border p-2.5 rounded w-full mt-1" type="password" placeholder="min 6 characters" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>{fieldErr.password&&<span className="text-xs text-red-600">{fieldErr.password}</span>}</label>
      <label className="text-xs font-medium">Role<select className="border p-2.5 rounded w-full mt-1" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option value="student">Student</option><option value="faculty">Faculty</option><option value="hod">HOD</option><option value="reviewer">Reviewer</option></select></label>
      {err&&<div className="text-red-600 text-xs bg-red-50 border border-red-200 p-2.5 rounded">{err}</div>}
      <button disabled={loading} className="bg-blue-600 text-white p-2.5 rounded font-medium disabled:opacity-50">{loading?'Creating...':'Create Account'}</button>
      <Link to="/login" className="text-sm text-blue-600 text-center">Already have an account? Login</Link>
    </form>
  </div>
}
