import { useEffect, useState } from 'react'
import client from '../api/client'

export default function HODAllocate(){
  const [groups,setGroups]=useState<any[]>([])
  const [faculty,setFaculty]=useState<any[]>([])
  const [selectedGroup,setSelectedGroup]=useState('')
  const [selectedFaculty,setSelectedFaculty]=useState('')
  const [msg,setMsg]=useState('')
  const [newUser,setNewUser]=useState({name:'',email:'',password:''})
  const [addMsg,setAddMsg]=useState('')
  const [hasReviewer,setHasReviewer]=useState(false)

  const loadGroups=async()=>{
    const r=await client.get('/api/v1/groups/')
    setGroups(r.data.results||r.data.data||[])
  }
  const loadFaculty=async()=>{
    // load all faculty-like users (faculty, reviewer, hod can act as guide/reviewer)
    const r=await client.get('/api/v1/users/')
    const all=(r.data.results||r.data.data||[])
    const fac=all.filter((u:any)=>['faculty','reviewer','hod','admin'].includes(u.role))
    setFaculty(fac)
  }
  useEffect(()=>{ loadGroups(); loadFaculty() },[])
  useEffect(()=>{
    const p=new URLSearchParams(location.search)
    if(p.get('group')) setSelectedGroup(p.get('group')!)
  },[])
  useEffect(()=>{
    if(!selectedGroup){ setHasReviewer(false); return }
    const check=async()=>{
      try{
        const r=await client.get(`/api/v1/reviewer-assignments/?group=${selectedGroup}`)
        const list=(r.data.results||r.data.data||[])
        setHasReviewer(list.length>0)
        if(list.length>0) setAddMsg('')
      }catch{ setHasReviewer(false) }
    }
    check()
  },[selectedGroup])

  const addFaculty=async()=>{
    if(!newUser.email || !newUser.password || !newUser.name){ setAddMsg('Name, Email, Password required'); return }
    try{
      const username=newUser.email.split('@')[0]
      const r=await client.post('/api/v1/users/', {username, email:newUser.email, password:newUser.password, first_name:newUser.name, role:'faculty', is_active:true})
      try{ await client.post('/api/v1/faculty/', {user: r.data.id, employee_id:`EMP${Date.now().toString().slice(-6)}`, name: newUser.name, designation:'Faculty', department:'Computer Engineering'}) }catch{}
      setAddMsg(`Added ${newUser.name} (${newUser.email}) — same user can be Guide or Reviewer — now shows below`)
      setNewUser({name:'',email:'',password:''})
      // immediately show in dropdown without needing refresh
      setFaculty(prev=>[...prev, r.data])
    }catch(e:any){ setAddMsg(e.response?.data?.email?.[0]||e.response?.data?.username?.[0]||JSON.stringify(e.response?.data)||'Add failed') }
  }

  const assignSame=async()=>{
    if(!selectedGroup || !selectedFaculty){ setMsg('Select group and faculty'); return }
    const gid=Number(selectedGroup), fid=Number(selectedFaculty)
    const g=groups.find(x=>x.id===gid)
    const facEmail=faculty.find(f=>f.id===fid)?.email
    try{
      await client.post('/api/v1/guide-assignments/', {group: gid, faculty: fid, academic_year: g.academic_year}).catch((e:any)=>{
        if(e.response?.status!==400) throw e
      })
      await client.post('/api/v1/reviewer-assignments/', {group: gid, faculty: fid, academic_year: g.academic_year, review_number: 1}).catch((e:any)=>{
        if(e.response?.status!==400) throw e
      })
      setMsg(`Guide & Reviewer are SAME — Group ${g.group_number} → ${facEmail} assigned as both Guide and Reviewer`)
    }catch(e:any){ setMsg(e.response?.data?.message||JSON.stringify(e.response?.data)||'Already assigned as both') }
  }

  return <div className="max-w-3xl mx-auto">
    <h1 className="text-2xl font-bold">HOD — Guide / Reviewer</h1>
    <p className="text-xs text-gray-500 mt-1">Simple: add one faculty account, then use same account as Guide or Reviewer for any group.</p>

    {!hasReviewer ? <div className="bg-white p-6 rounded-xl border mt-6">
      <h2 className="font-semibold">Add Guide / Reviewer (same user)</h2>
      <p className="text-xs text-gray-500">One account works as both Guide and Reviewer — no separate reviewer creation needed.</p>
      <div className="grid grid-cols-1 gap-3 mt-3">
        <input className="border p-2 rounded text-sm" placeholder="Full Name *" value={newUser.name} onChange={e=>setNewUser({...newUser, name:e.target.value})} />
        <input className="border p-2 rounded text-sm" placeholder="Email * (will be username)" value={newUser.email} onChange={e=>setNewUser({...newUser, email:e.target.value})} />
        <input className="border p-2 rounded text-sm" type="password" placeholder="Password *" value={newUser.password} onChange={e=>setNewUser({...newUser, password:e.target.value})} />
      </div>
      <button onClick={addFaculty} className="mt-3 bg-indigo-600 text-white px-6 py-2 rounded w-full">Add Faculty / Reviewer</button>
      {addMsg&&<div className="text-sm p-2 rounded bg-green-50 text-green-700 mt-2">{addMsg}</div>}
    </div> : <div className="bg-green-50 p-4 rounded-xl border mt-6 text-sm text-green-700">Reviewer already allocated for Group {groups.find(g=>String(g.id)===selectedGroup)?.group_number||selectedGroup} — no need to add another.</div>}

    <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-3">
      <h2 className="font-semibold">Give Permission to Group</h2>
      <p className="text-xs text-gray-500">Pick group and faculty — same list for Guide and Reviewer.</p>
      <label className="text-sm font-semibold">Group *</label>
      <select className="border p-2 rounded" value={selectedGroup} onChange={e=>setSelectedGroup(e.target.value)}>
        <option value="">Select Group</option>
        {groups.map((g:any)=><option key={g.id} value={g.id}>Group {g.group_number} — {g.project?.title||''}</option>)}
      </select>
      <label className="text-sm font-semibold">Faculty (Guide / Reviewer) *</label>
      <select className="border p-2 rounded" value={selectedFaculty} onChange={e=>setSelectedFaculty(e.target.value)}>
        <option value="">Select Faculty</option>
        {faculty.map((f:any)=><option key={f.id} value={f.id}>{f.first_name||f.username} — {f.email} ({f.role})</option>)}
      </select>
      <button onClick={assignSame} className="bg-blue-600 text-white p-3 rounded w-full">Assign as Guide & Reviewer — SAME PERSON</button>
      <div className="text-xs text-gray-500 text-center">One faculty will be both Guide and Reviewer for this group (no separate persons)</div>
      {msg&&<div className="text-sm p-3 rounded bg-amber-50 text-amber-700">{msg}</div>}
      <div className="text-xs text-gray-500">Only HOD can assign. Check result in HOD — All Groups detail.</div>
    </div>
  </div>
}
