import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { register } from '../api/auth'
export default function Register(){
  const [form,setForm]=useState({username:'',email:'',password:'',role:'student'})
  const [err,setErr]=useState('')
  const nav=useNavigate()
  const submit=async(e:any)=>{
    e.preventDefault()
    try{ const r=await register(form); localStorage.setItem('access',r.tokens.access); localStorage.setItem('refresh',r.tokens.refresh); localStorage.setItem('role',r.data.role); localStorage.setItem('email',r.data.email); nav(r.data.role==='student'?'/cover':'/')}catch(e:any){setErr(JSON.stringify(e.response?.data))}
  }
  return <div className="min-h-screen flex items-center justify-center bg-slate-900">
    <form onSubmit={submit} className="bg-white p-6 rounded-xl w-full max-w-sm flex flex-col gap-3">
      <h1 className="text-xl font-bold">Register</h1>
      <input className="border p-2 rounded" placeholder="Username" onChange={e=>setForm({...form,username:e.target.value})}/>
      <input className="border p-2 rounded" placeholder="Email" onChange={e=>setForm({...form,email:e.target.value})}/>
      <input className="border p-2 rounded" type="password" placeholder="Password" onChange={e=>setForm({...form,password:e.target.value})}/>
      <select className="border p-2 rounded" onChange={e=>setForm({...form,role:e.target.value})} value={form.role}><option value="student">Student</option><option value="faculty">Faculty</option><option value="hod">HOD</option></select>
      {err&&<div className="text-red-600 text-xs">{err}</div>}
      <button className="bg-blue-600 text-white p-2 rounded">Create</button>
    </form>
  </div>
}
