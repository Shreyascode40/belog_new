import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import client from '../api/client'
export default function Layout(){
  const nav=useNavigate()
  const role=localStorage.getItem('role')||'student'
  const [notifCount,setNotifCount]=useState(0)
  const [notifs,setNotifs]=useState<any[]>([])
  const [showNotifs,setShowNotifs]=useState(false)
  const loadNotifs=async()=>{
    try{
      const r=await client.get('/api/v1/notifications/')
      const list=r.data.results||r.data.data||r.data||[]
      setNotifs(Array.isArray(list)?list:[])
      setNotifCount(list.filter((n:any)=>!n.is_read).length)
    }catch{}
  }
  useEffect(()=>{ loadNotifs(); const id=setInterval(loadNotifs,10000); return ()=>clearInterval(id) },[])
  const markRead=async(id:number)=>{
    await client.post(`/api/v1/notifications/${id}/read/`)
    loadNotifs()
  }
  const logout=()=>{localStorage.clear();nav('/login')}
  return <div className="min-h-screen flex">
    <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col gap-6">
      <h1 className="text-xl font-bold">BE Logbook</h1>
      <nav className="flex flex-col gap-2 text-sm">
        <Link className="hover:bg-slate-800 p-2 rounded" to="/">Dashboard</Link>
        {role==='student'&&<Link className="hover:bg-slate-800 p-2 rounded bg-blue-800" to="/create-group">+ Create Group</Link>}
        <Link className="hover:bg-slate-800 p-2 rounded" to="/groups">Groups</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/projects">Projects</Link>
        {role==='hod'&&<Link className="hover:bg-slate-800 p-2 rounded bg-indigo-800" to="/hod/groups">HOD — All Groups</Link>}
        {role==='hod'&&<Link className="hover:bg-slate-800 p-2 rounded bg-indigo-800" to="/hod/allocate">HOD — Allocate Guide/Reviewer</Link>}
        <Link className="hover:bg-slate-800 p-2 rounded" to="/submissions">Submissions</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/reviews">Reviews</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/documents">Documents</Link>
        {(role==='faculty'||role==='reviewer')&&<Link className="hover:bg-slate-800 p-2 rounded bg-slate-700" to="/faculty/evaluate">Evaluate All Levels</Link>}
        {role==='hod'&&<Link className="hover:bg-slate-800 p-2 rounded" to="/admin">Admin</Link>}
        <button onClick={()=>setShowNotifs(!showNotifs)} className="relative bg-slate-800 p-2 rounded text-left mt-4">
          🔔 Notifications {notifCount>0&&<span className="bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full ml-2">{notifCount}</span>}
        </button>
        {showNotifs&&<div className="bg-slate-800 p-2 rounded max-h-64 overflow-auto">
          {notifs.length===0&&<div className="text-xs opacity-60">No notifications</div>}
          {notifs.slice(0,10).map((n:any)=><div key={n.id} className={`text-xs p-2 mb-1 rounded ${n.is_read?'opacity-60': 'bg-blue-600'}`}>
            <div className="font-semibold">{n.title}</div>
            <div className="opacity-80">{n.message?.slice(0,80)}</div>
            {!n.is_read&&<button onClick={()=>markRead(n.id)} className="text-xs underline">Mark read</button>}
          </div>)}
          <button onClick={async()=>{ await client.post('/api/v1/notifications/mark_all_read/'); loadNotifs()}} className="text-xs underline mt-1">Mark all read</button>
        </div>}
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        <span className="text-xs opacity-70">Role: {role}</span>
        <button onClick={logout} className="bg-red-600 p-2 rounded text-sm">Logout</button>
      </div>
    </aside>
    <main className="flex-1 p-8 bg-gray-50"><Outlet/></main>
  </div>
}
