import { useEffect, useState } from 'react'
import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import StatusBadge from '../../components/StatusBadge'

export default function StudentDashboard(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get('/api/v1/student/dashboard/')
      setData(r.data.data)
    }catch(e:any){setError(e.response?.data?.message||'Unable to load project information.')}
    setLoading(false)
  }
  useEffect(()=>{load()},[tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading your project...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center"><div className="text-red-600 text-sm">{error}</div><button onClick={load} className="mt-3 border px-4 py-2 rounded text-sm">Retry</button></div>
  if(!data) return null
  if(!data.has_group) return <div className="max-w-3xl mx-auto text-center bg-white border rounded-xl p-10">
    <h2 className="text-lg font-semibold">No group found</h2>
    <p className="text-sm text-gray-500 mt-2">You're not part of a project group yet. Create one via Cover Page.</p>
    <Link to="/cover" className="mt-4 inline-block bg-blue-600 text-white px-5 py-2 rounded">Go to Cover Page</Link>
  </div>
  const s=data.stats
  return <div className="max-w-6xl mx-auto">
    <div className="bg-white border rounded-xl p-6 flex flex-wrap justify-between gap-4">
      <div>
        <h1 className="text-xl font-bold">Welcome, {data.welcome}</h1>
        <div className="text-sm text-gray-600 mt-1">Group: G-{data.group.group_number} &nbsp; Project: {data.project?.title||'-'} &nbsp; Guide: {data.guide?.name||'Pending'}</div>
      </div>
      <div className="text-right">
        <div className="text-xs text-gray-400">Overall Project Progress</div>
        <div className="text-2xl font-bold">{data.progress}%</div>
        <div className="w-40 bg-gray-200 h-2 rounded-full mt-1"><div className="bg-blue-600 h-2 rounded-full" style={{width:`${data.progress}%`}}></div></div>
      </div>
    </div>

    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mt-6">
      {[
        ['Total Log Entries', s.total_log_entries],
        ['Pending Verification', s.pending_verification],
        ['Approved Entries', s.approved_entries],
        ['Changes Requested', s.changes_requested],
        ['Documents Submitted', s.documents_submitted],
        ['Overall Progress', `${s.overall_progress}%`],
      ].map(([k,v])=><div key={k as string} className="bg-white border rounded-xl p-4 text-center"><div className="text-xs text-gray-400">{k as string}</div><div className="text-xl font-bold mt-1">{v as any}</div></div>)}
    </div>

    <div className="grid md:grid-cols-2 gap-4 mt-6">
      <div className="bg-white border rounded-xl p-5">
        <h3 className="font-semibold text-sm">Project Status</h3>
        <div className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-gray-500">Current Stage</span><span className="font-medium">{data.current_stage?.name||'-'}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Status</span><span>{data.current_stage && <StatusBadge status={data.current_stage.status}/>}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Next Deadline</span><span className="text-xs">{data.next_deadline ? `${data.next_deadline.stage} — ${data.next_deadline.due_date}` : '—'}</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Last Submission</span><span className="text-xs">{data.last_submission ? new Date(data.last_submission.submitted_at||data.last_submission.created_at).toLocaleDateString() : '—'}</span></div>
        </div>
        {data.pending_actions?.length>0 && <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">Next Action: {data.pending_actions[0]}</div>}
      </div>
      <div className="bg-white border rounded-xl p-5">
        <h3 className="font-semibold text-sm">Pending Actions</h3>
        <ul className="mt-3 space-y-2 text-sm">
          {data.pending_actions?.length ? data.pending_actions.map((a:string,i:number)=><li key={i} className="flex gap-2"><span className="text-blue-600">•</span>{a}</li>) : <li className="text-gray-400">No pending actions</li>}
        </ul>
        <Link to="/student/logbook/new" className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded text-sm">Submit weekly log entry</Link>
      </div>
    </div>
  </div>
}
