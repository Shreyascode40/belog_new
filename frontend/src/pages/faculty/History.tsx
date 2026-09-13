import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function History({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [list,setList]=useState<any[]>([])
  const [group,setGroup]=useState('')
  const load=async()=>{
    setLoading(true)
    const params:any={}
    if(group) params.group=group
    const r=await client.get(`/api/v1/${role}/history/`, {params})
    const d=r.data.results||r.data.data||[]
    setList(Array.isArray(d)?d: (r.data.data?.data||[]))
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading history...</div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold">Review History</h1>
    <div className="mt-3 flex gap-2">
      <input placeholder="Group id" value={group} onChange={e=>setGroup(e.target.value)} className="border rounded px-3 py-2 text-sm w-32"/>
      <button onClick={load} className="border px-4 py-2 rounded text-sm">Filter</button>
    </div>
    {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4 text-sm text-gray-400">No review history</div> :
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Group</th><th className="text-left p-3">Decision</th><th className="text-left p-3">Reviewer</th><th className="text-left p-3">Date</th><th className="text-left p-3">Remark</th></tr></thead>
        <tbody>{list.map((a:any)=><tr key={a.id} className="border-t"><td className="p-3">Submission {a.submission}</td><td className="p-3"><span className={`text-xs px-2 py-1 rounded-full ${a.decision==='approved'?'bg-green-100 text-green-700':'bg-red-100'}`}>{a.decision}</span></td><td className="p-3 text-xs">{a.approver}</td><td className="p-3 text-xs">{a.decided_at? new Date(a.decided_at).toLocaleDateString():''}</td><td className="p-3 text-xs max-w-xs truncate">{a.remark||'-'}</td></tr>)}</tbody>
      </table>
    </div>}
  </div>
}