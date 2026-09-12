import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import Badge from '../components/Badge'

export default function HODGroups(){
  const nav = useNavigate()
  const [groups,setGroups]=useState<any[]>([])
  const [selected,setSelected]=useState<any>(null)
  const [detail,setDetail]=useState<any>(null)
  const [level,setLevel]=useState<any>(null)
  const [msg,setMsg]=useState('')
  const load=async()=>{
    const r=await client.get('/api/v1/groups/')
    setGroups(r.data.results||r.data.data||[])
  }
  useEffect(()=>{ load() },[])
  const openGroup=async(g:any)=>{
    setSelected(g)
    const [memRes, lvlRes] = await Promise.all([
      client.get(`/api/v1/groups/${g.id}/`),
      client.get(`/api/v1/groups/${g.id}/level/`).catch(()=>({data:{data:null}}))
    ])
    setDetail(memRes.data)
    setLevel(lvlRes.data.data)
  }
  const grantAccess=async(gid:number, stageId:number, grant:boolean)=>{
    await client.post(`/api/v1/groups/${gid}/stages/${stageId}/access-grant/`, {granted: grant})
    setMsg(grant?'Access granted by HOD':'Access revoked')
    openGroup(groups.find(x=>x.id===gid))
  }
  const hodApprove=async(gid:number)=>{
    await client.post(`/api/v1/groups/${gid}/hod-final-approval/`, {approved:true})
    setMsg('HOD Final Approval granted — now PDF can be generated')
  }
  const generate=async(gid:number)=>{
    try{
      const r=await client.post(`/api/v1/groups/${gid}/logbook/generate/`)
      setMsg(`PDF v${r.data.data.version} generated`)
      window.open(`http://localhost:8000/media/${r.data.data.pdf_path}`,'_blank')
    }catch(e:any){ setMsg(e.response?.data?.errors ? JSON.stringify(e.response.data.errors) : e.response?.data?.message) }
  }
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-2xl font-bold">HOD — All Groups</h1>
    <p className="text-xs text-gray-500 mt-1">Check every group personally — click any row to see members, guide, reviewer, progress, level, submissions, and give permissions.</p>
    <div className="bg-white rounded-xl border mt-6 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-900 text-white"><tr><th className="p-3 text-left">Group</th><th className="p-3">Project</th><th className="p-3">Members</th><th className="p-3">Progress</th><th className="p-3">Status</th><th className="p-3">Action</th></tr></thead>
        <tbody>
          {groups.map((g:any)=><tr key={g.id} className="border-t hover:bg-blue-50 cursor-pointer" onClick={()=>openGroup(g)}>
            <td className="p-3 font-medium">Group {g.group_number} <span className="text-xs text-gray-500">AY {g.academic_year}</span></td>
            <td className="p-3">{g.project?.title||'—'}</td>
            <td className="p-3 text-center">{g.members?.length??'—'}</td>
            <td className="p-3 text-center">{g.progress||0}%</td>
            <td className="p-3 text-center"><Badge status={g.status}/></td>
            <td className="p-3 text-center"><button onClick={(e)=>{e.stopPropagation(); openGroup(g)}} className="text-blue-600 underline text-xs">View</button></td>
          </tr>)}
          {groups.length===0&&<tr><td colSpan={6} className="p-8 text-center text-gray-400">No groups</td></tr>}
        </tbody>
      </table>
    </div>

    {selected && detail && <div className="bg-white p-6 rounded-xl border mt-6">
      <div className="flex justify-between items-center">
        <h2 className="font-bold">Group {detail.group_number} — Detail</h2>
        <button onClick={()=>setSelected(null)} className="border px-3 py-1 rounded text-sm">Close</button>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div><b>Project:</b> {detail.project?.title||'—'} ({detail.project?.area_domain||''})</div>
        <div><b>Status:</b> {detail.status} • Progress {detail.progress}%</div>
        <div><b>AY:</b> {detail.academic_year} • Dept {detail.department}</div>
        <div><b>Current Level:</b> {level? `${level.current_level_order} — ${level.current_level_name} (${level.current_level_status})` : 'loading...'}</div>
      </div>
      <div className="mt-4">
        <h3 className="font-semibold text-sm">Members ({detail.members?.length||0}/4)</h3>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {detail.members?.map((m:any)=><div key={m.id} className="border p-3 rounded bg-gray-50 text-xs">
            <div><b>{m.student_detail?.name||m.student}</b> — {m.role} — {m.status} {m.acknowledged?'✓':''}</div>
            <div>Roll: {m.student_detail?.roll_number||m.te_result||'—'} | Mobile: {m.student_detail?.mobile||'—'} | Seat: {m.student_detail?.exam_seat_number||'—'}</div>
            <div>Email: {m.student_detail?.email||''} | TE: {m.te_result||'—'} | Contribution: {m.contribution||'—'}</div>
          </div>)}
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mt-6">
        <button onClick={()=>nav(`/hod/allocate?group=${selected.id}`)} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">Allocate Guide / Reviewer</button>
        {level && <button onClick={()=>grantAccess(selected.id, level.stage_id, true)} className="bg-green-600 text-white px-4 py-2 rounded text-sm">Grant Access (Level {level.current_level_order})</button>}
        {level && <button onClick={()=>grantAccess(selected.id, level.stage_id, false)} className="border px-4 py-2 rounded text-sm">Revoke Access</button>}
        <button onClick={()=>hodApprove(selected.id)} className="bg-slate-800 text-white px-4 py-2 rounded text-sm">Give Permission — HOD Final Approval</button>
        <button onClick={()=>generate(selected.id)} className="bg-indigo-600 text-white px-4 py-2 rounded text-sm">Generate PDF</button>
        <button onClick={async()=>{
          const r=await client.get(`/api/v1/groups/${selected.id}/level/`)
          setLevel(r.data.data); setMsg(`Refreshed: ${r.data.data.current_level_name} — ${r.data.data.current_level_status}`)
        }} className="border px-4 py-2 rounded text-sm">Refresh Level</button>
      </div>
      {msg&&<div className="text-sm text-blue-600 mt-3 p-2 bg-blue-50 rounded">{msg}</div>}
      <div className="text-xs text-gray-500 mt-2">Permissions are server-enforced (HOD role only). Guide/Reviewer allocation and AccessGrant are audited.</div>
    </div>}
  </div>
}
