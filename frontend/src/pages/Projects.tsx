import { useEffect, useState } from 'react'
import client from '../api/client'
export default function Projects(){
  const [list,setList]=useState<any[]>([])
  useEffect(()=>{client.get('/api/v1/projects/').then(r=>setList(r.data.results||r.data.data||[]))},[])
  return <div>
    <h1 className="text-2xl font-bold">Projects</h1>
    <div className="grid grid-cols-2 gap-4 mt-6">
      {list.map((p:any)=><div key={p.id} className="bg-white p-5 rounded-xl border"><div className="font-semibold">{p.title}</div><div className="text-sm text-gray-500">{p.area_domain}</div><div className="text-xs mt-2">{p.description}</div></div>)}
      {list.length===0&&<div className="text-gray-400">No projects</div>}
    </div>
  </div>
}
