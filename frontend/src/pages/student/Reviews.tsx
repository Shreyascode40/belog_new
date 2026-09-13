import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Reviews(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState<any>(null)
  useEffect(()=>{
    client.get('/api/v1/student/reviews/').then(r=>setData(r.data.data)).catch(e=>setError('Unable to load reviews')).finally(()=>setLoading(false))
  },[tick])
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading reviews...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-4xl mx-auto">
    <h1 className="text-xl font-bold">Reviews & Feedback</h1>
    <div className="mt-4 space-y-4">
      {data.reviews?.length ? data.reviews.map((r:any)=><div key={r.id} className="bg-white border rounded-xl p-5">
        <div className="flex justify-between"><span className="font-medium text-sm">Review {r.review_number} — {r.status}</span><span className="text-xs text-gray-500">{r.review_date}</span></div>
        <div className="text-xs text-gray-500 mt-1">Reviewer: {r.reviewer||'-'}</div>
        {r.status==='finalized' ? <>
          <div className="mt-3 text-sm">Marks: {r.total_obtained}/{r.total_max} — {r.overall_remarks||''}</div>
          {r.marks?.length>0 && <table className="w-full text-xs mt-2 border"><thead><tr className="bg-gray-50"><th className="p-2 text-left">Criterion</th><th className="p-2">Obtained</th></tr></thead><tbody>{r.marks.map((m:any)=><tr key={m.id} className="border-t"><td className="p-2">{m.criterion}</td><td className="p-2 text-center">{m.obtained_marks}</td></tr>)}</tbody></table>}
        </> : <div className="text-xs bg-amber-50 p-3 rounded mt-3">Marks not yet released</div>}
        <div className="text-xs text-gray-500 mt-2">{r.overall_remarks||'No remarks'}</div>
      </div>) : <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-400">No reviews yet</div>}
      {data.feedbacks?.length>0 && <div className="bg-white border rounded-xl p-5">
        <h3 className="font-semibold text-sm">Submission Feedback</h3>
        {data.feedbacks.map((f:any,i:number)=><div key={i} className="border-t py-2 text-sm"><span className="font-medium">{f.stage}</span> — {f.status} <span className="text-xs text-gray-500">{f.comment}</span></div>)}
      </div>}
      {data.total?.max>0 && <div className="bg-white border rounded-xl p-5 text-sm font-medium">Total: {data.total.obtained} / {data.total.max}</div>}
    </div>
  </div>
}