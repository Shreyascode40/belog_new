import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function FinalLogbook(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [data,setData]=useState<any>(null)
  const [error,setError]=useState('')
  const [generating,setGenerating]=useState(false)
  const load=async()=>{
    setLoading(true)
    try{const r=await client.get('/api/v1/student/final-logbook/');setData(r.data.data)}catch(e:any){setError(e.response?.data?.message||'Failed')}
    setLoading(false)
  }
  useEffect(()=>{load()},[tick])
  const generate=async()=>{
    setGenerating(true)
    try{const r=await client.post('/api/v1/student/final-logbook/generate/'); setData({...data, latest:r.data.data, can_generate:true}); alert('PDF generated v'+r.data.data.version)}catch(e:any){alert(e.response?.data?.message||'Generate failed: '+JSON.stringify(e.response?.data?.errors))}
    setGenerating(false); load()
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading final log book...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  const c=data.checklist||{}
  const items=[
    ['Group Information',c.group_information],
    ['Student Information',c.student_information],
    ['Project Information',c.project_information],
    ['Log Entries',c.log_entries],
    ['Faculty Verification',c.faculty_verification],
    ['Reviewer Verification',c.reviewer_verification],
    ['Required Documents',c.required_documents],
    ['Progress Information',c.progress_information],
    ['Final Review',c.final_review],
  ]
  return <div className="max-w-3xl mx-auto">
    <h1 className="text-xl font-bold">Final Log Book</h1>
    <div className="bg-white border rounded-xl p-6 mt-4">
      <h3 className="font-semibold text-sm">Completion Checklist</h3>
      <div className="mt-3 space-y-2">
        {items.map(([label,done]:any)=><div key={label} className="flex gap-2 text-sm"><span>{done?'✓':'○'}</span><span className={done?'text-green-700':'text-gray-500'}>{label}</span></div>)}
      </div>
      {data.errors && Object.keys(data.errors).length>0 && <div className="mt-4 bg-red-50 border border-red-200 p-3 rounded text-xs text-red-700">{JSON.stringify(data.errors)}</div>}
      <div className="mt-6 flex gap-2">
        <button disabled={!data.can_generate || generating} onClick={generate} className={`px-5 py-2 rounded text-sm ${data.can_generate?'bg-blue-600 text-white':'bg-gray-200 text-gray-500'}`}>{generating?'Generating...':'Generate PDF'}</button>
        {data.latest?.pdf_path && <a href={`http://localhost:8000/media/${data.latest.pdf_path}`} target="_blank" className="border px-5 py-2 rounded text-sm">Download v{data.latest.version}</a>}
      </div>
      {!data.can_generate && <div className="text-xs text-amber-600 mt-2">Complete all required conditions before generating.</div>}
      {data.latest && <div className="text-xs text-gray-500 mt-3">Latest: v{data.latest.version} — {data.latest.status} — {data.latest.generated_at? new Date(data.latest.generated_at).toLocaleString():''}</div>}
    </div>
  </div>
}