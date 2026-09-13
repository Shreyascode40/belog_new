import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'

export default function Logbook({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [list,setList]=useState<any[]>([])
  const [filters,setFilters]=useState({group:'', week:'', stage:'', status:'', date:''})
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const params:any={}
      if(filters.group) params.group=filters.group
      if(filters.week) params.week=filters.week
      if(filters.stage) params.stage=filters.stage
      if(filters.status) params.status=filters.status
      if(filters.date) params.date=filters.date
      const r=await client.get(`/api/v1/${role}/logbook/`, {params})
      const d=r.data.results||r.data.data||r.data||[]
      const arr=Array.isArray(d)?d: (r.data.data?.data||[])
      setList(arr)
    }catch(e:any){setError(e.response?.data?.message||'Unable to load')}
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading log book...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error} <button onClick={load} className="ml-2 border px-3 py-1 rounded">Retry</button></div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold">Log Book Review</h1>
    <div className="bg-white border rounded-xl p-4 mt-4 flex flex-wrap gap-2">
      <input placeholder="Group id" value={filters.group} onChange={e=>setFilters({...filters, group:e.target.value})} className="border rounded px-2 py-1 text-sm w-24"/>
      <input placeholder="Week" value={filters.week} onChange={e=>setFilters({...filters, week:e.target.value})} className="border rounded px-2 py-1 text-sm w-20"/>
      <input placeholder="Stage" value={filters.stage} onChange={e=>setFilters({...filters, stage:e.target.value})} className="border rounded px-2 py-1 text-sm w-28"/>
      <select value={filters.status} onChange={e=>setFilters({...filters, status:e.target.value})} className="border rounded px-2 py-1 text-sm">
        <option value="">All status</option>
        <option value="submitted">Submitted</option>
        <option value="resubmitted">Resubmitted</option>
        <option value="approved">Approved</option>
        <option value="changes_required">Changes Required</option>
      </select>
      <input type="date" value={filters.date} onChange={e=>setFilters({...filters, date:e.target.value})} className="border rounded px-2 py-1 text-sm"/>
      <button onClick={load} className="bg-blue-600 text-white px-4 py-1 rounded text-sm">Filter</button>
    </div>
    {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4 text-sm text-gray-400">No log entries from assigned groups</div> :
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Group</th><th className="text-left p-3">Week</th><th className="text-left p-3">Date</th><th className="text-left p-3">Work Completed</th><th className="text-left p-3">Status</th><th className="text-right p-3">Action</th></tr></thead>
        <tbody>
          {list.map((s:any)=><tr key={s.id} className="border-t">
            <td className="p-3">G-{s.group_number||s.group}</td>
            <td className="p-3">{s.content?.week||'-'}</td>
            <td className="p-3 text-xs">{s.content?.date|| (s.submitted_at? new Date(s.submitted_at).toLocaleDateString(): '-')}</td>
            <td className="p-3 max-w-xs truncate">{s.content?.work_completed?.slice(0,60)||'-'}</td>
            <td className="p-3"><span className="text-xs px-2 py-1 rounded-full bg-gray-100">{s.status}</span></td>
            <td className="p-3 text-right"><Link to={`/${role}/logbook/${s.id}`} className="text-blue-600 text-xs underline">View / Review</Link></td>
          </tr>)}
        </tbody>
      </table>
    </div>}
  </div>
}