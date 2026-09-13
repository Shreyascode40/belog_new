import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Notifications({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [list,setList]=useState<any[]>([])
  const load=async()=>{
    setLoading(true)
    const r=await client.get(`/api/v1/${role}/notifications/`)
    const d=r.data.results||r.data.data||[]
    setList(Array.isArray(d)?d: (r.data.data?.data||[]))
    setLoading(false)
  }
  useEffect(()=>{load()},[role, tick])
  const mark=async(id:number)=>{
    await client.post(`/api/v1/${role}/notifications/${id}/read/`)
    load()
  }
  const markAll=async()=>{
    await client.post(`/api/v1/${role}/notifications/mark_all_read/`)
    load()
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading notifications...</div>
  return <div className="max-w-3xl mx-auto">
    <div className="flex justify-between"><h1 className="text-xl font-bold">Notifications</h1><button onClick={markAll} className="border px-3 py-1 rounded text-xs">Mark all read</button></div>
    <div className="mt-4 space-y-2">
      {list.length===0? <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-400">No notifications</div> :
        list.map((n:any)=><div key={n.id} className={`bg-white border rounded-xl p-4 flex justify-between ${!n.is_read?'border-blue-300 bg-blue-50':''}`}>
          <div><div className="font-medium text-sm">{n.title} {!n.is_read && <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full ml-2">New</span>}</div><div className="text-sm text-gray-600">{n.message}</div><div className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</div></div>
          {!n.is_read && <button onClick={()=>mark(n.id)} className="text-xs text-blue-600 underline">Mark read</button>}
        </div>)}
    </div>
  </div>
}