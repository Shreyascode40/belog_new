import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Documents({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [list,setList]=useState<any[]>([])
  const load=async()=>{
    setLoading(true);setError('')
    try{
      const r=await client.get(`/api/v1/${role}/documents/`)
      const d=r.data.results||r.data.data||[]
      const arr=Array.isArray(d)?d: (r.data.data?.data||[])
      setList(arr)
    }catch(e:any){setError(e.response?.data?.message||'Failed')}
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  const review=async(id:number, decision:string)=>{
    const remark=prompt(`Feedback for ${decision}?`)||''
    if(decision==='changes_required' && !remark.trim()){ alert('Feedback required'); return }
    try{
      await client.post(`/api/v1/${role}/documents/${id}/review/`, {decision, feedback:remark})
      load()
    }catch(e:any){ alert(e.response?.data?.message||'Failed')}
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading documents...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-6xl mx-auto">
    <h1 className="text-xl font-bold">Document Review</h1>
    {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center mt-4 text-sm text-gray-400">No documents from assigned groups</div> :
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Document</th><th className="text-left p-3">Group</th><th className="text-left p-3">Version</th><th className="text-left p-3">Status</th><th className="text-left p-3">Versions</th><th className="text-right p-3">Actions</th></tr></thead>
        <tbody>
          {list.map((d:any)=><tr key={d.id} className="border-t">
            <td className="p-3 font-medium">{d.title}</td>
            <td className="p-3">G-{d.group}</td>
            <td className="p-3">v{d.current_version}</td>
            <td className="p-3 text-xs">{d.status}</td>
            <td className="p-3 text-xs">{d.versions?.map((v:any)=>`v${v.version_number}`).join(' → ')||`v${d.current_version}`}</td>
            <td className="p-3 text-right flex gap-1 justify-end">
              <button onClick={()=>review(d.id,'approved')} className="bg-green-600 text-white px-2 py-1 rounded text-xs">Approve</button>
              <button onClick={()=>review(d.id,'changes_required')} className="bg-red-600 text-white px-2 py-1 rounded text-xs">Request Changes</button>
            </td>
          </tr>)}
        </tbody>
      </table>
    </div>}
  </div>
}