import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Progress({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [data,setData]=useState<any>(null)
  const [group,setGroup]=useState('')
  const [loading,setLoading]=useState(true)
  const load=async(gid?:string)=>{
    setLoading(true)
    const r=await client.get(`/api/v1/${role}/progress/`, {params: gid?{group:gid}: {}})
    setData(r.data.data)
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading progress...</div>
  if(!group || !data?.stages){
    return <div className="max-w-4xl mx-auto">
      <h1 className="text-xl font-bold">Project Progress Monitoring</h1>
      <p className="text-xs text-gray-500">Progress derived from approved milestones — not manually editable</p>
      <div className="bg-white border rounded-xl p-5 mt-4">
        <div className="grid md:grid-cols-2 gap-3">
          {Array.isArray(data) && data.map((g:any)=><div key={g.group_id} className="border rounded p-4 flex justify-between items-center">
            <div><div className="font-medium text-sm">G-{g.group_number}</div><div className="text-xs text-gray-500">{g.project}</div></div>
            <div className="text-right"><div className="text-lg font-bold">{g.progress}%</div><button onClick={()=>{setGroup(String(g.group_id)); load(String(g.group_id))}} className="text-xs text-blue-600 underline">View detail</button></div>
          </div>)}
          {Array.isArray(data) && data.length===0 && <div className="text-sm text-gray-400">No groups</div>}
        </div>
      </div>
    </div>
  }
  return <div className="max-w-4xl mx-auto">
    <button onClick={()=>{setGroup(''); load()}} className="text-sm text-blue-600 underline">← Back to overview</button>
    <h1 className="text-xl font-bold mt-2">Group {data.group} — {data.overall}%</h1>
    <div className="mt-4 space-y-2">
      {data.stages.map((s:any)=><div key={s.id} className="bg-white border rounded-xl p-4 flex justify-between">
        <span className="text-sm">{s.order}. {s.name}</span>
        <span className={`text-xs px-2 py-1 rounded-full ${s.pct===100?'bg-green-100 text-green-700': s.pct===0?'bg-gray-100':'bg-yellow-100'}`}>{s.status} • {s.pct}%</span>
      </div>)}
    </div>
  </div>
}