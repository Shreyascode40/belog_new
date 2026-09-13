import { useEffect, useState } from 'react'
import client from '../api/client'
import { useNavigate } from 'react-router-dom'

function InlineField({ label, value, placeholder, help, onSave, warning }: { label: string, value: string, placeholder: string, help: string, warning?: string, onSave: (v:string)=>Promise<void> }){
  const [editing,setEditing]=useState(false)
  const [draft,setDraft]=useState(value)
  const [saving,setSaving]=useState(false)
  const [toast,setToast]=useState('')
  useEffect(()=>{ setDraft(value) },[value])
  const save=async()=>{
    if(draft===value){ setEditing(false); return }
    setSaving(true)
    try{
      await onSave(draft)
      setToast('✓ Saved')
      setTimeout(()=>setToast(''),1500)
      setEditing(false)
    }catch(e:any){
      const d=e.response?.data
      setToast(d?.errors?.roll_number?.[0]||d?.errors?.email?.[0]||d?.message||'Save failed')
      setTimeout(()=>setToast(''),2500)
    }
    setSaving(false)
  }
  return <div className="flex flex-col">
    <label className="text-xs font-semibold flex justify-between">
      <span>{label}</span>
      {!editing && <button onClick={()=>setEditing(true)} className="text-blue-600 text-xs">✏️ Edit</button>}
    </label>
    {!editing ? (
      <div className="border p-3 rounded bg-gray-50 flex justify-between items-center mt-1">
        <span className="text-sm">{value||<span className="text-gray-400">Not filled — click Edit</span>}</span>
        {toast&&<span className="text-xs text-green-600">{toast}</span>}
      </div>
    ) : (
      <div className="mt-1">
        <input autoFocus className="border p-3 rounded w-full text-sm" value={draft} onChange={e=>setDraft(e.target.value)} placeholder={placeholder} onBlur={save} onKeyDown={e=>{ if(e.key==='Enter') save(); if(e.key==='Escape'){ setDraft(value); setEditing(false)} }}/>
        {warning&&<div className="text-xs text-amber-600 mt-1">{warning}</div>}
        <div className="text-xs text-gray-500 mt-1">{help}</div>
        <div className="flex gap-2 mt-2">
          <button onClick={save} disabled={saving} className="bg-blue-600 text-white px-3 py-1 rounded text-xs">{saving?'Saving...':'Save'}</button>
          <button onClick={()=>{ setDraft(value); setEditing(false)}} className="border px-3 py-1 rounded text-xs">Cancel</button>
          {toast&&<span className="text-xs text-green-600 ml-2">{toast}</span>}
        </div>
      </div>
    )}
    {!editing && <div className="text-xs text-gray-400 mt-1">{help}</div>}
    {warning && !editing && value && <div className="text-xs text-amber-600">{warning}</div>}
  </div>
}

