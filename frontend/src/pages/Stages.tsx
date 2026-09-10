import { useEffect, useState } from 'react'
import client from '../api/client'
export default function Stages(){
  const [stages,setStages]=useState<any[]>([])
  useEffect(()=>{client.get('/api/v1/stages/').then(r=>setStages(r.data.results||r.data.data||[]))},[])
  return <div>
    <h1 className="text-2xl font-bold">Workflow Stages (18 steps)</h1>
    <div className="bg-white rounded-xl border mt-6">
      {stages.map((s:any,i:number)=><div key={s.id} className="flex gap-4 p-4 border-b last:border-0">
        <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm">{s.order||i+1}</div>
        <div><div className="font-medium">{s.name}</div><div className="text-xs text-gray-500">{s.slug} • {s.is_required?'Required':'Optional'}</div></div>
        <div className="ml-auto text-xs text-gray-400">{s.due_date||''}</div>
      </div>)}
      {stages.length===0&&<div className="p-8 text-center text-gray-400">No stages configured</div>}
    </div>
  </div>
}
