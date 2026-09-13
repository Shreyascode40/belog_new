import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Audit({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [list,setList]=useState<any[]>([])
  const load=async()=>{
    setLoading(true)
    const r=await client.get(`/api/v1/${role}/audit/`)
    setList(r.data.data||[])
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading audit...</div>
  return <div className="max-w-4xl mx-auto">
    <h1 className="text-xl font-bold">Audit Trail</h1>
    <p className="text-xs text-gray-500">Append-only — no delete/modify</p>
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      {list.length===0? <div className="p-12 text-center text-sm text-gray-400">No audit records</div> :
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Actor</th><th className="text-left p-3">Role</th><th className="text-left p-3">Action</th><th className="text-left p-3">Object</th><th className="text-left p-3">Time</th></tr></thead>
        <tbody>{list.map((a:any)=><tr key={a.id} className="border-t"><td className="p-3 text-xs">{a.actor}</td><td className="p-3 text-xs">{a.actor_role}</td><td className="p-3 text-xs">{a.action}</td><td className="p-3 text-xs">{a.entity_type} {a.entity_id}</td><td className="p-3 text-xs">{a.timestamp? new Date(a.timestamp).toLocaleString():''}</td></tr>)}</tbody>
      </table>}
    </div>
  </div>
}