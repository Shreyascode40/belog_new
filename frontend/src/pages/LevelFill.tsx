import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function LevelFill(){
  const { stageId } = useParams()
  const nav = useNavigate()
  const [stage,setStage]=useState<any>(null)
  const [group,setGroup]=useState<any>(null)
  const [section,setSection]=useState<any>(null)
  const [form,setForm]=useState<any>({})
  const [status,setStatus]=useState('draft')
  const [msg,setMsg]=useState('')
  const [loading,setLoading]=useState(true)

  useEffect(()=>{
    const load=async()=>{
      try{
        const gRes = await client.get('/api/v1/groups/')
        const g = (gRes.data.results||gRes.data.data||[])[0]
        if(!g){ setMsg('No group — create one first'); setLoading(false); return }
        setGroup(g)
        const sRes = await client.get(`/api/v1/stages/${stageId}/`)
        setStage(sRes.data)
        const secRes = await client.get(`/api/v1/sections/?group=${g.id}&stage=${stageId}`)
        const list = secRes.data.results||secRes.data||[]
        if(list.length>0){
          setSection(list[0])
          setForm(list[0].content||{})
          setStatus(list[0].status)
        }
      }catch(e:any){
        setMsg(e.response?.data?.errors?.access?.[0] || e.response?.data?.errors?.level?.[0] || e.response?.data?.message || 'Failed — previous level not complete')
      }
      setLoading(false)
    }
    load()
  },[stageId])

  const saveDraft=async()=>{
    try{
      if(section){
        const r=await client.patch(`/api/v1/sections/${section.id}/`, {content: form})
        setSection(r.data); setStatus(r.data.status); setMsg('Draft saved — you can submit when ready')
      } else {
        const r=await client.post('/api/v1/sections/', {stage: Number(stageId), group: group.id, section_type: stage.slug, title: stage.name, owner_role:'student', content: form, status:'draft'})
        setSection(r.data); setStatus(r.data.status); setMsg('Draft created — fill next info and Submit')
      }
    }catch(e:any){ setMsg(e.response?.data?.errors?.access?.[0] || e.response?.data?.errors?.level?.[0] || JSON.stringify(e.response?.data)) }
  }

  const submitForReview=async()=>{
    try{
      if(!section){ await saveDraft(); return }
      let sub:any=null
      try{
        const sRes = await client.get(`/api/v1/submissions/?section=${section.id}&group=${group.id}`)
        sub = (sRes.data.results||sRes.data||[])[0]
      }catch{}
      if(!sub){
        const r=await client.post('/api/v1/submissions/', {section: section.id, group: group.id, content: form, status:'draft'})
        sub=r.data
      }
      await client.post(`/api/v1/submissions/${sub.id}/submit/`)
      setMsg('Submitted for review — guide notified. Next level will unlock after approval')
      setStatus('submitted')
    }catch(e:any){ setMsg(e.response?.data?.errors?.level?.[0] || e.response?.data?.errors?.access?.[0] || 'Submit failed') }
  }

  if(loading) return <div className="p-8">Loading next info...</div>
  if(!stage) return <div className="p-8 bg-white rounded-xl border">{msg||'Stage not found'} <button onClick={()=>nav('/')} className="text-blue-600 underline ml-2">Back</button></div>

  const isLocked = ['approved','locked','submitted','under_review'].includes(status)
  const renderForm=()=>{
    const order = stage.order
    if(order===0){
      return <div className="flex flex-col gap-4">
        <p className="text-xs text-gray-500">Level 0 — Information is filled via Group Creation (Cover + Members + Undertaking). This is the source for PDF pages 1-5.</p>
        <div className="bg-blue-50 p-4 rounded border">
          <div className="text-sm font-semibold">Group No. {group.group_number} — {group.project?.title||form.title||'Project Title'}</div>
          <div className="text-xs">Area: {group.project?.area_domain||form.area||'—'}</div>
          <div className="text-xs">Guide: Pending Guide Allocation (HOD assigns)</div>
        </div>
        <a href="/create-group" className="bg-blue-600 text-white px-6 py-2 rounded text-center">Go to Create Group — Fill Member Details (Name, Roll, Mobile, Seat, Email, TE Result, Contribution, Photo)</a>
        <div className="text-xs text-gray-500">Member info auto-fetched from registration when project title given — if blank, it fills from Student Profile (roll/mobile/seat/email) automatically.</div>
      </div>
    }
    if(order===1){
      return <div className="flex flex-col gap-4">
        <h3 className="font-semibold">Schedule & Topic Finalization</h3>
        <label className="text-sm font-semibold">Project Schedule — Sem I Dates</label>
        <input className="border p-2 rounded" placeholder="e.g., June-Nov dates" value={form.schedule_sem1||''} onChange={e=>setForm({...form, schedule_sem1: e.target.value})} disabled={isLocked}/>
        <label className="text-sm font-semibold">Project Schedule — Sem II Dates</label>
        <input className="border p-2 rounded" placeholder="e.g., Dec-May dates" value={form.schedule_sem2||''} onChange={e=>setForm({...form, schedule_sem2: e.target.value})} disabled={isLocked}/>
        <label className="text-sm font-semibold">Topic 1 — Proposed Topic</label>
        <textarea className="border p-2 rounded" rows={2} placeholder="Topic 1" value={form.topic1||''} onChange={e=>setForm({...form, topic1: e.target.value})} disabled={isLocked}/>
        <label className="text-sm font-semibold">Topic 2 — Alternative</label>
        <textarea className="border p-2 rounded" rows={2} placeholder="Topic 2" value={form.topic2||''} onChange={e=>setForm({...form, topic2: e.target.value})} disabled={isLocked}/>
        <div className="grid grid-cols-2 gap-3">
          <input className="border p-2 rounded text-sm" placeholder="Significance" value={form.significance||''} onChange={e=>setForm({...form, significance: e.target.value})} disabled={isLocked}/>
          <input className="border p-2 rounded text-sm" placeholder="Innovativeness" value={form.innovativeness||''} onChange={e=>setForm({...form, innovativeness: e.target.value})} disabled={isLocked}/>
          <input className="border p-2 rounded text-sm" placeholder="Scope" value={form.scope||''} onChange={e=>setForm({...form, scope: e.target.value})} disabled={isLocked}/>
          <input className="border p-2 rounded text-sm" placeholder="Feasibility" value={form.feasibility||''} onChange={e=>setForm({...form, feasibility: e.target.value})} disabled={isLocked}/>
        </div>
      </div>
    }
    if(order===2){
      return <div className="flex flex-col gap-4">
        <h3 className="font-semibold">Monthly Activity Charts (June–Nov)</h3>
        {["June","July","August","September","October","November"].map(mon=><div key={mon} className="border p-3 rounded">
          <div className="text-sm font-semibold">{mon}</div>
          <textarea className="border p-2 rounded w-full mt-1 text-sm" rows={2} placeholder={`Activities for ${mon} — e.g., Group Submission, Guide Meeting`} value={form[mon]||''} onChange={e=>setForm({...form, [mon]: e.target.value})} disabled={isLocked}/>
        </div>)}
      </div>
    }
    if(order===3){
      return <div className="flex flex-col gap-4">
        <h3 className="font-semibold">Requirement & Cost</h3>
        <label className="text-sm font-semibold">Requirement Traceability Matrix (Req ID | Requirement | Design Ref | Test Ref)</label>
        <textarea className="border p-2 rounded font-mono text-sm" rows={4} placeholder="R1 | Requirement | Design | Test" value={form.rtm||''} onChange={e=>setForm({...form, rtm: e.target.value})} disabled={isLocked}/>
        <label className="text-sm font-semibold">Cost Estimation</label>
        <div className="grid grid-cols-3 gap-2">
          <input className="border p-2 rounded" placeholder="Hardware Rs." value={form.cost_hw||''} onChange={e=>setForm({...form, cost_hw: e.target.value})} disabled={isLocked}/>
          <input className="border p-2 rounded" placeholder="Software Rs." value={form.cost_sw||''} onChange={e=>setForm({...form, cost_sw: e.target.value})} disabled={isLocked}/>
          <input className="border p-2 rounded" placeholder="Other Rs." value={form.cost_other||''} onChange={e=>setForm({...form, cost_other: e.target.value})} disabled={isLocked}/>
        </div>
      </div>
    }
    if(order===4){
      return <div className="flex flex-col gap-3">
        <h3 className="font-semibold">Review-1 — Problem Statement, Motivation, Objectives, Literature Review</h3>
        <textarea className="border p-2 rounded" rows={2} placeholder="Problem Statement" value={form.problem||''} onChange={e=>setForm({...form, problem: e.target.value})} disabled={isLocked}/>
        <textarea className="border p-2 rounded" rows={2} placeholder="Motivation" value={form.motivation||''} onChange={e=>setForm({...form, motivation: e.target.value})} disabled={isLocked}/>
        <textarea className="border p-2 rounded" rows={2} placeholder="Objectives" value={form.objectives||''} onChange={e=>setForm({...form, objectives: e.target.value})} disabled={isLocked}/>
        <textarea className="border p-2 rounded" rows={3} placeholder="Literature Review" value={form.literature||''} onChange={e=>setForm({...form, literature: e.target.value})} disabled={isLocked}/>
      </div>
    }
    // default for other levels (Design, Review-2, Development, Testing, Review-3, Competition, Terms, Final)
    return <div className="flex flex-col gap-3">
      <h3 className="font-semibold">{stage.name} — Fill next info</h3>
      <p className="text-xs text-gray-500">Official section: {stage.name} ({stage.slug}) — fill as per logbook layout.</p>
      {stage.slug.includes('design') && <><label className="text-sm">UML Diagrams (upload or describe)</label><textarea className="border p-2 rounded" rows={3} placeholder="Class, Sequence, DFD, State Chart" value={form.uml||''} onChange={e=>setForm({...form, uml: e.target.value})} disabled={isLocked}/></>}
      {stage.slug.includes('development') && <input className="border p-2 rounded" placeholder="Tech Stack, modules" value={form.stack||''} onChange={e=>setForm({...form, stack: e.target.value})} disabled={isLocked}/>}
      {stage.slug.includes('testing') && <input className="border p-2 rounded" placeholder="Test cases: alpha/beta, GUI, usability" value={form.testing||''} onChange={e=>setForm({...form, testing: e.target.value})} disabled={isLocked}/>}
      {stage.slug.includes('competition') && <><input className="border p-2 rounded" placeholder="Competition name, date, award" value={form.competition||''} onChange={e=>setForm({...form, competition: e.target.value})} disabled={isLocked}/><input className="border p-2 rounded" placeholder="Paper title, conference, ISSN" value={form.paper||''} onChange={e=>setForm({...form, paper: e.target.value})} disabled={isLocked}/></>}
      {!stage.slug.includes('design') && !stage.slug.includes('development') && !stage.slug.includes('testing') && !stage.slug.includes('competition') && <textarea className="border p-2 rounded" rows={6} placeholder="Enter details for this level..." value={form.details||form.info||''} onChange={e=>setForm({...form, details: e.target.value})} disabled={isLocked}/>}
    </div>
  }

  const locked = ['approved','locked','submitted','under_review'].includes(status)
  return <div className="max-w-3xl mx-auto">
    <button onClick={()=>nav('/')} className="text-sm text-blue-600 underline">← Back to Journey</button>
    <h1 className="text-2xl font-bold mt-2">Level {stage.order} — {stage.name}</h1>
    <p className="text-xs text-gray-500">{stage.slug} • {stage.is_required?'Required':'Optional'} • Status: <b>{status}</b> {locked&&'(Read-only)'}</p>
    {msg&&<div className={`mt-3 p-3 rounded text-sm ${msg.includes('Submitted')?'bg-green-50 text-green-700':'bg-amber-50 text-amber-700'}`}>{msg}</div>}
    <div className="bg-white p-6 rounded-xl border mt-6 flex flex-col gap-4">
      {renderForm()}
      {!locked ? <div className="flex gap-3">
        <button onClick={saveDraft} className="bg-slate-800 text-white px-6 py-2 rounded">Save Draft</button>
        <button onClick={submitForReview} className="bg-blue-600 text-white px-6 py-2 rounded">Submit for Review — unlock next</button>
      </div> : <div className="text-sm text-gray-500">Locked — view only. Complete previous level to unlock next.</div>}
      <div className="text-xs text-gray-400">Next level unlocks only after this is APPROVED/LOCKED — backend enforces.</div>
    </div>
  </div>
}
