import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../../api/client'

export default function Groups({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [list,setList]=useState<any[]>([])
  const [search,setSearch]=useState('')
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get(`/api/v1/${role}/groups/`, {params: search?{search}: {}})
      const d=r.data.results||r.data.data||r.data||[]
      const arr=Array.isArray(d)?d: (r.data.data?.data||[])
      setList(arr)
    }catch(e:any){setError(e.response?.data?.message||'Unable to load groups')}
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading groups...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error} <button onClick={load} className="ml-2 border px-3 py-1 rounded">Retry</button></div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold">Assigned Groups</h1>
    <div className="mt-3 flex gap-2">
      <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search group/project" className="border rounded px-3 py-2 text-sm flex-1 max-w-xs"/>
      <button onClick={load} className="border px-4 py-2 rounded text-sm">Search</button>
    </div>
    {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4 text-sm text-gray-400">No groups assigned</div> :
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Group</th><th className="text-left p-3">Project</th><th className="text-left p-3">Students</th><th className="text-left p-3">Progress</th><th className="text-left p-3">Stage</th><th className="text-left p-3">Pending Action</th><th className="text-right p-3">Action</th></tr></thead>
        <tbody>
          {list.map((g:any)=><tr key={g.id} className="border-t">
            <td className="p-3 font-medium">G-{g.group_number}</td>
            <td className="p-3">{g.project_detail?.title||'-'}</td>
            <td className="p-3">{g.students_count ?? g.members?.length ?? '-'}</td>
            <td className="p-3">{g.progress_value ?? g.progress}% <div className="w-20 bg-gray-200 h-1 rounded-full mt-1"><div className="bg-blue-600 h-1 rounded-full" style={{width:`${g.progress_value ?? g.progress}%`}}></div></div></td>
            <td className="p-3 text-xs">{g.project_detail?.title? 'Implementation':'Literature'}</td>
            <td className="p-3 text-xs">{g.pending_action? <span className="bg-amber-100 text-amber-800 px-2 py-1 rounded-full text-xs">{g.pending_action}</span> : '-'}</td>
            <td className="p-3 text-right"><Link to={`/${role}/groups/${g.id}`} className="text-blue-600 text-xs underline">View Group</Link></td>
          </tr>)}
        </tbody>
      </table>
    </div>}
  </div>
}