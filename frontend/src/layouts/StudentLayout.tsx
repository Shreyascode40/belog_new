import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import client from '../api/client'
import { useRealtimeTick } from '../contexts/RealtimeContext'

const navItems=[
  {to:'/student/dashboard', label:'Dashboard', icon:'🏠'},
  {to:'/student/profile', label:'My Profile', icon:'👤'},
  {to:'/student/group', label:'My Group', icon:'👥'},
  {to:'/student/logbook', label:'Log Book', icon:'📖'},
  {to:'/student/progress', label:'Progress', icon:'📊'},
  {to:'/student/documents', label:'Documents', icon:'📄'},
  {to:'/student/reviews', label:'Reviews & Feedback', icon:'⭐'},
  {to:'/student/notifications', label:'Notifications', icon:'🔔'},
  {to:'/student/final-logbook', label:'Final Log Book', icon:'📕'},
]

export default function StudentLayout(){
  const loc=useLocation()
  const nav=useNavigate()
  const tick=useRealtimeTick()
  const [unread,setUnread]=useState(0)
  useEffect(()=>{
    client.get('/api/v1/student/notifications/').then(r=>{
      const d=r.data.data|| r.data.results||[]
      const arr=Array.isArray(d)?d: (r.data.data||[])
      setUnread(arr.filter((n:any)=>!n.is_read).length)
    }).catch(()=>{})
  },[loc.pathname, tick])
  const logout=()=>{localStorage.clear();nav('/login')}
  return <div className="min-h-screen flex">
    <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col gap-4 hidden md:flex">
      <h1 className="text-lg font-bold tracking-wide">BE LOGBOOK</h1>
      <div className="text-xs opacity-60">Student Section</div>
      <nav className="flex flex-col gap-1 mt-2">
        {navItems.map(i=>{
          const active=loc.pathname===i.to || (i.to!=='/student/dashboard' && loc.pathname.startsWith(i.to))
          return <Link key={i.to} to={i.to} className={`px-3 py-2 rounded text-sm flex justify-between items-center ${active?'bg-slate-700':'hover:bg-slate-800'}`}>
            <span>{i.icon} {i.label}</span>
            {i.to==='/student/notifications' && unread>0 && <span className="bg-red-600 text-xs px-1.5 py-0.5 rounded-full">{unread}</span>}
          </Link>
        })}
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        <Link to="/profile" className="bg-slate-800 px-3 py-2 rounded text-sm text-center">⚙ Settings</Link>
        <button onClick={logout} className="bg-red-600 px-3 py-2 rounded text-sm">🚪 Logout</button>
        <div className="text-xs opacity-50 text-center">{localStorage.getItem('email')||''}</div>
      </div>
    </aside>
    <div className="flex-1 flex flex-col bg-gray-50 min-h-screen">
      <div className="md:hidden bg-slate-900 text-white p-3 flex gap-2 overflow-x-auto text-xs">
        {navItems.map(i=><Link key={i.to} to={i.to} className={`whitespace-nowrap px-2 py-1 rounded ${loc.pathname===i.to?'bg-slate-700':''}`}>{i.icon}</Link>)}
      </div>
      <main className="flex-1 p-4 md:p-8"><Outlet/></main>
    </div>
  </div>
}