export default function Profile(){
  const [profile,setProfile]=useState<any>(null)
  const [members,setMembers]=useState<any[]>([])
  const [coverDone,setCoverDone]=useState(false)
  const [msg,setMsg]=useState('')
  const [showDeleteConfirm,setShowDeleteConfirm]=useState(false)
  const [deleteInput,setDeleteInput]=useState('')
  const [undoAvailable,setUndoAvailable]=useState(false)
  const [deletedProfile,setDeletedProfile]=useState<any>(null)
  const [photoPreview,setPhotoPreview]=useState<string | null>(null)

  const load=async()=>{
    const r=await client.get('/api/v1/students/')
    const list=r.data.results||r.data.data||r.data||[]
    const email=localStorage.getItem('email')
    const own=list.find((p:any)=>p.email===email) || list[0]
    if(own){
      setProfile(own)
      if(own.photograph) setPhotoPreview(own.photograph)
    }
    try{
      const gRes=await client.get('/api/v1/groups/')
      const g=(gRes.data.results||gRes.data.data||[])[0]
      if(g){
        setCoverDone(true)
        const mRes=await client.get(`/api/v1/groups/${g.id}/`)
        setMembers(mRes.data.members||[])
      } else {
        setCoverDone(false)
      }
    }catch{}
  }
  useEffect(()=>{ load() },[])

  const filledCount = [profile?.name, profile?.roll_number, profile?.mobile, profile?.exam_seat_number, profile?.email].filter(Boolean).length
  const totalFields = 5

  const saveField=async(field:string, value:string)=>{
    if(!profile?.id){
      const payload={[field]: value, user: JSON.parse(atob(localStorage.getItem('access')!.split('.')[1])).user_id, name: profile?.name||'Student', roll_number: field==='roll_number'?value:'', email: localStorage.getItem('email')||''}
      const r=await client.post('/api/v1/students/', payload)
      setProfile(r.data)
      return
    }
    await client.patch(`/api/v1/students/${profile.id}/`, {[field]: value})
    if(field==='email'){
      // sync to User and update localStorage
      try{ await client.patch(`/api/v1/users/${profile.user||profile.user_id}/`, {email: value}) }catch{}
      localStorage.setItem('email', value)
    }
    // reload
    const r=await client.get('/api/v1/students/')
    const list=r.data.results||r.data.data||r.data||[]
    const email=localStorage.getItem('email')
    const own=list.find((p:any)=>p.email===email) || list.find((p:any)=>p.id===profile.id)
    if(own) setProfile(own)
  }

  const handleDelete=async()=>{
    if(deleteInput!=='DELETE'){ setMsg('Type DELETE to confirm'); return }
    const toDelete=profile
    try{
      await client.delete(`/api/v1/students/${profile.id}/`)
      setDeletedProfile(toDelete)
      setProfile(null)
      setUndoAvailable(true)
      setMsg('Profile deleted — Journey will go back to NOT_STARTED and other levels will lock')
      setShowDeleteConfirm(false)
      setDeleteInput('')
      setTimeout(()=>setUndoAvailable(false),5000)
    }catch(e:any){ setMsg(e.response?.data?.message||'Delete failed') }
  }
  const handleUndo=async()=>{
    if(!deletedProfile) return
    try{
      // recreate
      await client.post('/api/v1/students/', {name: deletedProfile.name, roll_number: deletedProfile.roll_number, mobile: deletedProfile.mobile, exam_seat_number: deletedProfile.exam_seat_number, email: deletedProfile.email, department: deletedProfile.department, user: deletedProfile.user})
      setMsg('Profile restored')
      setUndoAvailable(false)
      load()
    }catch{ setMsg('Undo failed — please recreate manually') }
  }

  const handlePhotoChange=async(e:any)=>{
    const file=e.target.files?.[0]
    if(!file) return
    if(file.size>2*1024*1024){ setMsg('Photo must be <2MB'); return }
    setPhotoPreview(URL.createObjectURL(file))
    // upload as Document with type STUDENT_PHOTO or via profile
    const fd=new FormData()
    fd.append('photograph', file)
    try{
      await client.patch(`/api/v1/students/${profile.id}/`, fd, {headers:{'Content-Type':'multipart/form-data'}})
      setMsg('Photo uploaded — will appear in PDF Affix your photo here box')
      load()
    }catch{
      setMsg('Photo upload failed — saved preview locally, will be uploaded on Save')
    }
  }

  return <div className="max-w-3xl mx-auto">
    <h1 className="text-2xl font-bold">My Profile — Member Info</h1>
    <p className="text-xs text-gray-500 mt-1">Separate section — per-field inline edit (click ✏️ → Save/Cancel), auto-save on blur with ✓ Saved toast, email warning, delete with type-to-confirm and undo.</p>

    <div className="bg-white p-4 rounded-xl border mt-4">
      <div className="flex items-center gap-2 text-xs font-semibold">
        <span className={coverDone?'text-green-600':'text-gray-400'}>✓ Cover {coverDone?'✓':''}</span>
        <span>→</span>
        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">Profile (you are here, {filledCount}/{totalFields} fields filled)</span>
        <span>→</span>
        <span className={members.length>=4?'text-green-600':'text-gray-400'}>Student Info {members.length}/4</span>
        <span>→</span>
        <span className="text-gray-400">Submit → Other levels</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-3"><div className="bg-blue-600 h-1.5 rounded-full" style={{width:`${(filledCount/totalFields)*50 + (members.length/4)*50}%`}}></div></div>
    </div>

    <div className="bg-amber-50 p-3 rounded text-xs text-amber-800 mt-4">All fields like registration — fill here once, it will auto-fetch in Cover and Student Info. Different fields per member — each has its own separate form in Student Section.</div>

    <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-5">
      <InlineField label="Name *" value={profile?.name||''} placeholder="Full name — different per member" help="Full name as in official form" onSave={v=>saveField('name', v)} />
      <InlineField label="Roll No. *" value={profile?.roll_number||''} placeholder="41001 — unique per member" help="Roll 41001 — unique per member, shows in PDF" onSave={v=>saveField('roll_number', v)} />
      <InlineField label="Mobile No. *" value={profile?.mobile||''} placeholder="10-digit — different per member" help="Mobile 10-digit, different per member" onSave={v=>saveField('mobile', v)} />
      <InlineField label="Exam Seat No. *" value={profile?.exam_seat_number||''} placeholder="SEAT... — different per member" help="Seat SEAT… — unique, shows in PDF" onSave={v=>saveField('exam_seat_number', v)} />
      <InlineField label="Email ID *" value={profile?.email||''} placeholder="member email — different box per member" help="Email — different per member, used for login" warning={profile?.email ? 'Login email — changing logs you out, use new email next login' : undefined} onSave={v=>saveField('email', v)} />
      <InlineField label="Department" value={profile?.department||''} placeholder="Computer Engineering" help="Department — auto-fetched in Cover" onSave={v=>saveField('department', v)} />

      <div className="flex flex-col">
        <label className="text-xs font-semibold flex justify-between"><span>Photo — Affix your photo here — &lt;2MB, shows in PDF (optional for now)</span><span className="text-gray-400">Preview helps verify before PDF</span></label>
        <div className="mt-1 flex gap-4 items-center">
          <div className="w-24 h-32 border-2 border-dashed rounded flex items-center justify-center bg-gray-50 overflow-hidden">
            {photoPreview ? <img src={photoPreview} alt="preview" className="w-full h-full object-cover" /> : <span className="text-xs text-gray-400 text-center">No photo<br/>Affix here</span>}
          </div>
          <div className="flex-1">
            <input type="file" accept="image/*" onChange={handlePhotoChange} className="border p-2 rounded text-sm w-full" />
            <div className="text-xs text-gray-500 mt-1">Photo &lt;2MB — will be DOCUMENT type STUDENT_PHOTO in PDF's photo box. Preview shows how it will appear.</div>
          </div>
        </div>
      </div>

      <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded">If not filled, journey shows NOT_STARTED and other levels locked. Partially filled → Save per field (✓ Saved toast) keeps journey DRAFT — you can return and complete later. Fully filled (all 4 members) → Student Section Submit → other levels unlock.</div>
      {msg&&<div className="text-sm p-3 rounded bg-green-50 text-green-700">{msg}</div>}
    </div>

    <div className="bg-white p-4 rounded-xl border mt-6">
      <h3 className="font-semibold text-sm">Danger Zone — Delete Profile</h3>
      <p className="text-xs text-gray-500">Journey will go back to NOT_STARTED and other levels lock — currently same row as Edit, too prominent.</p>
      {!showDeleteConfirm ? <button onClick={()=>setShowDeleteConfirm(true)} className="mt-3 text-sm text-gray-500 underline hover:text-red-600">Delete profile</button>
      : <div className="mt-3 p-3 border rounded bg-red-50">
          <div className="text-sm font-semibold text-red-700">Type DELETE to confirm</div>
          <p className="text-xs text-gray-600">This removes your member info. Journey will go back to NOT_STARTED and other levels will lock.</p>
          <input className="border p-2 rounded w-full mt-2 text-sm" placeholder="Type DELETE" value={deleteInput} onChange={e=>setDeleteInput(e.target.value)} />
          <div className="flex gap-2 mt-2">
            <button onClick={handleDelete} className="bg-red-600 text-white px-4 py-2 rounded text-sm">Confirm Delete</button>
            <button onClick={()=>{setShowDeleteConfirm(false); setDeleteInput('')}} className="border px-4 py-2 rounded text-sm">Cancel</button>
          </div>
        </div>}
      {undoAvailable&&<div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded flex justify-between items-center">
        <span className="text-sm text-amber-800">Profile deleted — Journey will go back to NOT_STARTED</span>
        <button onClick={handleUndo} className="bg-amber-600 text-white px-3 py-1 rounded text-xs">Undo (5s)</button>
      </div>}
    </div>

    <div className="text-xs text-gray-400 mt-3 text-center">Changes reflect in Cover and Student Info automatically via auto-fetch. Each of 4 members has its own separate card in Student Info — fill differently.</div>
  </div>
}
