import { useEffect, useState } from 'react'
import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import StatusBadge from '../../components/StatusBadge'

export default function Logbook(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [list,setList]=useState<any[]>([])
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get('/api/v1/student/logbook/')
      setList(r.data.data||[])
    }catch(e:any){setError(e.response?.data?.message||'Unable to load log entries')}
    setLoading(false)
  }
  useEffect(()=>{load()},[tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading log book...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center"><div className="text-sm text-red-600">{error}</div><button onClick={load} className="mt-3 border px-4 py-2 rounded text-sm">Retry</button></div>
  return <div className="max-w-5xl mx-auto">
    <div className="flex justify-between items-center">
      <h1 className="text-xl font-bold">Digital Log Book</h1>
      <Link to="/student/logbook/new" className="bg-blue-600 text-white px-4 py-2 rounded text-sm">+ New Entry</Link>
    </div>
    {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4">
      <div className="text-sm text-gray-500">No log entries yet.</div>
      <Link to="/student/logbook/new" className="mt-3 inline-block bg-blue-600 text-white px-5 py-2 rounded text-sm">Create First Entry</Link>
    </div> : <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Week</th><th className="text-left p-3">Date</th><th className="text-left p-3">Activity / Stage</th><th className="text-left p-3">Status</th><th className="text-left p-3">Submitted</th><th className="text-left p-3">Verified By</th><th className="text-right p-3">Action</th></tr></thead>
        <tbody>
          {list.map((s:any)=><tr key={s.id} className="border-t">
            <td className="p-3">{s.content?.week||'-'}</td>
            <td className="p-3 text-xs">{s.content?.date|| (s.created_at? new Date(s.created_at).toLocaleDateString(): '-')}</td>
            <td className="p-3">{s.section?.stage_name|| s.content?.project_stage || s.section?.title || '-'}</td>
            <td className="p-3"><StatusBadge status={s.status}/></td>
            <td className="p-3 text-xs">{s.submitted_at? new Date(s.submitted_at).toLocaleDateString(): '-'}</td>
            <td className="p-3 text-xs">{s.reviewed_by||'-'}</td>
            <td className="p-3 text-right">
              {s.status==='draft' ? <Link to={`/student/logbook/${s.id}`} className="text-blue-600 text-xs underline">Edit</Link> : s.status==='changes_required' ? <Link to={`/student/logbook/${s.id}`} className="text-red-600 text-xs underline">Edit & Resubmit</Link> : <Link to={`/student/logbook/${s.id}`} className="text-xs underline">View</Link>}
            </td>
          </tr>)}
        </tbody>
      </table>
    </div>}
  </div>
}
