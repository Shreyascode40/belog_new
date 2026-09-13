import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function StudentGroup(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [group,setGroup]=useState<any>(null)
  const [msg,setMsg]=useState('')
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get('/api/v1/student/group/')
      setGroup(r.data.data)
    }catch(e:any){setError(e.response?.data?.message||'Unable to load group information.')}
    setLoading(false)
  }
  useEffect(()=>{load()},[tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading group profile...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center"><div className="text-sm text-red-600">{error}</div><button onClick={load} className="mt-3 border px-4 py-2 rounded text-sm">Retry</button></div>
  if(!group) return <div className="bg-white border rounded-xl p-10 text-center text-sm text-gray-500">No group found</div>
  return <div className="max-w-5xl mx-auto">
    <h1 className="text-xl font-bold">My Group</h1>
    <div className="bg-white border rounded-xl p-6 mt-4 flex justify-between flex-wrap gap-4">
      <div>
        <div className="text-xs tracking-widest text-blue-600 font-semibold">BE PROJECT</div>
        <h2 className="text-lg font-bold">Group {group.group_number} — {group.project_detail?.title||'Untitled'}</h2>
        <div className="text-xs text-gray-500">{group.academic_year_detail?.year_label} • {group.department_detail?.name} {group.semester?`• ${group.semester.name}`:''}</div>
      </div>
      <div className="text-right text-xs">
        {group.is_locked?<span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full">Locked</span>: group.can_edit?<span className="bg-green-50 text-green-700 px-3 py-1 rounded-full">Editable</span>:<span className="bg-slate-100 px-3 py-1 rounded-full">Read-only</span>}
      </div>
    </div>

    <div className="grid md:grid-cols-2 gap-4 mt-4">
      <div className="bg-white border rounded-xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide">Project Information</h3>
        <div className="mt-3 text-sm space-y-2">
          <div><span className="text-gray-400 text-xs">Group Number</span><div className="font-medium">{group.group_number}</div></div>
          <div><span className="text-gray-400 text-xs">Academic Year</span><div className="font-medium">{group.academic_year_detail?.year_label}</div></div>
          <div><span className="text-gray-400 text-xs">Department / Semester</span><div className="font-medium">{group.department_detail?.name} {group.semester?`• Sem ${group.semester.number}`:''}</div></div>
          <div><span className="text-gray-400 text-xs">Project Title</span><div className="font-medium">{group.project_detail?.title||'-'}</div></div>
          <div><span className="text-gray-400 text-xs">Domain</span><div className="font-medium">{group.project_detail?.area_domain||'-'}</div></div>
          <div><span className="text-gray-400 text-xs">Description</span><div className="whitespace-pre-wrap">{group.project_detail?.description||'-'}</div></div>
          <div><span className="text-gray-400 text-xs">Status / Progress</span><div className="font-medium">{group.status} • {group.progress}%</div></div>
        </div>
      </div>
      <div className="bg-white border rounded-xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide">Guide Information</h3>
        {group.guide_detail ? <div className="mt-3 text-sm space-y-1">
          <div className="font-medium">{group.guide_detail.name}</div>
          <div className="text-gray-600">{group.guide_detail.email}</div>
          <div className="text-xs text-gray-500">{group.guide_detail.designation} • {group.guide_detail.department}</div>
        </div> : <div className="mt-3 text-sm text-gray-400 bg-slate-50 border-dashed border rounded p-4 text-center">No guide assigned</div>}
      </div>
    </div>

    <div className="bg-white border rounded-xl p-5 mt-4">
      <h3 className="text-xs font-semibold uppercase tracking-wide">Group Members</h3>
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-sm">
          <thead><tr className="text-xs text-gray-400 border-b"><th className="text-left py-2">Name</th><th className="text-left py-2">PRN / Roll</th><th className="text-left py-2">Email</th><th className="text-left py-2">Role</th></tr></thead>
          <tbody>{group.members?.map((m:any,i:number)=><tr key={m.id} className="border-b last:border-0"><td className="py-2 font-medium">{m.student_detail?.name}</td><td>{m.student_detail?.roll_number||'-'}</td><td>{m.student_detail?.email}</td><td><span className={`text-xs px-2 py-0.5 rounded-full ${m.role==='leader'?'bg-blue-100 text-blue-700':'bg-slate-100'}`}>{m.role}</span></td></tr>)}</tbody>
        </table>
      </div>
    </div>
    {msg && <div className="mt-3 text-sm text-green-700 bg-green-50 border p-3 rounded">{msg}</div>}
  </div>
}