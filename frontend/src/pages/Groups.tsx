import { useEffect, useState } from 'react'
import client from '../api/client'
import Badge from '../components/Badge'
export default function Groups(){
  const role=localStorage.getItem('role')
  const [groups,setGroups]=useState<any[]>([])
  useEffect(()=>{client.get('/api/v1/groups/').then(r=>setGroups(r.data.results||r.data.data||[])).catch(()=>{})},[])
  return <div>
    <div className="flex justify-between items-center">
      <h1 className="text-2xl font-bold">Project Groups</h1>
      {role==='student'&&<a href="/create-group" className="bg-blue-600 text-white px-4 py-2 rounded text-sm">+ Create Group</a>}
    </div>
    <p className="text-xs text-gray-500 mt-1">Group No. auto-assigned per AY — Guide shows Pending until HOD assigns.</p>
    <div className="bg-white rounded-xl border mt-6 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50"><tr><th className="p-3 text-left">Group</th><th className="p-3">Status</th><th className="p-3">Progress</th></tr></thead>
        <tbody>{groups.map((g:any)=><tr key={g.id} className="border-t"><td className="p-3 font-medium">Group {g.group_number} — {g.project?.title||''}</td><td className="p-3 text-center"><Badge status={g.status}/></td><td className="p-3 text-center">{g.progress||0}%</td></tr>)}
        {groups.length===0&&<tr><td colSpan={3} className="p-8 text-center text-gray-400">No groups yet {role==='student'?<>— <a href="/create-group" className="text-blue-600 underline">Create a Group</a></>: '— HOD will create/allocate groups.'}</td></tr>}</tbody>
      </table>
    </div>
  </div>
}
