import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function CoverPage(){
  const nav = useNavigate()
  const role=localStorage.getItem('role')
  const [title,setTitle]=useState('')
  const [area,setArea]=useState('')
  const [group,setGroup]=useState<any>(null)
  const [msg,setMsg]=useState('')
  const [err,setErr]=useState('')
  useEffect(()=>{
    client.get('/api/v1/groups/').then(r=>{
      const list=(r.data.results||r.data.data||[])
      if(list.length>0) setGroup(list[0])
    }).catch(()=>{})
  },[])
  const create=async()=>{
    if(!title.trim() || !area.trim()){ setErr('Project Title and Area are required'); return }
    setErr(''); setMsg('')
    try{
      const r=await client.post('/api/v1/groups/', {project_title: title, area})
      setMsg(`Group No. ${r.data.group_number} created — Guide: Pending Allocation`)
      setTimeout(()=>nav('/student-info'),800)
    }catch(e:any){
      const data=e.response?.data
      let friendly=''
      if(typeof data==='string' && data.includes('<!DOCTYPE')){
        friendly='Server error — please check you are logged in as Student (HOD cannot create groups via Cover) and Academic Year exists. Try logging out and registering as Student.'
      } else {
        friendly=data?.message || data?.errors?.role?.[0] || data?.errors?.group?.[0] || JSON.stringify(data) || 'Create failed'
      }
      setErr(friendly)
    }
  }
  if(role && role!=='student'){
    return <div className="max-w-2xl mx-auto p-8 bg-white rounded-xl border mt-6 text-center">
      <h1 className="text-xl font-bold">Cover Page — Students Only</h1>
      <p className="text-sm text-gray-600 mt-2">You are logged in as <b>{role.toUpperCase()}</b>. Only <b>Students</b> create groups via Cover Page. HOD allocates Guide/Reviewer via HOD dashboard, not by creating a cover.</p>
      <p className="text-xs text-gray-500 mt-2">If you are a student, please log out and register/login as Student. If you already have a group, go to <a href="/student-info" className="text-blue-600 underline">Student Info</a>.</p>
      <a href="/" className="mt-4 inline-block bg-slate-800 text-white px-6 py-2 rounded">Back to Dashboard</a>
    </div>
  }
  if(group){
    return <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold">Cover Page</h1>
      <div className="bg-green-50 p-4 rounded-xl border mt-6">
        <div className="text-sm">Group No. <b>{group.group_number}</b> (AY {group.academic_year})</div>
        <div className="text-sm">Project Title: <b>{group.project?.title}</b></div>
        <div className="text-sm">Area: {group.project?.area_domain}</div>
        <div className="text-sm">Guide: <b>Pending Guide Allocation</b> (HOD assigns)</div>
      </div>
      <p className="text-xs text-gray-500 mt-3">Cover already created — next: fill Student Info for all 4 members.</p>
      <button onClick={()=>nav('/student-info')} className="mt-4 bg-blue-600 text-white px-6 py-2 rounded">Go to Student Section →</button>
      {err&&<div className="text-sm text-red-600 bg-red-50 p-3 rounded mt-3">{err}</div>}
      {msg&&<div className="text-sm text-green-600 bg-green-50 p-3 rounded mt-3">{msg}</div>}
    </div>
  }
  return <div className="max-w-2xl mx-auto">
    <h1 className="text-2xl font-bold">Cover Page</h1>
    <p className="text-xs text-gray-500 mt-1">First step after register — Group No. auto-assigned per AY/Department, Guide shows Pending until HOD assigns. This mirrors official logbook Cover.</p>
    <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-4">
      <label className="text-sm font-semibold">Project Title <span className="text-red-500">*</span> <span className="text-gray-400 font-normal">(two-line as in cover)</span></label>
      <textarea className="border p-3 rounded" rows={2} value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g., AI Based Logbook System"/>
      <label className="text-sm font-semibold">Area of Project <span className="text-red-500">*</span></label>
      <input className="border p-3 rounded" value={area} onChange={e=>setArea(e.target.value)} placeholder="e.g., AI/ML, IoT, Web"/>
      <div className="text-xs text-gray-500">Group No. will be auto-assigned (e.g., 07) — read-only. Guide: <b>Pending Guide Allocation</b> — not editable by student.</div>
      <button onClick={create} className="bg-blue-600 text-white p-3 rounded">Create Cover — Next: Student Info</button>
      {err&&<div className="text-sm text-red-600 bg-red-50 p-3 rounded">{err}</div>}
      {msg&&<div className="text-sm text-green-600 bg-green-50 p-3 rounded">{msg}</div>}
    </div>
  </div>
}
