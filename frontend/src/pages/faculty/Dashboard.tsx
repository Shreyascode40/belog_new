import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import { useRealtimeTick } from '../../contexts/RealtimeContext'
export default function Dashboard({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get(`/api/v1/${role}/dashboard/`)
      setData(r.data.data)
    }catch(e:any){setError(e.response?.data?.message||'Unable to load dashboard')}
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading dashboard...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center"><div className="text-sm text-red-600">{error}</div><button onClick={load} className="mt-3 border px-4 py-2 rounded text-sm">Retry</button></div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold capitalize">{role} Dashboard</h1>
    <p className="text-xs text-gray-500">Workload overview — all values from backend</p>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
      {[
        ['Assigned Groups', data.assigned_groups],
        ['Pending Reviews', data.pending_reviews],
        ['Pending Log Entries', data.pending_log_entries],
        ['Changes Requested', data.changes_requested],
        ['Approved Submissions', data.approved_submissions],
        ['Completed Reviews', data.completed_reviews],
        ['Total Documents', data.total_documents],
        ['Upcoming Deadlines', data.upcoming_deadlines?.length||0],
      ].map(([k,v])=><div key={k as string} className="bg-white border rounded-xl p-4"><div className="text-xs text-gray-400">{k as string}</div><div className="text-2xl font-bold mt-1">{v as any}</div></div>)}
    </div>
    {data.upcoming_deadlines?.length>0 && <div className="bg-white border rounded-xl p-5 mt-6">
      <h3 className="font-semibold text-sm">Upcoming Deadlines</h3>
      <div className="mt-3 space-y-2 text-sm">
        {data.upcoming_deadlines.map((d:any,i:number)=><div key={i} className="flex justify-between border-b py-2"><span>{d.stage}</span><span className={`text-xs px-2 py-1 rounded-full ${d.overdue?'bg-red-100 text-red-700':'bg-blue-50'}`}>{d.due_date} {d.overdue?'• Overdue':''}</span></div>)}
      </div>
    </div>}
    <div className="flex gap-3 mt-6">
      <Link to={`/${role}/groups`} className="bg-blue-600 text-white px-5 py-2 rounded text-sm">View Assigned Groups</Link>
      <Link to={`/${role}/logbook`} className="border px-5 py-2 rounded text-sm">Review Log Book</Link>
    </div>
  </div>
}
