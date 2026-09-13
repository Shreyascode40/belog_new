import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Evaluation({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [reviews,setReviews]=useState<any[]>([])
  const [groupFilter,setGroupFilter]=useState('')
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get(`/api/v1/${role}/evaluations/`, {params: groupFilter?{group:groupFilter}: {}})
      const d=r.data.data||r.data.results||[]
      setReviews(Array.isArray(d)?d: [])
    }catch(e:any){setError(e.response?.data?.message||'Failed')}
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  const saveMark=async(criterion:any, groupId:number)=>{
    const val=prompt(`Marks for ${criterion.name} (max ${criterion.max_marks})?`)
    if(val===null) return
    const num=parseFloat(val)
    if(isNaN(num)) {alert('Enter a number'); return}
    const remarks=prompt('Remarks?')||''
    try{
      await client.post(`/api/v1/${role}/evaluations/`, {criterion: criterion.id, group: groupId, obtained_marks: num, remarks})
      load()
    }catch(e:any){ alert(e.response?.data?.message|| JSON.stringify(e.response?.data?.errors)||'Failed')}
  }
  const finalize=async(id:number)=>{
    if(!confirm('Finalize this review? Marks will be locked.')) return
    try{
      await client.post(`/api/v1/${role}/evaluations/${id}/finalize/`)
      load()
    }catch(e:any){ alert(e.response?.data?.message||'Failed')}
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading evaluations...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold">Evaluation & Marks</h1>
    <p className="text-xs text-gray-500">Criteria and max marks from project configuration — marks are validated on backend</p>
    <div className="mt-3 flex gap-2">
      <input placeholder="Group id filter" value={groupFilter} onChange={e=>setGroupFilter(e.target.value)} className="border rounded px-3 py-2 text-sm w-32"/>
      <button onClick={load} className="border px-4 py-2 rounded text-sm">Filter</button>
    </div>
    {reviews.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4 text-sm text-gray-400">No reviews/criteria configured — ask HOD to create Review + Criteria</div> :
      reviews.map((rev:any)=><div key={rev.id} className="bg-white border rounded-xl p-5 mt-4">
        <div className="flex justify-between">
          <h3 className="font-semibold text-sm">Review {rev.review_number} — {rev.status} — Group G-{rev.group} • {rev.total_obtained_marks}/{rev.total_max_marks}</h3>
          <span className={`text-xs px-2 py-1 rounded-full ${rev.status==='finalized'?'bg-green-100 text-green-700':'bg-amber-100'}`}>{rev.status}</span>
        </div>
        <table className="w-full text-sm mt-3">
          <thead><tr className="text-xs text-gray-400 border-b"><th className="text-left py-2">Criterion</th><th className="text-left py-2">Max</th><th className="text-left py-2">Obtained</th><th className="text-left py-2">Status</th><th className="text-right py-2">Action</th></tr></thead>
          <tbody>
            {rev.criteria?.map((c:any)=>{
              const m=rev.marks?.find((mk:any)=>mk.criterion===c.id)
              return <tr key={c.id} className="border-b last:border-0">
                <td className="py-2"><div className="font-medium">{c.name}</div><div className="text-xs text-gray-500">{c.description}</div></td>
                <td className="py-2">{c.max_marks}</td>
                <td className="py-2">{m? m.obtained_marks : '-'}</td>
                <td className="py-2 text-xs">{m? (m.is_finalized?'Finalized': m.status) : 'Not entered'}</td>
                <td className="py-2 text-right">{rev.status!=='finalized' && <button onClick={()=>saveMark(c, rev.group)} className="text-blue-600 text-xs underline">{m?'Edit':'Enter'}</button>}</td>
              </tr>
            })}
          </tbody>
        </table>
        {rev.status!=='finalized' && <button onClick={()=>finalize(rev.id)} className="mt-3 bg-blue-600 text-white px-4 py-2 rounded text-sm">Finalize Review</button>}
        {rev.status==='finalized' && <div className="text-xs text-green-600 mt-2">Locked — cannot modify except via correction workflow.</div>}
      </div>)}
  </div>
}