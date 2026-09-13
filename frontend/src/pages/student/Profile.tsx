import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function StudentProfile(){
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  const [editing,setEditing]=useState(false)
  const [form,setForm]=useState<any>({})
  const [saving,setSaving]=useState(false)
  const [msg,setMsg]=useState('')
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get('/api/v1/student/profile/')
      setData(r.data.data)
      setForm(r.data.data.profile||{name:'',roll_number:'',mobile:'',exam_seat_number:'',email:r.data.data.user.email,department:''})
    }catch(e:any){setError(e.response?.data?.message||'Unable to load profile')}
    setLoading(false)
  }
  useEffect(()=>{load()},[])
  const save=async()=>{
    setSaving(true);setMsg('')
    try{
      const r=await client.patch('/api/v1/student/profile/', form)
      // if email changed update localStorage
      if(form.email) localStorage.setItem('email', form.email)
      setMsg('Profile updated')
      setEditing(false)
      load()
    }catch(e:any){
      setMsg(e.response?.data?.errors? JSON.stringify(e.response.data.errors) : e.response?.data?.message || 'Save failed')
    }
    setSaving(false)
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading your profile...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error} <button onClick={load} className="ml-2 border px-3 py-1 rounded">Retry</button></div>
  const p=data.profile
  const u=data.user
  return <div className="max-w-3xl mx-auto">
    <h1 className="text-xl font-bold">My Profile</h1>
    <p className="text-xs text-gray-500">Your academic profile — editing controlled by backend permissions</p>
    <div className="bg-white border rounded-xl p-6 mt-4">
      {!editing ? <>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><div className="text-xs text-gray-400">Full Name</div><div className="font-medium">{p?.name||u.first_name||u.username||'-'}</div></div>
          <div><div className="text-xs text-gray-400">PRN / Roll</div><div className="font-medium">{p?.roll_number||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Email</div><div className="font-medium">{p?.email||u.email}</div></div>
          <div><div className="text-xs text-gray-400">Department</div><div className="font-medium">{p?.department||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Academic Year</div><div className="font-medium">{p?.academic_year||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Semester</div><div className="font-medium">{p?.semester||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Phone</div><div className="font-medium">{p?.mobile||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Role</div><div className="font-medium capitalize">{u.role}</div></div>
        </div>
        {p?.photograph && <img src={p.photograph} alt="photo" className="w-24 h-32 object-cover border rounded mt-4"/>}
        <button onClick={()=>setEditing(true)} className="mt-6 bg-blue-600 text-white px-4 py-2 rounded text-sm">Edit Profile</button>
      </> : <>
        <div className="grid grid-cols-2 gap-4">
          {[
            ['name','Full Name','text'],
            ['roll_number','PRN / Roll','text'],
            ['email','Email','email'],
            ['mobile','Phone','text'],
            ['exam_seat_number','Exam Seat No','text'],
            ['department','Department','text'],
          ].map(([k,label,type])=><label key={k} className="text-xs font-medium">{label}<input type={type} value={form[k]||''} onChange={e=>setForm({...form,[k]:e.target.value})} className="mt-1 w-full border rounded p-2 text-sm"/></label>)}
          <label className="text-xs font-medium col-span-2">Photo<input type="file" accept="image/*" onChange={e=>{
            const f=e.target.files?.[0]; if(f) setForm({...form, photograph:f})
          }} className="mt-1 w-full border rounded p-2 text-sm"/></label>
        </div>
        <div className="text-xs text-amber-600 mt-3">Role cannot be changed — controlled by backend.</div>
        <div className="flex gap-2 mt-4">
          <button onClick={save} disabled={saving} className="bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50">{saving?'Saving...':'Save'}</button>
          <button onClick={()=>setEditing(false)} className="border px-4 py-2 rounded text-sm">Cancel</button>
        </div>
      </>}
      {msg && <div className="mt-3 text-sm p-3 bg-green-50 border border-green-200 rounded text-green-700">{msg}</div>}
    </div>
  </div>
}
