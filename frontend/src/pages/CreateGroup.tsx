import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function CreateGroup(){
  const nav = useNavigate()
  const [step,setStep]=useState(1)
  const [title,setTitle]=useState('')
  const [area,setArea]=useState('')
  const [group,setGroup]=useState<any>(null)
  const [members,setMembers]=useState<any[]>([])
  const [newMember,setNewMember]=useState({name:'', roll_number:'', mobile:'', exam_seat_number:'', email:'', te_result:'', contribution:''})
  const [batch,setBatch]=useState('B.E. Computer Engineering')
  const [batchYears,setBatchYears]=useState('2023-2027')
  const [msg,setMsg]=useState('')

  const createGroup=async()=>{
    try{
      const r=await client.post('/api/v1/groups/', {project_title: title, area})
      setGroup(r.data)
      const g=await client.get(`/api/v1/groups/${r.data.id}/`)
      setGroup(g.data)
      const mem=await client.get(`/api/v1/groups/${r.data.id}/`)
      setMembers(mem.data.members||[])
      setStep(2)
      setMsg(`Group No. ${r.data.group_number} created (AY ${r.data.academic_year}) — Guide: Pending Allocation`)
    }catch(e:any){ setMsg(e.response?.data?.group?.[0]|| e.response?.data?.message|| 'Create failed') }
  }

  const addMemberDirect=async()=>{
    if(!newMember.email || !newMember.name || !newMember.roll_number){
      setMsg('Name, Roll No., Email required'); return
    }
    try{
      await client.post(`/api/v1/groups/${group.id}/add-member-direct/`, newMember)
      setMsg(`Member ${newMember.name} added directly — no invite needed`)
      setNewMember({name:'', roll_number:'', mobile:'', exam_seat_number:'', email:'', te_result:'', contribution:''})
      const g=await client.get(`/api/v1/groups/${group.id}/`)
      setMembers(g.data.members||[])
    }catch(e:any){ setMsg(e.response?.data?.message||JSON.stringify(e.response?.data)||'Add failed — need exactly 4') }
  }

  const updateMember=async(m:any, field:string, value:string)=>{
    try{
      await client.patch(`/api/v1/group-members/${m.id}/`, {[field]: value})
      setMembers(members.map(x=>x.id===m.id? {...x,[field]:value, student_detail: {...x.student_detail, [field]: value}}:x))
    }catch(e:any){ setMsg('Update failed') }
  }
  const updateProfile=async(m:any, field:string, value:string)=>{
    try{
      if(!m.student_detail?.id){ setMsg('No profile yet — will be created on save'); return }
      await client.patch(`/api/v1/students/${m.student_detail.id}/`, {[field]: value})
      setMembers(members.map(x=>x.id===m.id? {...x, student_detail: {...x.student_detail, [field]: value}}:x))
      setMsg(`Updated ${field} — auto-fetched next time`)
    }catch(e:any){ 
      // fallback: try create profile
      try{
        await client.post('/api/v1/students/', {user: m.student, [field]: value, name: m.student_detail?.name||'Student', roll_number: field==='roll_number'?value: m.student_detail?.roll_number||'', email: m.student_detail?.email})
        setMsg('Profile created and updated')
      }catch{ setMsg('Profile update failed') }
    }
  }

  const acknowledge=async()=>{
    await client.post(`/api/v1/groups/${group.id}/acknowledge/`, {contribution: 'Sample contribution', te_result: 'Distinction'})
    setMsg('You acknowledged undertaking — Digitally Acknowledged')
    const mem=await client.get(`/api/v1/group-members/?group=${group.id}`)
    setMembers(mem.data.results||mem.data||[])
  }

  const submit=async()=>{
    try{
      const r=await client.post(`/api/v1/groups/${group.id}/submit-information/`)
      setMsg(r.data.data?.message||'Submitted — guide/HOD notified')
      setTimeout(()=>nav('/'),1500)
    }catch(e:any){ setMsg(e.response?.data?.message|| JSON.stringify(e.response?.data?.errors)||'Submit failed — check all fields, size, acknowledgements') }
  }

  return <div className="max-w-4xl mx-auto">
    <h1 className="text-2xl font-bold">Create Project Group</h1>
    <div className="flex gap-2 mt-4 text-sm">
      <span className={step>=1?'bg-blue-600 text-white px-3 py-1 rounded':'bg-gray-200 px-3 py-1 rounded'}>Step A — Cover</span>
      <span className={step>=2?'bg-blue-600 text-white px-3 py-1 rounded':'bg-gray-200 px-3 py-1 rounded'}>Step B — Members</span>
      <span className={step>=3?'bg-blue-600 text-white px-3 py-1 rounded':'bg-gray-200 px-3 py-1 rounded'}>Step C — Undertaking</span>
    </div>

    {step===1 && <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-4">
      <p className="text-xs text-gray-500">Group No. auto-assigned per Academic Year/Department — read-only after creation. Guide shows Pending until HOD assigns.</p>
      {group && <div className="bg-green-50 p-3 rounded text-sm">Group No. <b>{group.group_number}</b> (AY {group.academic_year}) — Project Guide: <b>Pending Guide Allocation</b></div>}
      <label className="text-sm font-semibold">Project Title <span className="text-red-500">*</span> <span className="text-gray-400 font-normal">(two-line, as in official cover)</span></label>
      <textarea className="border p-2 rounded" rows={2} value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g., AI Based Logbook System"/>
      <label className="text-sm font-semibold">Area of Project <span className="text-red-500">*</span></label>
      <input className="border p-2 rounded" value={area} onChange={e=>setArea(e.target.value)} placeholder="e.g., AI/ML, IoT, Web"/>
      <div className="text-xs text-gray-500">Guide field: <b>Pending Guide Allocation</b> — not editable by student, HOD assigns.</div>
      {!group ? <button onClick={createGroup} className="bg-blue-600 text-white p-2 rounded">Create Group</button>
      : <button onClick={()=>setStep(2)} className="bg-green-600 text-white p-2 rounded">Next — Add Members</button>}
      {msg&&<div className="text-sm text-blue-600">{msg}</div>}
    </div>}

    {step===2 && <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-4">
      <h2 className="font-semibold">Step B — Group Members — Fill directly (no invite)</h2>
      <p className="text-xs text-gray-500">Creator is <b>Member 1 (Leader)</b> automatically. <b>Just fill fields like registration — no invite needed.</b> All fields match official logbook. Group size exactly <b>4</b> members.</p>
      <div className="bg-amber-50 p-3 rounded text-xs text-amber-800">Required per member: <b>Name*, Roll No.*, Mobile No.*, Exam Seat No.*, Email ID*, TE Result*, Contribution, Photo*</b> — Must have exactly 4 members. If project title given but info blank, it auto-fetches from previous StudentProfile.</div>

      <div className="flex flex-col gap-4">
        {members.map((m:any,idx:number)=>(
          <div key={m.id} className="border rounded-xl p-4 bg-gray-50">
            <div className="font-semibold text-sm mb-3">Member {idx+1} {m.role==='leader'?'— Leader (You)':''} {m.acknowledged?'✓ Acknowledged':''} {m.student_detail?.name ? `— ${m.student_detail.name}` : ''}</div>
            <div className="text-xs text-green-600 mb-2">All fields like registration — editable directly.</div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col"><label className="text-xs font-semibold">Name *</label><input className="border p-2 rounded text-sm bg-blue-50" defaultValue={m.student_detail?.name||''} placeholder="Full name" onBlur={e=>updateProfile(m,'name',e.target.value)} /></div>
              <div className="flex flex-col"><label className="text-xs font-semibold">Roll No. *</label><input className="border p-2 rounded text-sm bg-blue-50" defaultValue={m.student_detail?.roll_number||''} placeholder="41001" onBlur={e=>updateProfile(m,'roll_number',e.target.value)} /></div>
              <div className="flex flex-col"><label className="text-xs font-semibold">TE Result *</label><input className="border p-2 rounded text-sm" defaultValue={m.te_result||''} placeholder="Distinction" onBlur={e=>updateMember(m,'te_result',e.target.value)} /></div>
              <div className="flex flex-col"><label className="text-xs font-semibold">Mobile No. *</label><input className="border p-2 rounded text-sm bg-blue-50" defaultValue={m.student_detail?.mobile||''} placeholder="10-digit" onBlur={e=>updateProfile(m,'mobile',e.target.value)} /></div>
              <div className="flex flex-col"><label className="text-xs font-semibold">Exam Seat No. *</label><input className="border p-2 rounded text-sm bg-blue-50" defaultValue={m.student_detail?.exam_seat_number||''} placeholder="SEAT..." onBlur={e=>updateProfile(m,'exam_seat_number',e.target.value)} /></div>
              <div className="flex flex-col"><label className="text-xs font-semibold">Email ID *</label><input className="border p-2 rounded text-sm bg-gray-100" value={m.student_detail?.email||''} readOnly /></div>
              <div className="flex flex-col col-span-2"><label className="text-xs font-semibold">Contribution</label><input className="border p-2 rounded text-sm" defaultValue={m.contribution||''} placeholder="Backend, Testing..." onBlur={e=>updateMember(m,'contribution',e.target.value)} /></div>
              <div className="flex flex-col col-span-2"><label className="text-xs font-semibold">Photo * (Affix your photo here)</label><input type="file" accept="image/*" className="border p-2 rounded text-sm bg-white" onChange={e=>{ if(e.target.files?.[0]) setMsg(`Photo ${e.target.files[0].name} selected`)}} /></div>
            </div>
            <div className="text-xs mt-2">Status: <b>{m.status}</b> — {m.acknowledged?`Ack ${new Date(m.acknowledged_at).toLocaleDateString()}`:'Not yet acknowledged'}</div>
          </div>
        ))}
      </div>

      {members.length<4 && <div className="border-2 border-dashed rounded-xl p-4 bg-amber-50">
        <div className="font-semibold text-sm">Add Member {members.length+1} — Fill directly (no invite)</div>
        <p className="text-xs text-gray-500">Fill like registration — all fields required. This directly adds member, no accept needed.</p>
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
      {members.length>=4 && <div className="text-sm text-green-600 bg-green-50 p-3 rounded">Exactly 4 members — ready for Undertaking.</div>}

      <div className="flex gap-2">
        <button onClick={()=>setStep(1)} className="border p-2 rounded">Back</button>
        <button onClick={()=>setStep(3)} className="bg-blue-600 text-white p-2 rounded flex-1">Next — Undertaking</button>
      </div>
      {msg&&<div className="text-sm text-blue-600">{msg}</div>}
    </div>}

    {step===3 && <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-3">
      <h2 className="font-semibold">Step C — Undertaking</h2>
      <p className="text-xs text-gray-500">We, the students of B.E. {batch} batch {batchYears} hereby assure that project <b>{title|| group?.project?.title || '—'}</b> is our original work.</p>
      <label className="text-sm">Batch</label><input className="border p-2 rounded" value={batch} onChange={e=>setBatch(e.target.value)}/>
      <label className="text-sm">Batch Years</label><input className="border p-2 rounded" value={batchYears} onChange={e=>setBatchYears(e.target.value)}/>
      <div className="text-xs bg-gray-50 p-3 rounded">Academic Year auto: {group?.academic_year} — Project Title (read-only): {title}</div>
      <div className="border p-3 rounded text-sm">
        <div className="font-semibold">Members must individually acknowledge — do not sign on behalf of teammates</div>
        {members.map((m:any)=><div key={m.id} className="flex justify-between py-1"><span>{m.student} — {m.acknowledged ? `Digitally Acknowledged on ${new Date(m.acknowledged_at).toLocaleDateString()}` : 'Not yet'}</span>{!m.acknowledged && <span className="text-amber-600 text-xs">Awaiting their login to acknowledge</span>}</div>)}
      </div>
      <button onClick={acknowledge} className="bg-green-600 text-white p-2 rounded">I Acknowledge (Digitally) — for me</button>
      <button onClick={submit} className="bg-blue-600 text-white p-2 rounded">Submit for Verification (Information Stage)</button>
      <p className="text-xs text-gray-500">Until submitted, DRAFT and editable. After submit → SUBMITTED → Guide notified (or HOD if no guide yet) → AccessGrant flow (same gate). Pending guide shows no silent fail — HOD notified.</p>
      <button onClick={()=>setStep(2)} className="border p-2 rounded">Back</button>
      {msg&&<div className="text-sm text-blue-600">{msg}</div>}
    </div>}
  </div>
}
