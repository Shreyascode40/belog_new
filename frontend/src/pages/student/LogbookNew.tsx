import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../../api/client'

export default function LogbookNew(){
  const nav=useNavigate()
  const [stages,setStages]=useState<any[]>([])
  const [form,setForm]=useState({week:'',date:new Date().toISOString().slice(0,10),project_stage:'',work_completed:'',work_planned:'',problems:'',solution:'',learning:''})
  const [files,setFiles]=useState<FileList|null>(null)
  const [saving,setSaving]=useState(false)
  const [error,setError]=useState('')
  const [stageId,setStageId]=useState('')
  useEffect(()=>{
    client.get('/api/v1/student/progress/').then(r=>{
      const st=r.data.data.stages||[]
      setStages(st)
      const cur=st.find((s:any)=>!['approved','locked'].includes(s.status))
      if(cur){ setStageId(cur.id); setForm(f=>({...f,project_stage:cur.name}))}
    }).catch(()=>{})
  },[])
  const submit=async(submitNow:boolean)=>{
    setSaving(true);setError('')
    try{
      const fd=new FormData()
      fd.append('week',form.week)
      fd.append('date',form.date)
      fd.append('project_stage',form.project_stage)
      fd.append('work_completed',form.work_completed)
      fd.append('work_planned',form.work_planned)
      fd.append('problems',form.problems)
      fd.append('solution',form.solution)
      fd.append('learning',form.learning)
      if(stageId) fd.append('stage',stageId)
      if(files) Array.from(files).forEach(f=>fd.append('evidence',f))
      const r=await client.post('/api/v1/student/logbook/', fd, {headers:{'Content-Type':'multipart/form-data'}})
      if(submitNow){
        await client.post(`/api/v1/student/logbook/${r.data.data.id}/submit/`)
      }
      nav('/student/logbook')
    }catch(e:any){setError(e.response?.data?.message|| JSON.stringify(e.response?.data?.errors)||'Save failed')}
    setSaving(false)
  }
  return <div className="max-w-3xl mx-auto">
    <h1 className="text-xl font-bold">Create Log Entry</h1>
    <div className="bg-white border rounded-xl p-6 mt-4 space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <label className="text-xs font-medium">Week Number<input value={form.week} onChange={e=>setForm({...form,week:e.target.value})} className="mt-1 w-full border rounded p-2 text-sm" placeholder="5"/></label>
        <label className="text-xs font-medium">Date<input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})} className="mt-1 w-full border rounded p-2 text-sm"/></label>
        <label className="text-xs font-medium">Project Stage<select value={stageId} onChange={e=>{setStageId(e.target.value); const s=stages.find(x=>String(x.id)===e.target.value); if(s) setForm({...form,project_stage:s.name})}} className="mt-1 w-full border rounded p-2 text-sm"><option value="">Select stage</option>{stages.map(s=><option key={s.id} value={s.id}>{s.order} — {s.name} ({s.status})</option>)}</select></label>
      </div>
      <label className="text-xs font-medium">What work was completed this week?<textarea value={form.work_completed} onChange={e=>setForm({...form,work_completed:e.target.value})} rows={4} className="mt-1 w-full border rounded p-2 text-sm" placeholder="Describe work..."/></label>
      <label className="text-xs font-medium">What work is planned for next period?<textarea value={form.work_planned} onChange={e=>setForm({...form,work_planned:e.target.value})} rows={3} className="mt-1 w-full border rounded p-2 text-sm"/></label>
      <label className="text-xs font-medium">Problems / challenges<textarea value={form.problems} onChange={e=>setForm({...form,problems:e.target.value})} rows={2} className="mt-1 w-full border rounded p-2 text-sm"/></label>
      <label className="text-xs font-medium">Solution / action taken<textarea value={form.solution} onChange={e=>setForm({...form,solution:e.target.value})} rows={2} className="mt-1 w-full border rounded p-2 text-sm"/></label>
      <label className="text-xs font-medium">Learning / outcome<textarea value={form.learning} onChange={e=>setForm({...form,learning:e.target.value})} rows={2} className="mt-1 w-full border rounded p-2 text-sm"/></label>
      <label className="text-xs font-medium">Evidence (images, PDFs)<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" onChange={e=>setFiles(e.target.files)} className="mt-1 w-full border rounded p-2 text-sm"/></label>
      {error && <div className="text-sm text-red-600 bg-red-50 border p-3 rounded">{error}</div>}
      <div className="flex gap-2">
        <button onClick={()=>submit(false)} disabled={saving} className="bg-slate-700 text-white px-5 py-2 rounded text-sm disabled:opacity-50">{saving?'Saving...':'Save Draft'}</button>
        <button onClick={()=>submit(true)} disabled={saving} className="bg-blue-600 text-white px-5 py-2 rounded text-sm">{saving?'Submitting...':'Save & Submit'}</button>
        <button onClick={()=>nav('/student/logbook')} className="border px-5 py-2 rounded text-sm">Cancel</button>
      </div>
    </div>
  </div>
}
