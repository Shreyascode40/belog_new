import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function StudentInfo(){
  const nav=useNavigate()
  const [group,setGroup]=useState<any>(null)
  const [members,setMembers]=useState<any[]>([])
  const [msg,setMsg]=useState('')
  const [newMember,setNewMember]=useState({name:'', roll_number:'', mobile:'', exam_seat_number:'', email:'', te_result:'', contribution:''})

  const load=async()=>{
    const gRes=await client.get('/api/v1/groups/')
    const g=(gRes.data.results||gRes.data.data||[])[0]
    if(!g){ setMsg('No cover yet — create cover first'); return }
    setGroup(g)
    const mRes=await client.get(`/api/v1/groups/${g.id}/`)
    setMembers(mRes.data.members||[])
  }
  useEffect(()=>{ load() },[])

  const updateProfile=async(m:any, field:string, value:string)=>{
    if(!m.student_detail?.id) return
    try{
      await client.patch(`/api/v1/students/${m.student_detail.id}/`, {[field]: value})
      setMsg(`Updated ${field} — will be fetched automatically next time`)
      load()
    }catch{ setMsg('Profile update failed') }
  }
  const updateMember=async(m:any, field:string, value:string)=>{
    try{
      await client.patch(`/api/v1/group-members/${m.id}/`, {[field]: value})
      load()
    }catch{ setMsg('Update failed') }
  }
  const addMemberDirect=async()=>{
    if(!newMember.email || !newMember.name || !newMember.roll_number){
      setMsg('Name, Roll No., Email required for new member')
      return
    }
    try{
      await client.post(`/api/v1/groups/${group.id}/add-member-direct/`, newMember)
      setMsg(`Member ${newMember.name} added directly — no invite needed`)
      setNewMember({name:'', roll_number:'', mobile:'', exam_seat_number:'', email:'', te_result:'', contribution:''})
      load()
    }catch(e:any){ setMsg(e.response?.data?.message||JSON.stringify(e.response?.data)||'Add failed — need exactly 4 members') }
  }
  const acknowledge=async()=>{
    await client.post(`/api/v1/groups/${group.id}/acknowledge/`, {})
    setMsg('You acknowledged — Digitally Acknowledged')
    load()
  }
  const submit=async()=>{
    try{
      const r=await client.post(`/api/v1/groups/${group.id}/submit-information/`)
      setMsg('Submitted — guide/HOD notified, awaiting AccessGrant. Other levels will unlock after approval.')
      setTimeout(()=>nav('/'),1000)
    }catch(e:any){ setMsg(e.response?.data?.message||JSON.stringify(e.response?.data?.errors)||'Submit failed — need exactly 4 members, all fields, all acknowledged') }
  }

  if(!group) return <div className="max-w-3xl mx-auto p-8 bg-white rounded-xl border mt-6">No cover yet — <a href="/cover" className="text-blue-600 underline">Go to Cover Page</a> to create Group No. first. {msg&&<div className="text-sm text-amber-600 mt-2">{msg}</div>}</div>

  return <div className="max-w-4xl mx-auto">
    <h1 className="text-2xl font-bold">Student Section — Member Info</h1>
    <p className="text-xs text-gray-500 mt-1">Separate section (not in sidebar) — fill all 4 members directly here. No invite system — just fill fields like registration. If project title given but member info blank, it auto-fetches from registration.</p>
    <div className="bg-blue-50 p-3 rounded text-sm mt-4">Group No. <b>{group.group_number}</b> — Project: <b>{group.project?.title}</b> — Guide: <b>Pending</b> — Fill exactly 4 members to unlock other levels. Members shown below are editable like registration.</div>

    <div className="flex flex-col gap-4 mt-6">
      {members.map((m:any,idx:number)=>(
        <div key={m.id} className="border rounded-xl p-4 bg-white">
          <div className="font-semibold text-sm mb-2">Member {idx+1} {m.role==='leader'?'— Leader (You)':''} {m.acknowledged?'✓ Acknowledged':''} — {m.student_detail?.name||''}</div>
          <div className="text-xs text-green-600 mb-2">All fields like registration — Name*, Roll No.*, Mobile*, Exam Seat*, Email*, TE Result*, Contribution, Photo* — fetched automatically if blank.</div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col"><label className="text-xs font-semibold">Name *</label><input className="border p-2 rounded text-sm" defaultValue={m.student_detail?.name||''} placeholder="Full name" onBlur={e=>updateProfile(m,'name',e.target.value)} /></div>
            <div className="flex flex-col"><label className="text-xs font-semibold">Roll No. *</label><input className="border p-2 rounded text-sm" defaultValue={m.student_detail?.roll_number||''} placeholder="41001" onBlur={e=>updateProfile(m,'roll_number',e.target.value)} /></div>
            <div className="flex flex-col"><label className="text-xs font-semibold">TE Result *</label><input className="border p-2 rounded text-sm" defaultValue={m.te_result||''} placeholder="Distinction / First Class" onBlur={e=>updateMember(m,'te_result',e.target.value)} /></div>
            <div className="flex flex-col"><label className="text-xs font-semibold">Mobile No. *</label><input className="border p-2 rounded text-sm" defaultValue={m.student_detail?.mobile||''} placeholder="10-digit" onBlur={e=>updateProfile(m,'mobile',e.target.value)} /></div>
            <div className="flex flex-col"><label className="text-xs font-semibold">Exam Seat No. *</label><input className="border p-2 rounded text-sm" defaultValue={m.student_detail?.exam_seat_number||''} placeholder="SEAT..." onBlur={e=>updateProfile(m,'exam_seat_number',e.target.value)} /></div>
            <div className="flex flex-col"><label className="text-xs font-semibold">Email ID *</label><input className="border p-2 rounded text-sm bg-gray-100" value={m.student_detail?.email||''} readOnly /></div>
            <div className="flex flex-col col-span-2"><label className="text-xs font-semibold">Contribution</label><input className="border p-2 rounded text-sm" defaultValue={m.contribution||''} placeholder="Backend, Testing..." onBlur={e=>updateMember(m,'contribution',e.target.value)} /></div>
            <div className="flex flex-col col-span-2"><label className="text-xs font-semibold">Photo * (Affix your photo here)</label><input type="file" accept="image/*" className="border p-2 rounded text-sm" onChange={e=>{ if(e.target.files?.[0]) setMsg(`Photo ${e.target.files[0].name} selected — will be DOCUMENT type STUDENT_PHOTO`)}} /></div>
          </div>
          <div className="text-xs mt-2">Status: <b>{m.status}</b> — {m.acknowledged?`Ack ${new Date(m.acknowledged_at).toLocaleDateString()}`:'Not acknowledged — each member must individually acknowledge undertaking'}</div>
        </div>
      ))}
      {members.length<4 && <div className="border-2 border-dashed rounded-xl p-4 bg-amber-50">
        <div className="font-semibold text-sm">Add Member {members.length+1} — Fill directly (no invite)</div>
        <p className="text-xs text-gray-500">Fill like registration — all fields required. This directly adds the member, no accept needed.</p>
        <div className="grid grid-cols-2 gap-3 mt-3">
          <input className="border p-2 rounded text-sm" placeholder="Name *" value={newMember.name} onChange={e=>setNewMember({...newMember, name:e.target.value})} />
          <input className="border p-2 rounded text-sm" placeholder="Roll No. * " value={newMember.roll_number} onChange={e=>setNewMember({...newMember, roll_number:e.target.value})} />
          <input className="border p-2 rounded text-sm" placeholder="TE Result *" value={newMember.te_result} onChange={e=>setNewMember({...newMember, te_result:e.target.value})} />
          <input className="border p-2 rounded text-sm" placeholder="Mobile *" value={newMember.mobile} onChange={e=>setNewMember({...newMember, mobile:e.target.value})} />
          <input className="border p-2 rounded text-sm" placeholder="Exam Seat No. *" value={newMember.exam_seat_number} onChange={e=>setNewMember({...newMember, exam_seat_number:e.target.value})} />
          <input className="border p-2 rounded text-sm" placeholder="Email *" value={newMember.email} onChange={e=>setNewMember({...newMember, email:e.target.value})} />
          <input className="border p-2 rounded text-sm col-span-2" placeholder="Contribution" value={newMember.contribution} onChange={e=>setNewMember({...newMember, contribution:e.target.value})} />
        </div>
        <button onClick={addMemberDirect} className="mt-3 bg-blue-600 text-white px-6 py-2 rounded w-full">Add Member Directly</button>
      </div>}
      {members.length>=4 && <div className="text-sm text-green-600 bg-green-50 p-3 rounded">Exactly 4 members — ready to submit. Other levels will unlock after undertaking acknowledged and submitted.</div>}
    </div>

    <div className="bg-white p-4 rounded-xl border mt-6">
      <h3 className="font-semibold">Undertaking</h3>
      <p className="text-xs text-gray-500">We, the students of B.E. Computer Engineering hereby assure project "{group.project?.title}" is our work. Each member must individually acknowledge (not on behalf).</p>
      <button onClick={acknowledge} className="mt-3 bg-green-600 text-white px-6 py-2 rounded">I Acknowledge — Digitally</button>
      <button onClick={submit} className="ml-3 bg-blue-600 text-white px-6 py-2 rounded">Submit for Verification — unlock other levels</button>
      <div className="text-xs text-gray-500 mt-2">Until submitted, DRAFT editable. After submit → SUBMITTED → Guide/HOD notified → AccessGrant → other levels lock open.</div>
    </div>
    {msg&&<div className="text-sm p-3 bg-amber-50 text-amber-700 rounded mt-4">{msg}</div>}
  </div>
}
