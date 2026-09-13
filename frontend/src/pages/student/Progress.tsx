import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'
import StatusBadge from '../../components/StatusBadge'

export default function Progress(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  useEffect(()=>{
    client.get('/api/v1/student/progress/').then(r=>setData(r.data.data)).catch(e=>setError(e.response?.data?.message||'Failed')).finally(()=>setLoading(false))
  },[tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading progress...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-4xl mx-auto">
    <h1 className="text-xl font-bold">Project Progress</h1>
    <div className="text-sm text-gray-500">Overall {data.overall_progress}%</div>
    <div className="mt-6 space-y-3">
      {data.stages.map((s:any,i:number)=><div key={s.id} className="bg-white border rounded-xl p-4 flex gap-4">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${['approved','locked'].includes(s.status)?'bg-green-600 text-white': s.status==='submitted'||s.status==='under_review'?'bg-blue-600 text-white': s.status==='changes_required'?'bg-red-600 text-white':'bg-gray-200'}`}>{['approved','locked'].includes(s.status)?'✓':s.order}</div>
        <div className="flex-1">
          <div className="flex justify-between"><span className="font-medium text-sm">{i+1}. {s.name}</span><StatusBadge status={s.status}/></div>
          <div className="text-xs text-gray-500 mt-1">Start: {s.start_date||'-'} • Target: {s.target_date||'-'} • {s.completion_pct}%</div>
          {s.feedback && <div className="text-xs bg-amber-50 border p-2 rounded mt-2">{s.feedback}</div>}
          <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2"><div className="bg-blue-600 h-1.5 rounded-full" style={{width:`${s.completion_pct}%`}}></div></div>
        </div>
      </div>)}
    </div>
    <div className="bg-white border rounded-xl p-5 mt-6">
      <h3 className="font-semibold text-sm">Upcoming Milestones</h3>
      <div className="mt-3 space-y-2 text-sm">
        {data.milestones.map((m:any,i:number)=><div key={i} className="flex justify-between border-b py-2"><span>{m.name}</span><span className="text-xs">{m.due} <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${m.status==='overdue'?'bg-red-100 text-red-700': m.status==='completed'?'bg-green-100': 'bg-blue-50'}`}>{m.status}</span></span></div>)}
        {data.milestones.length===0 && <div className="text-xs text-gray-400">No milestones configured</div>}
      </div>
    </div>
  </div>
}