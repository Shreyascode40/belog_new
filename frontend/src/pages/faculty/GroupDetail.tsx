import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import client from '../../api/client'

export default function GroupDetail({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const {id}=useParams()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  const [tab,setTab]=useState<'students'|'progress'|'logbook'|'documents'>('students')
  useEffect(()=>{
    (async()=>{
      setLoading(true);setError('')
      try{
        const r=await client.get(`/api/v1/${role}/groups/${id}/`)
        setData(r.data.data)
      }catch(e:any){setError(e.response?.data?.message||'Unable to load group')}
      setLoading(false)
    })()
  },[id, role])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading group...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-6xl mx-auto">
    <Link to={`/${role}/groups`} className="text-sm text-blue-600 underline">← Back to Groups</Link>
    <div className="bg-white border rounded-xl p-6 mt-4">
      <h1 className="text-lg font-bold">G-{data.group_number} — {data.project_detail?.title||'Untitled'}</h1>
      <div className="text-xs text-gray-500">{data.academic_year_detail?.year_label} • {data.department_detail?.name} • Progress {data.overall_progress ?? data.progress}%</div>
      <div className="w-full bg-gray-200 h-2 rounded-full mt-3"><div className="bg-blue-600 h-2 rounded-full" style={{width:`${data.overall_progress ?? data.progress}%`}}></div></div>
    </div>

    <div className="bg-white border rounded-xl p-4 mt-4">
      <div className="flex gap-2 text-sm border-b pb-2">
        {(['students','progress','logbook','documents'] as const).map(t=><button key={t} onClick={()=>setTab(t)} className={`px-3 py-1.5 rounded capitalize ${tab===t?'bg-blue-600 text-white':'border'}`}>{t}</button>)}
      </div>

      {tab==='students' && <div className="mt-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-xs font-semibold uppercase">Project</h3>
            <div className="text-sm mt-2 space-y-1">
              <div><span className="text-gray-400">Title:</span> {data.project_detail?.title||'-'}</div>
              <div><span className="text-gray-400">Domain:</span> {data.project_detail?.area_domain||'-'}</div>
              <div><span className="text-gray-400">Description:</span> {data.project_detail?.description||'-'}</div>
            </div>
            <h3 className="text-xs font-semibold uppercase mt-4">Guide / Reviewer</h3>
            <div className="text-sm mt-2">
              <div>Guide: {data.guide_detail?.name||'—'} ({data.guide_detail?.email||''})</div>
              <div className="text-xs text-gray-500">Reviewer via assignment</div>
            </div>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase">Students</h3>
            <table className="w-full text-sm mt-2">
              <thead><tr className="text-xs text-gray-400 border-b"><th className="text-left py-1">Name</th><th className="text-left py-1">PRN</th><th className="text-left py-1">Email</th><th className="text-left py-1">Role</th></tr></thead>
              <tbody>{data.members?.map((m:any)=><tr key={m.id} className="border-b last:border-0"><td className="py-1">{m.student_detail?.name}</td><td>{m.student_detail?.roll_number}</td><td className="text-xs">{m.student_detail?.email}</td><td>{m.role}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </div>}

      {tab==='progress' && <div className="mt-4 space-y-2">
        {data.progress_detail?.map((p:any)=><div key={p.id} className="flex justify-between items-center border rounded p-3">
          <span className="text-sm">{p.order}. {p.name} <span className="text-xs text-gray-400">({p.status})</span></span>
          <span className={`text-xs px-2 py-1 rounded-full ${p.pct===100?'bg-green-100 text-green-700': p.pct===0?'bg-gray-100':'bg-yellow-100'}`}>{p.pct}%</span>
        </div>)}
        <div className="text-xs text-gray-500">Completed: {data.completed_milestones} • Pending: {data.pending_milestones} • Overdue: {data.overdue_milestones}</div>
      </div>}

      {tab==='logbook' && <div className="mt-4">
        {data.pending_reviews?.length ? data.pending_reviews.map((s:any)=><div key={s.id} className="border rounded p-3 flex justify-between items-center mt-2">
          <div><div className="text-sm font-medium">Week {s.content?.week||'-'} — {s.section?.title||s.content?.project_stage||''}</div><div className="text-xs text-gray-500">{s.status} • {s.submitted_at? new Date(s.submitted_at).toLocaleDateString():''}</div></div>
          <Link to={`/${role}/logbook/${s.id}`} className="bg-blue-600 text-white px-3 py-1 rounded text-xs">Review</Link>
        </div>) : <div className="text-sm text-gray-400 text-center py-8">No pending reviews</div>}
      </div>}

      {tab==='documents' && <div className="mt-4">
        {data.recent_documents?.length ? data.recent_documents.map((d:any)=><div key={d.id} className="border rounded p-3 flex justify-between items-center mt-2">
          <div><div className="text-sm font-medium">{d.title}</div><div className="text-xs text-gray-500">v{d.current_version} • {d.status}</div></div>
          <span className="text-xs">{d.file_path}</span>
        </div>) : <div className="text-sm text-gray-400 text-center py-8">No documents</div>}
      </div>}
    </div>

    {data.recent_feedback?.length>0 && <div className="bg-white border rounded-xl p-5 mt-4">
      <h3 className="font-semibold text-sm">Recent Feedback</h3>
      {data.recent_feedback.map((f:any,i:number)=><div key={i} className="text-sm border-t py-2">"{f.remark}" <span className="text-xs text-gray-500">— {f.stage} by {f.reviewer}</span></div>)}
    </div>}
  </div>
}