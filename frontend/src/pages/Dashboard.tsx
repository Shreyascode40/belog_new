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
        <div className="grid grid-cols-2 gap-3">
          <a href="/profile" className="bg-teal-600 text-white p-3 rounded-xl text-center font-semibold">✏️ Edit My Info<br/><span className="text-xs font-normal">My Profile — Name/Roll/Mobile/Seat/Email/Photo</span></a>
          <a href="/student-info" className="bg-green-600 text-white p-3 rounded-xl text-center font-semibold">👥 Fill Group's 4 Members<br/><span className="text-xs font-normal">Student Section — all 4, different fields, Photo preview</span></a>
        </div>
        <div className="text-xs text-gray-500 text-center mt-3">Not filled → NOT_STARTED. Save Draft — you can finish later (Journey stays DRAFT). Save & Continue → Go to Student Info — clearer</div>
      </div>
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
        <div className="flex justify-between items-center mb-3">
          <div className="text-sm font-bold">Journey — Your Project Progress</div>
          <div className="text-xs text-gray-500">{level.levels.filter((x:any)=>['APPROVED','LOCKED'].includes(x.status)).length} / {level.levels.length} completed</div>
        </div>
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
          <div className="flex flex-col gap-3">
            {level.levels.map((l:any, idx:number)=>{
              const prev = idx>0 ? level.levels[idx-1] : null
              const prevDone = !prev || ['APPROVED','LOCKED'].includes(prev.status)
              const isClickable = prevDone || l.order===level.current_level_order || l.order<level.current_level_order
              const isCurrent = l.order===level.current_level_order
              const isDone = ['APPROVED','LOCKED'].includes(l.status)
              const isLocked = !isClickable
              return <div key={l.order} onClick={()=>isClickable && openLevel(l, idx)} className={`relative flex gap-4 p-4 rounded-xl border ${isLocked?'opacity-50 cursor-not-allowed bg-gray-50': 'cursor-pointer hover:shadow-md bg-white'} ${isCurrent?'border-blue-500 ring-2 ring-blue-100': isDone?'border-green-300 bg-green-50':''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${isDone?'bg-green-600 text-white': isCurrent?'bg-blue-600 text-white': isLocked?'bg-gray-300 text-gray-600':'bg-slate-800 text-white'}`}>
                  {isDone?'✓': isLocked?'🔒': l.order}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <div className="font-semibold text-sm">Level {l.order} — {l.name}</div>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${l.status==='APPROVED'?'bg-green-100 text-green-700': l.status==='LOCKED'?'bg-slate-800 text-white': l.status==='SUBMITTED'?'bg-yellow-100 text-yellow-700': l.status==='UNDER_REVIEW'?'bg-blue-100 text-blue-700': l.status==='CHANGES_REQUIRED'?'bg-red-100 text-red-700':'bg-gray-200 text-gray-600'}`}>{l.status}</span>
                  </div>
                  <div className="text-xs text-gray-500 truncate">{l.slug} • {l.granted?'Access Granted': l.order===1 && !l.granted && l.status==='APPROVED'?'Waiting for guide grant':''}</div>
                  {isCurrent && <div className="text-xs mt-1 text-blue-600 font-medium">→ Current: {level.next_action_label}</div>}
                  {isDone && <div className="text-xs mt-1 text-green-600">✓ Completed — click to view</div>}
                  {isLocked && <div className="text-xs mt-1 text-gray-400">🔒 Locked — complete "{prev?.name}" first</div>}
                  {isClickable && !isLocked && <div className="text-xs mt-2 text-blue-600 underline">Open to fill next info →</div>}
                </div>
              </div>
            })}
          </div>
        </div>
        {levelMsg&&<div className="text-xs mt-3 p-3 bg-amber-50 text-amber-700 rounded border border-amber-200">{levelMsg}</div>}
        <div className="text-xs text-gray-400 mt-3">System: Previous level must be APPROVED/LOCKED. Click any unlocked (white/blue/green) level to fill. Grey locked levels are blocked server-side (403).</div>
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
    <p className="text-xs text-gray-500">System to evaluate all levels activity properly — every stage is reviewed, not just Level 0.</p>
    <div className="grid grid-cols-3 gap-4 mt-6">
      <Card title="Assigned Groups" value={data.assigned_groups??queue.length}/>
      <Card title="Awaiting Action" value={queue.filter((q:any)=>q.needs_data_approval||q.needs_access_grant).length}/>
      <Card title="Access Gates" value={queue.filter((q:any)=>q.needs_access_grant).length}/>
    </div>
    {grantMsg&&<div className="mt-4 text-sm text-green-600">{grantMsg}</div>}
    <div className="mt-6 bg-white p-4 rounded-xl border">
      <h2 className="font-semibold">Groups awaiting your action (All Levels)</h2>
      <p className="text-xs text-gray-500">Proper evaluation: each level shows submission, status, and actions for every assigned group. Click "Evaluate All Levels" to open detailed per-level review.</p>
      <div className="mt-3">
        {queue.map((q:any)=><div key={q.group_id} className="border rounded p-3 mb-2 bg-gray-50">
          <div className="flex justify-between items-center">
            <div><span className="font-medium">Group {q.group_number}</span> — Level {q.level.current_level_order} {q.level.current_level_name} <span className={`ml-2 text-xs px-2 py-0.5 rounded ${q.level.current_level_status==='SUBMITTED'?'bg-yellow-100': q.level.current_level_status==='APPROVED'?'bg-green-100':'bg-gray-200'}`}>{q.level.current_level_status}</span></div>
            <a href="/faculty/evaluate" className="bg-blue-600 text-white px-3 py-1 rounded text-xs">Evaluate All Levels →</a>
          </div>
          <div className="text-xs text-gray-500 mt-1">Needs: {q.needs_data_approval?'Data approval':''} {q.needs_data_approval && q.needs_access_grant ? ' • ' : ''} {q.needs_access_grant?'Access grant':''} {!q.needs_data_approval && !q.needs_access_grant?'No pending — view all levels anyway':''}</div>
        </div>)}
        {queue.length===0&&<div className="text-xs text-gray-400 py-2">No assigned groups — HOD must allocate via HOD → Allocate Guide/Reviewer</div>}
      </div>
    </div>
    <div className="bg-blue-50 p-4 rounded-xl border mt-6">
      <h2 className="font-semibold text-sm">Evaluate All Levels Activity</h2>
      <p className="text-xs text-gray-600">Faculty/Reviewer must evaluate <b>every</b> level: Information → Schedule & Topic → Activity → Requirement/Cost → Review-1 → Design → Review-2 → Development → Testing → Review-3 → Competition/Publication → Term → Final. Each level has Approve / Request Changes / Lock + per-criterion marks.</p>
      <a href="/faculty/evaluate" className="mt-3 inline-block bg-slate-900 text-white px-6 py-2 rounded text-sm">Open Evaluation Workspace →</a>
    </div>
  </div>
}
