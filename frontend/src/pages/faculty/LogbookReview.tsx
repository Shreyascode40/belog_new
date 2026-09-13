import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import client from '../../api/client'

export default function LogbookReview({role}:{role:'faculty'|'reviewer'}){
  const tick=useRealtimeTick()
  const {id}=useParams()
  const nav=useNavigate()
  const [data,setData]=useState<any>(null)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [decision,setDecision]=useState('approved')
  const [feedback,setFeedback]=useState('')
  const [submitting,setSubmitting]=useState(false)
  const load=async()=>{
    setLoading(true)
    try{
      const r=await client.get(`/api/v1/${role}/logbook/${id}/`)
      setData(r.data.data)
    }catch(e:any){setError(e.response?.data?.message|| e.response?.data?.errors?.detail|| 'Failed to load')}
    setLoading(false)
  }
  useEffect(()=>{load()},[id, role, tick])
  const submit=async()=>{
    if(decision==='changes_required' && !feedback.trim()){ setError('Feedback required for changes requested'); return}
    setSubmitting(true);setError('')
    try{
      await client.post(`/api/v1/${role}/logbook/${id}/review/`, {decision, feedback})
      alert('Review submitted')
      nav(`/${role}/logbook`)
    }catch(e:any){setError(e.response?.data?.message|| JSON.stringify(e.response?.data?.errors)||'Submit failed')}
    setSubmitting(false)
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading entry...</div>
  if(error && !data) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error} <Link to={`/${role}/logbook`} className="underline ml-2">Back</Link></div>
  const canReview=['submitted','resubmitted','under_review'].includes(data.status)
  return <div className="max-w-4xl mx-auto">
    <Link to={`/${role}/logbook`} className="text-sm text-blue-600 underline">← Back to Log Book</Link>
    <div className="bg-white border rounded-xl p-6 mt-4">
      <div className="flex justify-between">
        <div>
          <h1 className="text-lg font-bold">G-{data.group_detail?.group_number||data.group} — Week {data.content?.week||'-'}</h1>
          <div className="text-xs text-gray-500">{data.content?.date||''} • {data.section?.title||''} • {data.status} • v{data.version}</div>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-gray-100 h-fit">{data.status}</span>
      </div>

      <div className="mt-6 space-y-4 text-sm">
        <div><div className="text-xs text-gray-400">Group / Students</div><div>{data.group_detail?.members?.map((m:any)=>m.student_detail?.name).join(', ')||''}</div></div>
        <div><div className="text-xs text-gray-400">Work Completed</div><div className="whitespace-pre-wrap bg-gray-50 p-3 rounded">{data.content?.work_completed||'-'}</div></div>
        <div><div className="text-xs text-gray-400">Planned Work</div><div className="whitespace-pre-wrap">{data.content?.work_planned||'-'}</div></div>
        <div className="grid grid-cols-2 gap-4">
          <div><div className="text-xs text-gray-400">Problems</div><div>{data.content?.problems||'-'}</div></div>
          <div><div className="text-xs text-gray-400">Solutions</div><div>{data.content?.solution||'-'}</div></div>
        </div>
        <div><div className="text-xs text-gray-400">Learning / Outcomes</div><div>{data.content?.learning||'-'}</div></div>
        {data.content?.evidence_files && <div><div className="text-xs text-gray-400">Attachments</div><div className="text-xs">{data.content.evidence_files.join(', ')}</div></div>}
        {data.review_remarks && <div className="bg-amber-50 border p-3 rounded text-xs"><div className="font-semibold">Previous feedback:</div>{data.review_remarks}</div>}
      </div>

      {data.versions?.length>0 && <div className="mt-6 border-t pt-4">
        <h3 className="text-xs font-semibold">Submission History</h3>
        {data.versions.map((v:any)=><div key={v.id} className="text-xs bg-gray-50 p-2 rounded mt-2">v{v.version_number} — {new Date(v.submitted_at).toLocaleDateString()} — {v.review_remark||''}</div>)}
      </div>}

      {canReview ? <div className="mt-6 border-t pt-6">
        <h3 className="font-semibold text-sm">Review Decision</h3>
        <div className="mt-3 flex gap-2">
          {[
            ['approved','APPROVE'],
            ['changes_required','CHANGES REQUESTED'],
            ['rejected','REJECT'],
          ].map(([val,label])=><label key={val} className={`px-4 py-2 rounded border text-xs cursor-pointer ${decision===val?'bg-blue-600 text-white border-blue-600':'bg-white'}`}><input type="radio" name="decision" value={val} checked={decision===val} onChange={e=>setDecision(e.target.value)} className="mr-2"/>{label}</label>)}
        </div>
        <label className="text-xs font-medium mt-4 block">Feedback {decision==='changes_required' && <span className="text-red-600">*</span>}<textarea value={feedback} onChange={e=>setFeedback(e.target.value)} rows={4} className="mt-1 w-full border rounded p-2 text-sm" placeholder={decision==='changes_required'?'Please provide additional details about the testing methodology...':'General/technical feedback...'}/></label>
        {error && <div className="text-sm text-red-600 bg-red-50 border p-2 rounded mt-3">{error}</div>}
        <div className="flex gap-2 mt-4">
          <button onClick={submit} disabled={submitting} className="bg-blue-600 text-white px-6 py-2 rounded text-sm disabled:opacity-50">{submitting?'Submitting...':'Submit Review'}</button>
          <Link to={`/${role}/logbook`} className="border px-6 py-2 rounded text-sm">Cancel</Link>
        </div>
      </div> : <div className="mt-6 bg-gray-50 border p-4 rounded text-sm text-gray-500 text-center">This entry is in <b>{data.status}</b> — cannot review a draft or already decided entry. Workflow: DRAFT → SUBMITTED → REVIEW → APPROVED / CHANGES_REQUESTED → RESUBMIT → REVIEW.</div>}
    </div>
  </div>
}