import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../../api/client'
import StatusBadge from '../../components/StatusBadge'

export default function LogbookDetail(){
  const tick=useRealtimeTick()
  const {id}=useParams()
  const nav=useNavigate()
  const [data,setData]=useState<any>(null)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [editing,setEditing]=useState(false)
  const [form,setForm]=useState<any>({})
  const [saving,setSaving]=useState(false)
  const load=async()=>{
    setLoading(true)
    try{
      const r=await client.get(`/api/v1/student/logbook/${id}/`)
      setData(r.data.data)
      setForm(r.data.data.content||{})
    }catch(e:any){setError(e.response?.data?.message||'Failed to load')}
    setLoading(false)
  }
  useEffect(()=>{load()},[id])
  const save=async(submit=false)=>{
    setSaving(true)
    try{
      await client.patch(`/api/v1/student/logbook/${id}/`, form)
      if(submit) await client.post(`/api/v1/student/logbook/${id}/submit/`)
      await load()
      setEditing(false)
    }catch(e:any){setError(e.response?.data?.message||'Save failed')}
    setSaving(false)
  }
  const del=async()=>{
    if(!confirm('Delete draft?')) return
    await client.delete(`/api/v1/student/logbook/${id}/`)
    nav('/student/logbook')
  }
  const submit=async()=>{
    await client.post(`/api/v1/student/logbook/${id}/submit/`)
    load()
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  const canEdit=['draft','changes_required'].includes(data.status)
  return <div className="max-w-3xl mx-auto">
    <Link to="/student/logbook" className="text-sm text-blue-600 underline">← Back to Log Book</Link>
    <div className="bg-white border rounded-xl p-6 mt-4">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-lg font-bold">Week {data.content?.week||'-'} — {data.content?.project_stage||''}</h1>
          <div className="text-xs text-gray-500">{data.content?.date||''} • {data.submitted_at?`Submitted ${new Date(data.submitted_at).toLocaleDateString()}`:''} {data.reviewed_by?`• Verified by ${data.reviewed_by}`:''}</div>
        </div>
        <StatusBadge status={data.status}/>
      </div>

      {data.status==='changes_required' && <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-sm font-semibold text-red-800">Changes Requested</div>
        <div className="text-sm text-red-700 mt-1">Reviewer: {data.reviewed_by||'-'}</div>
        <div className="text-sm mt-1">"{data.review_remarks}"</div>
        <div className="text-xs text-gray-500 mt-1">Requested on {data.reviewed_at? new Date(data.reviewed_at).toLocaleDateString():''}</div>
        <button onClick={()=>setEditing(true)} className="mt-3 bg-red-600 text-white px-4 py-1 rounded text-xs">Edit Entry & Resubmit</button>
      </div>}

      {!editing ? <>
        <div className="mt-6 space-y-4 text-sm">
          <div><div className="text-xs text-gray-400">Work Completed</div><div className="whitespace-pre-wrap">{data.content?.work_completed||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Work Planned</div><div className="whitespace-pre-wrap">{data.content?.work_planned||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Problems</div><div>{data.content?.problems||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Solution</div><div>{data.content?.solution||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Learning</div><div>{data.content?.learning||'-'}</div></div>
          {data.content?.evidence_files && <div><div className="text-xs text-gray-400">Evidence</div><div className="text-xs">{data.content.evidence_files.join(', ')}</div></div>}
        </div>
        {data.versions?.length>0 && <div className="mt-6 border-t pt-4">
          <h3 className="text-xs font-semibold">Submission History</h3>
          {data.versions.map((v:any)=><div key={v.id} className="text-xs bg-gray-50 p-2 rounded mt-2">Version {v.version_number} — {new Date(v.submitted_at).toLocaleDateString()} — {v.review_remark||''}</div>)}
        </div>}
        <div className="mt-6 flex gap-2">
          {canEdit && <button onClick={()=>setEditing(true)} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">Edit</button>}
          {data.status==='draft' && <button onClick={submit} className="bg-green-600 text-white px-4 py-2 rounded text-sm">Submit</button>}
          {data.status==='draft' && <button onClick={del} className="border px-4 py-2 rounded text-sm text-red-600">Delete Draft</button>}
        </div>
      </> : <>
        <div className="mt-6 space-y-4">
          <label className="text-xs font-medium">Work Completed<textarea value={form.work_completed||''} onChange={e=>setForm({...form,work_completed:e.target.value})} rows={4} className="w-full border rounded p-2 text-sm mt-1"/></label>
          <label className="text-xs font-medium">Work Planned<textarea value={form.work_planned||''} onChange={e=>setForm({...form,work_planned:e.target.value})} rows={3} className="w-full border rounded p-2 text-sm mt-1"/></label>
          <label className="text-xs font-medium">Problems<textarea value={form.problems||''} onChange={e=>setForm({...form,problems:e.target.value})} rows={2} className="w-full border rounded p-2 text-sm mt-1"/></label>
          <label className="text-xs font-medium">Solution<textarea value={form.solution||''} onChange={e=>setForm({...form,solution:e.target.value})} rows={2} className="w-full border rounded p-2 text-sm mt-1"/></label>
          <label className="text-xs font-medium">Learning<textarea value={form.learning||''} onChange={e=>setForm({...form,learning:e.target.value})} rows={2} className="w-full border rounded p-2 text-sm mt-1"/></label>
        </div>
        <div className="flex gap-2 mt-4">
          <button onClick={()=>save(false)} disabled={saving} className="bg-slate-700 text-white px-4 py-2 rounded text-sm">Save</button>
          <button onClick={()=>save(true)} disabled={saving} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">Save & Resubmit</button>
          <button onClick={()=>setEditing(false)} className="border px-4 py-2 rounded text-sm">Cancel</button>
        </div>
      </>}
      {data.status!=='draft' && !canEdit && <div className="mt-4 text-xs text-gray-500 bg-gray-50 p-3 rounded">Submitted entries cannot be freely modified.</div>}
    </div>
  </div>
}