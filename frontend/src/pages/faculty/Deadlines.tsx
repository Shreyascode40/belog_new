import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Deadlines({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [data,setData]=useState<any>(null)
  const [loading,setLoading]=useState(true)
  useEffect(()=>{
    client.get(`/api/v1/${role}/deadlines/`).then(r=>setData(r.data.data)).finally(()=>setLoading(false))
  },[role])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading deadlines...</div>
  return <div className="max-w-4xl mx-auto">
    <h1 className="text-xl font-bold">Calendar / Deadlines</h1>
    <div className="bg-white border rounded-xl p-5 mt-4">
      <h3 className="font-semibold text-sm">Upcoming & Overdue</h3>
      {data.deadlines?.length ? data.deadlines.map((d:any,i:number)=><div key={i} className="flex justify-between border-b py-3 text-sm"><span>{d.stage}</span><span className={`text-xs px-2 py-1 rounded-full ${d.overdue?'bg-red-100 text-red-700': d.due_today?'bg-amber-100':'bg-blue-50'}`}>{d.due_date} {d.overdue?'• Overdue': d.due_today?'• Due Today':''}</span></div>) : <div className="text-sm text-gray-400 py-8 text-center">No deadlines</div>}
    </div>
    {data.pending_submissions?.length>0 && <div className="bg-white border rounded-xl p-5 mt-4">
      <h3 className="font-semibold text-sm">Pending Submissions</h3>
      {data.pending_submissions.map((p:any,i:number)=><div key={i} className="flex justify-between py-2 text-sm border-b"><span>G-{p.group_number} — {p.stage}</span><span className="text-xs text-gray-500">{p.submitted_at? new Date(p.submitted_at).toLocaleDateString():''}</span></div>)}
    </div>}
  </div>
}