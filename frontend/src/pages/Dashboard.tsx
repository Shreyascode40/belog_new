import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import Card from '../components/Card'
export default function Dashboard(){
  const role=localStorage.getItem('role')
  const nav = useNavigate()
  const [data,setData]=useState<any>({})
  const [level,setLevel]=useState<any>(null)
  const [queue,setQueue]=useState<any[]>([])
  const [grantMsg,setGrantMsg]=useState('')
  const [hasGroup,setHasGroup]=useState<boolean | null>(null)
  const [invites,setInvites]=useState<any[]>([])
  const [seedMsg,setSeedMsg]=useState('')
  const [levelMsg,setLevelMsg]=useState('')
  const seedStudent=async()=>{
    const gid = (level?.group_id) || (data.my_group?.[0]?.id || data.my_group?.id)
    if(!gid){ setSeedMsg('No group found'); return }
    try{ const r=await client.post(`/api/v1/groups/${gid}/seed-student/`); setSeedMsg(r.data.message); client.get(`/api/v1/groups/${gid}/level/`).then(res=>setLevel(res.data.data)) }catch(e:any){ setSeedMsg(e.response?.data?.message||'Seed failed') }
  }
  const openLevel=async(l:any, idx:number)=>{
    const levels = level?.levels || []
    const prev = idx>0 ? levels[idx-1] : null
    const prevDone = !prev || ['APPROVED','LOCKED'].includes(prev.status)
    if(!prevDone){
      setLevelMsg(`Level ${l.order} locked — complete "${prev?.name}" (${prev?.status}) first`)
      setTimeout(()=>setLevelMsg(''), 3000)
      return
    }
    nav(`/level/${l.id}`)
  }
  useEffect(()=>{
    const ep=role==='hod'?'/api/v1/dashboard/hod/':role==='student'?'/api/v1/dashboard/student/':'/api/v1/dashboard/faculty/'
    client.get(ep).then(r=>setData(r.data.data)).catch(()=>{})
    if(role==='student'){
      client.get('/api/v1/groups/').then(r=>{
        const list=(r.data.results||r.data.data||[])
        if(list.length===0){ setHasGroup(false); setLevel(null) }
        else { setHasGroup(true); const g=list[0]; client.get(`/api/v1/groups/${g.id}/level/`).then(res=>setLevel(res.data.data)).catch(()=>{}) }
      }).catch(()=>setHasGroup(false))
      client.get('/api/v1/groups/my-invites/').then(r=>setInvites(r.data.data||[])).catch(()=>{})
    }
    if(role==='faculty'||role==='reviewer'||role==='hod'){
      client.get('/api/v1/guide/queue/').then(r=>setQueue(r.data.data||[])).catch(()=>{})
    }
  },[])
  const [logbook,setLogbook]=useState<any>(null)
  const [hodMsg,setHodMsg]=useState('')
  const grantAccess=async(gid:number,sid:number,grant:boolean)=>{
    await client.post(`/api/v1/groups/${gid}/stages/${sid}/access-grant/`,{granted:grant})
    setGrantMsg(grant?'Access granted':'Access revoked')
    client.get('/api/v1/guide/queue/').then(r=>setQueue(r.data.data||[]))
  }
  const checkLogbook=async(gid:number)=>{
    const r=await client.get(`/api/v1/groups/${gid}/logbook/status/`)
    setLogbook(r.data.data)
  }
  const hodApprove=async(gid:number)=>{
    await client.post(`/api/v1/groups/${gid}/hod-final-approval/`,{approved:true})
    setHodMsg('HOD approval granted')
    checkLogbook(gid)
  }
  const generateLogbook=async(gid:number)=>{
    try{ const r=await client.post(`/api/v1/groups/${gid}/logbook/generate/`); setLogbook({can_generate:true, latest:r.data.data}); setHodMsg('PDF generated v'+r.data.data.version)}catch(e:any){ setHodMsg(e.response?.data?.errors? JSON.stringify(e.response.data.errors): e.response?.data?.message)}
  }
  if(role==='hod') return <div>
    <h1 className="text-2xl font-bold">HOD Dashboard</h1>
    <div className="grid grid-cols-4 gap-4 mt-6">
      <Card title="Total Groups" value={data.total_groups??'-'}/>
      <Card title="Completed" value={data.completed??'-'}/>
      <Card title="In Progress" value={data.in_progress??'-'}/>
      <Card title="Overdue" value={data.overdue??'-'}/>
    </div>
    <div className="mt-6 bg-white p-4 rounded-xl border">
      <h2 className="font-semibold">Access Grants</h2>
      <p className="text-xs text-gray-500">HOD can view/grant for any group. Use queue below.</p>
      {queue.map((q:any)=><div key={q.group_id} className="flex justify-between items-center border-t py-2 text-sm mt-2">
        <span>Group {q.group_number} — Level {q.level.current_level_order} {q.level.current_level_name} ({q.level.current_level_status})</span>
        <span className="flex gap-2">
          {q.needs_access_grant&&<button onClick={()=>grantAccess(q.group_id,q.level.stage_id,true)} className="bg-green-600 text-white px-3 py-1 rounded">Grant Access</button>}
          {!q.needs_access_grant&&q.level.current_level_order===1&&<button onClick={()=>grantAccess(q.group_id,q.level.stage_id,false)} className="bg-red-600 text-white px-3 py-1 rounded">Revoke</button>}
        </span>
      </div>)}
    </div>
    <div className="mt-6 bg-white p-4 rounded-xl border">
      <h2 className="font-semibold">Final Log Book — HOD Gate</h2>
      <p className="text-xs text-gray-500">Generate is blocked until all required stages LOCKED, reviews FINALIZED, and HOD approval granted. PDF replicates official Record No. ACA/D/003B exactly.</p>
      {queue.map((q:any)=><div key={'log'+q.group_id} className="border-t py-3 mt-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Group {q.group_number}</span>
          <span className="flex gap-2">
            <button onClick={()=>checkLogbook(q.group_id)} className="border px-3 py-1 rounded text-xs">Check Status</button>
            <button onClick={()=>hodApprove(q.group_id)} className="bg-slate-800 text-white px-3 py-1 rounded text-xs">HOD Approve</button>
            <button onClick={()=>generateLogbook(q.group_id)} className="bg-blue-600 text-white px-3 py-1 rounded text-xs">Generate PDF</button>
          </span>
        </div>
        {logbook&&<div className="text-xs mt-2 p-2 bg-gray-50 rounded">
          Can generate: {String(logbook.can_generate)} {logbook.errors&&Object.keys(logbook.errors).length>0&&<span className="text-red-600"> — {JSON.stringify(logbook.errors)}</span>}
          {logbook.latest&&<span> — Latest v{logbook.latest.version} {logbook.latest.status} <a href={`http://localhost:8000/media/${logbook.latest.pdf_path}`} target="_blank" className="text-blue-600 underline">Download</a></span>}
        </div>}
      </div>)}
      {hodMsg&&<div className="text-sm text-blue-600 mt-2">{hodMsg}</div>}
    </div>
  </div>
  if(role==='student'){
    if(hasGroup===false){
      const acceptInvite=async(gid:number)=>{
        await client.post(`/api/v1/groups/${gid}/accept-invite/`); location.reload()
      }
      const declineInvite=async(gid:number)=>{
        await client.post(`/api/v1/groups/${gid}/decline-invite/`); setInvites(invites.filter((x:any)=>x.group!==gid))
      }
      return <div>
        <h1 className="text-2xl font-bold">Student Dashboard</h1>
        <div className="bg-white p-8 rounded-xl border mt-6">
          <div className="text-lg font-semibold text-center">You're not part of a project group yet.</div>
          <p className="text-sm text-gray-500 mt-2 text-center">Flow: Register → Cover Page → Student Section (fill all 4 members) → Other levels unlock</p>
          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="border rounded-xl p-4 bg-blue-50">
              <div className="font-semibold text-sm">1. Cover Page</div>
              <p className="text-xs text-gray-600 mt-1">Group No. auto-assigned, Project Title (2-line), Area, Guide Pending. Mirrors official Cover.</p>
              <a href="/cover" className="mt-3 inline-block bg-blue-600 text-white px-4 py-2 rounded text-sm w-full text-center">Go to Cover Page →</a>
            </div>
            <div className="border rounded-xl p-4 bg-green-50">
              <div className="font-semibold text-sm">2. Student Section</div>
              <p className="text-xs text-gray-600 mt-1">Separate section — fill all 4 members: Name, Roll, Mobile, Seat, Email, TE Result, Contribution, Photo. Auto-fetched from registration if project title given but member blank. Undertaking each member acknowledges individually.</p>
              <a href="/student-info" className="mt-3 inline-block bg-green-600 text-white px-4 py-2 rounded text-sm w-full text-center">Go to Student Info →</a>
            </div>
          </div>
          <div className="text-xs text-gray-500 mt-3 text-center">Member Info and Undertaking are separate sections — not in sidebar. Other levels remain locked until Student Section submitted and guide grants AccessGrant.</div>
          <div className="flex justify-center gap-4 mt-4">
            <a href="/create-group" className="text-xs text-gray-500 underline">Or use combined Create Group wizard</a>
            <a href="/groups" className="text-xs text-gray-500 underline">View Groups</a>
          </div>
        </div>
        {invites.length>0 && <div className="bg-white p-4 rounded-xl border mt-6">
          <h2 className="font-semibold">Pending Invites</h2>
          {invites.map((inv:any)=><div key={inv.id} className="flex justify-between items-center py-2 border-b text-sm">
            <span>Group {inv.group} — {inv.role} — {inv.status}</span>
            <span className="flex gap-2">
              <button onClick={()=>acceptInvite(inv.group)} className="bg-green-600 text-white px-3 py-1 rounded">Accept</button>
              <button onClick={()=>declineInvite(inv.group)} className="border px-3 py-1 rounded">Decline</button>
            </span>
          </div>)}
        </div>}
        <div className="bg-amber-50 p-3 rounded mt-6 text-xs text-amber-800">No other group's data visible — other levels lock open only after Student Section is submitted and approved.</div>
      </div>
    }
    const badge = level ? `Level ${level.current_level_order} — ${level.current_level_name} (${level.current_level_status})` : 'Loading...'
    const cta = level?.next_action_label || ''
    return <div>
      <h1 className="text-2xl font-bold">Student Dashboard</h1>
      <div className="bg-white p-4 rounded-xl border mt-6">
        <div className="flex justify-between items-center">
          <div className="text-sm font-semibold">Current Level</div>
          <button onClick={seedStudent} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs">Seed All Info (Sample)</button>
        </div>
        <div className="mt-2 inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">{badge}</div>
        <div className={`mt-3 text-sm ${!level?.is_access_granted && level?.current_level_status==='APPROVED' ? 'text-amber-600 font-medium' : 'text-gray-600'}`}>{cta}</div>
        {!level?.is_access_granted && level?.current_level_order===1 && <div className="mt-2 text-xs text-amber-700 bg-amber-50 p-2 rounded">Your information has been approved. Waiting for your guide to grant access to the next stage.</div>}
        {level?.current_level_status==='CHANGES_REQUIRED' && <div className="mt-2 text-xs text-red-600">Guide requested changes — please edit & resubmit.</div>}
        {seedMsg&&<div className="text-xs text-green-600 mt-2">{seedMsg} — fills all 18 stages (Group/Student info, schedule, topics, activities, RTM, cost, reviews prep, development, testing, competition, terms) as DRAFT for you to then Submit.</div>}
        <div className="text-xs text-gray-400 mt-2">Fills every logbook section from student side — member contacts (roll/mobile/seat/email), project title/area, undertakings etc. Guide/HOD still approves & grants next level.</div>
      </div>
      {level?.levels && <div className="mt-6 bg-white p-4 rounded-xl border">
        <div className="text-sm font-semibold mb-3">Journey — click to open level (only if previous complete)</div>
        <div className="flex gap-2 overflow-x-auto">
          {level.levels.map((l:any, idx:number)=>{
            const prev = idx>0 ? level.levels[idx-1] : null
            const prevDone = !prev || ['APPROVED','LOCKED'].includes(prev.status)
            const isClickable = prevDone || l.order===level.current_level_order || l.order<level.current_level_order
            return <div key={l.order} onClick={()=>openLevel(l, idx)} className={`min-w-[120px] p-3 rounded border text-xs ${!isClickable?'opacity-40 cursor-not-allowed': 'cursor-pointer hover:shadow'} ${l.order===level.current_level_order?'bg-blue-600 text-white': l.order<level.current_level_order?'bg-green-50 border-green-200':'bg-gray-50'}`}>
            <div className="font-semibold">{l.order===0?'✓': l.order<level.current_level_order?'✓': !isClickable?'🔒':'→'} Level {l.order} {isClickable?'':'🔒'}</div>
            <div className="truncate">{l.name}</div>
            <div className="opacity-70">{l.status}</div>
            {isClickable && <div className="text-xs mt-1 underline">Open →</div>}
          </div>})}
        </div>
        {levelMsg&&<div className="text-xs mt-2 p-2 bg-amber-50 text-amber-700 rounded">{levelMsg}</div>}
        <div className="text-xs text-gray-400 mt-2">Previous level must be APPROVED/LOCKED — backend enforces 403 otherwise. Click any unlocked level to open its endpoint.</div>
      </div>}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <Card title="My Group" value={data.my_group?.[0]?.group_number||data.my_group?.group_number||'-'}/>
        <Card title="Progress" value={`${data.progress||0}%`}/>
        <Card title="Next Action" value={cta.slice(0,20)}/>
      </div>
      {invites.length>0 && <div className="bg-white p-4 rounded-xl border mt-6">
        <h2 className="text-sm font-semibold">Pending Invites</h2>
        {invites.map((inv:any)=><div key={inv.id} className="flex justify-between py-2 text-sm"><span>Group {inv.group}</span><button onClick={async()=>{await client.post(`/api/v1/groups/${inv.group}/accept-invite/`); location.reload()}} className="bg-green-600 text-white px-3 py-1 rounded">Accept</button></div>)}
      </div>}
    </div>
  }
  return <div>
    <h1 className="text-2xl font-bold">Guide / Reviewer Dashboard</h1>
    <div className="grid grid-cols-3 gap-4 mt-6">
      <Card title="Assigned Groups" value={data.assigned_groups??queue.length}/>
      <Card title="Awaiting Action" value={queue.filter((q:any)=>q.needs_data_approval||q.needs_access_grant).length}/>
      <Card title="Access Gates" value={queue.filter((q:any)=>q.needs_access_grant).length}/>
    </div>
    {grantMsg&&<div className="mt-4 text-sm text-green-600">{grantMsg}</div>}
    <div className="mt-6 bg-white p-4 rounded-xl border">
      <h2 className="font-semibold">Groups awaiting your action</h2>
      <div className="mt-2">
        <div className="text-xs font-semibold text-gray-500">Data to approve</div>
        {queue.filter((q:any)=>q.needs_data_approval).map((q:any)=><div key={'d'+q.group_id} className="flex justify-between py-2 border-b text-sm"><span>Group {q.group_number} — {q.level.current_level_name}</span><span className="text-amber-600">Submitted</span></div>)}
        {queue.filter((q:any)=>q.needs_data_approval).length===0&&<div className="text-xs text-gray-400 py-2">None</div>}
        <div className="text-xs font-semibold text-gray-500 mt-4">Access to grant</div>
        {queue.filter((q:any)=>q.needs_access_grant).map((q:any)=><div key={'a'+q.group_id} className="flex justify-between items-center py-2 border-b text-sm"><span>Group {q.group_number} — Information APPROVED</span><button onClick={()=>grantAccess(q.group_id,q.level.stage_id,true)} className="bg-green-600 text-white px-3 py-1 rounded text-xs">Grant Access</button></div>)}
        {queue.filter((q:any)=>q.needs_access_grant).length===0&&<div className="text-xs text-gray-400 py-2">None</div>}
      </div>
      <div className="mt-4 text-xs text-gray-500">Approve Data and Grant Access are separate actions. Both needed to unlock Level 1.</div>
    </div>
  </div>
}
