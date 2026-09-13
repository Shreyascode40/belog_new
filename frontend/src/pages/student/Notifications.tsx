import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Notifications(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [list,setList]=useState<any[]>([])
  const [filter,setFilter]=useState<'all'|'unread'>('all')
  const load=async()=>{
    setLoading(true)
    const url=filter==='unread'?'/api/v1/student/notifications/?is_read=false':'/api/v1/student/notifications/'
    const r=await client.get(url)
    setList(r.data.data||[])
    setLoading(false)
  }
  useEffect(()=>{load()},[filter])
  const mark=async(id:number)=>{
    await client.post(`/api/v1/student/notifications/${id}/read/`)
    load()
  }
  const markAll=async()=>{
    await client.post('/api/v1/student/notifications/mark_all_read/')
    load()
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading notifications...</div>
  return <div className="max-w-3xl mx-auto">
    <div className="flex justify-between items-center">
      <h1 className="text-xl font-bold">Notifications</h1>
      <button onClick={markAll} className="border px-3 py-1 rounded text-xs">Mark all as read</button>
    </div>
    <div className="flex gap-2 mt-3">
      <button onClick={()=>setFilter('all')} className={`px-3 py-1 rounded text-xs ${filter==='all'?'bg-blue-600 text-white':'border'}`}>All</button>
      <button onClick={()=>setFilter('unread')} className={`px-3 py-1 rounded text-xs ${filter==='unread'?'bg-blue-600 text-white':'border'}`}>Unread</button>
    </div>
    <div className="mt-4 space-y-2">
      {list.length===0 ? <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-400">No notifications</div> :
        list.map((n:any)=><div key={n.id} className={`bg-white border rounded-xl p-4 flex justify-between ${!n.is_read?'border-blue-300 bg-blue-50':''}`}>
          <div>
            <div className="font-medium text-sm">{n.title} {!n.is_read && <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full ml-2">New</span>}</div>
            <div className="text-sm text-gray-600">{n.message}</div>
            <div className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</div>
          </div>
          {!n.is_read && <button onClick={()=>mark(n.id)} className="text-xs text-blue-600 underline self-start">Mark read</button>}
        </div>)}
    </div>
  </div>
}