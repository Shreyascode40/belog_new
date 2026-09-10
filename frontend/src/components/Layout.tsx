import { Link, Outlet, useNavigate } from 'react-router-dom'
export default function Layout(){
  const nav=useNavigate()
  const role=localStorage.getItem('role')||'student'
  const logout=()=>{localStorage.clear();nav('/login')}
  return <div className="min-h-screen flex">
    <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col gap-6">
      <h1 className="text-xl font-bold">BE Logbook</h1>
      <nav className="flex flex-col gap-2 text-sm">
        <Link className="hover:bg-slate-800 p-2 rounded" to="/">Dashboard</Link>
        <Link className="hover:bg-slate-800 p-2 rounded bg-blue-800" to="/create-group">+ Create Group</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/groups">Groups</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/projects">Projects</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/submissions">Submissions</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/reviews">Reviews</Link>
        <Link className="hover:bg-slate-800 p-2 rounded" to="/documents">Documents</Link>
        {role==='hod'&&<Link className="hover:bg-slate-800 p-2 rounded" to="/admin">Admin</Link>}
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        <span className="text-xs opacity-70">Role: {role}</span>
        <button onClick={logout} className="bg-red-600 p-2 rounded text-sm">Logout</button>
      </div>
    </aside>
    <main className="flex-1 p-8 bg-gray-50"><Outlet/></main>
  </div>
}
