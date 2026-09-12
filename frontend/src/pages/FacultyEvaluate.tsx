import { useEffect, useState } from 'react'
import client from '../api/client'

type Level = {id:number, order:number, name:string, slug:string, status:string, granted:boolean}
type GroupQueue = {group_id:number, group_number:string, level:{current_level_order:number, current_level_name:string, current_level_status:string}}

export default function FacultyEvaluate(){
  const [groups,setGroups]=useState<GroupQueue[]>([])
  const [selected,setSelected]=useState<GroupQueue|null>(null)
  const [levels,setLevels]=useState<Level[]>([])
  const [subs,setSubs]=useState<any[]>([])
  const [criteriaMap,setCriteriaMap]=useState<Record<number, any[]>>({})
  const [msg,setMsg]=useState('')
  const [saving,setSaving]=useState<number|null>(null)

  const loadGroups=async()=>{
    const r=await client.get('/api/v1/guide/queue/')
    setGroups(r.data.data||[])
  }
  useEffect(()=>{ loadGroups() },[])

  const openGroup=async(g:GroupQueue)=>{
    setSelected(g)
    setMsg('')
    const [lvlRes, subRes]=await Promise.all([
      client.get(`/api/v1/groups/${g.group_id}/level/`),
      client.get(`/api/v1/submissions/?group=${g.group_id}`)
    ])
    setLevels(lvlRes.data.data.levels||[])
    const list=subRes.data.results||subRes.data||[]
    setSubs(list)
    // load criteria for each review level
    const map:Record<number, any[]>={}
    for(const lvl of (lvlRes.data.data.levels||[])){
      if(lvl.slug.includes('review') || lvl.name.toLowerCase().includes('review')){
        try{
          const cr=await client.get(`/api/v1/criteria/?review__group=${g.group_id}&review__review_number=${lvl.order}`)
          // fallback to criteria by review id
          const byLvl=await client.get(`/api/v1/criteria/?review=${lvl.id}`)
          const arr=(byLvl.data.results||byLvl.data||[])
          if(arr.length>0) map[lvl.id]=arr
        }catch{}
        // also try fetch reviews then criteria
        try{
          const revRes=await client.get(`/api/v1/reviews/?group=${g.group_id}`)
          const revs=(revRes.data.results||revRes.data||[])
          for(const rev of revs){
            const cRes=await client.get(`/api/v1/criteria/?review=${rev.id}`)
            const cs=cRes.data.results||cRes.data||[]
            if(cs.length>0) map[rev.id]=cs
          }
        }catch{}
      }
    }
    setCriteriaMap(map)
  }

  const findSubForLevel=(lvl:Level)=>{
    // match submission whose section's stage id equals lvl.id
    // submissions store section id, need to match via level's stage
    // since we don't have section->stage mapping here, use status from level as fallback and find any sub for that group
    // try direct match by checking sub.section's stage via separate fetch would be heavy, so we match by level order's submission status
    // For now, find first submission where level status != NOT_STARTED and order matches current
    return subs.find((s:any)=> s.section && levels.find(l=>l.id===s.section)?.order===lvl.order) || subs.find((s:any)=> lvl.status!=='NOT_STARTED' && s.id) || null
  }

  const doAction=async(sub:any, action:'approve'|'changes'|'lock')=>{
    if(!sub || sub.id==='—'){ setMsg('No submission to act on — student has not submitted this level yet'); return }
    try{
      if(action==='approve') await client.post(`/api/v1/submissions/${sub.id}/approve/`)
      if(action==='changes'){
        const remark=prompt('Why changes required? This remark will be shown to student:')
        if(!remark) return
        await client.post(`/api/v1/submissions/${sub.id}/request_changes/`, {remarks: remark})
      }
      if(action==='lock') await client.post(`/api/v1/submissions/${sub.id}/lock/`)
      setMsg(`✓ Level submission ${action} successful — student will see updated status`)
      if(selected) openGroup(selected)
    }catch(e:any){ setMsg(e.response?.data?.message||e.response?.data?.errors?.access?.[0]||e.response?.data?.errors?.level?.[0]||'Action failed — maybe already locked or previous level not complete') }
  }

  const saveMark=async(criterion:any, groupId:number, obtained:string, remark:string)=>{
    if(!criterion) return
    const val=parseFloat(obtained)
    if(isNaN(val)){ setMsg('Enter a valid number for obtained marks'); return }
    if(val<0){ setMsg('Marks cannot be negative'); return }
    if(val>parseFloat(criterion.max_marks)){ setMsg(`Cannot exceed max ${criterion.max_marks}`); return }
    setSaving(criterion.id)
    try{
      const existing=await client.get(`/api/v1/marks/?criterion=${criterion.id}&group=${groupId}`)
      const list=existing.data.results||existing.data||[]
      if(list.length>0){
        await client.patch(`/api/v1/marks/${list[0].id}/`, {obtained_marks: val, remarks: remark, status:'saved'})
      } else {
        const tokenPayload=JSON.parse(atob(localStorage.getItem('access')!.split('.')[1]))
        await client.post('/api/v1/marks/', {criterion: criterion.id, group: groupId, reviewer: tokenPayload.user_id || 1, obtained_marks: val, remarks: remark, status:'saved'})
      }
      setMsg(`✓ Saved ${criterion.name}: ${val}/${criterion.max_marks}`)
    }catch(e:any){ setMsg(e.response?.data?.errors?.obtained_marks?.[0]||e.response?.data?.message||'Save failed') }
    setSaving(null)
  }

  return <div className="max-w-7xl mx-auto">
    <div className="bg-gradient-to-r from-slate-900 to-indigo-900 text-white p-6 rounded-xl">
      <h1 className="text-2xl font-bold">Evaluate All Levels — Easy & Clear</h1>
      <p className="text-sm opacity-80 mt-1">For every assigned group, see all 12 levels in order. Previous level must be Approved/Locked before next unlocks. Approve student work, request changes with a remark, or lock to finalize.</p>
      <div className="mt-3 flex gap-2 text-xs">
        <span className="bg-white/20 px-3 py-1 rounded">Step 1: Pick a group left</span>
        <span className="bg-white/20 px-3 py-1 rounded">Step 2: Review each level's student content</span>
        <span className="bg-white/20 px-3 py-1 rounded">Step 3: Approve / Request Changes / Enter marks</span>
      </div>
    </div>

    <div className="grid grid-cols-4 gap-6 mt-6">
      <div className="bg-white p-4 rounded-xl border h-fit">
        <h2 className="font-bold text-sm">My Assigned Groups ({groups.length})</h2>
        <p className="text-xs text-gray-500">HOD allocated you as Guide & Reviewer (same person) — you evaluate every level for these groups.</p>
        <div className="mt-3 flex flex-col gap-2">
          {groups.map((g)=><button key={g.group_id} onClick={()=>openGroup(g)} className={`text-left p-3 rounded-xl border ${selected?.group_id===g.group_id?'bg-blue-600 text-white border-blue-600':'bg-gray-50 hover:bg-blue-50'}`}>
            <div className="font-semibold text-sm">Group {g.group_number}</div>
            <div className="text-xs opacity-80 truncate">{g.level.current_level_name}</div>
            <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full ${g.level.current_level_status==='SUBMITTED'?'bg-yellow-400 text-yellow-900': g.level.current_level_status==='APPROVED'?'bg-green-100 text-green-700':'bg-gray-200 text-gray-600'}`}>{g.level.current_level_status}</span>
            {(g as any).needs_data_approval && <span className="ml-1 text-xs bg-amber-500 text-white px-2 py-0.5 rounded">Needs you</span>}
          </button>)}
          {groups.length===0&&<div className="text-xs text-gray-400 py-4 text-center">No groups — ask HOD to allocate via HOD → Allocate (same user can be Guide & Reviewer)</div>}
        </div>
      </div>

      <div className="col-span-3">
        {!selected && <div className="bg-white p-12 rounded-xl border text-center">
          <div className="text-4xl">👈</div>
          <div className="font-semibold mt-2">Select a group to start evaluating</div>
          <div className="text-sm text-gray-500">All 12 levels will appear in order — most recent submission on top.</div>
        </div>}
        {selected && <div className="bg-white p-6 rounded-xl border">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold">Group {selected.group_number} — {levels.find(l=>l.order===selected.level.current_level_order)?.name||selected.level.current_level_name}</h2>
              <div className="text-sm text-gray-600">Current Level {selected.level.current_level_order} • {selected.level.current_level_status}</div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2 max-w-md"><div className="bg-green-600 h-2 rounded-full" style={{width: `${(levels.filter(l=>['APPROVED','LOCKED'].includes(l.status)).length/levels.length*100)||0}%`}}></div></div>
            </div>
            <button onClick={()=>openGroup(selected)} className="border px-3 py-1 rounded text-sm">Refresh</button>
          </div>

          <div className="mt-6 flex flex-col gap-4">
            {levels.map((lvl)=>{
              const sub=findSubForLevel(lvl)
              const isDone=['APPROVED','LOCKED'].includes(lvl.status)
              const isCurrent=lvl.order===selected.level.current_level_order
              const isLocked=lvl.status==='NOT_STARTED' && !levels.slice(0, lvl.order).every(x=>['APPROVED','LOCKED'].includes(x.status))
              const criteria=criteriaMap[lvl.id]||[]
              return <div key={lvl.id} className={`border rounded-xl overflow-hidden ${isCurrent?'border-blue-400 ring-2 ring-blue-100': isDone?'border-green-200':''}`}>
                <div className={`p-4 flex justify-between items-center ${isDone?'bg-green-50': isCurrent?'bg-blue-50':'bg-gray-50'}`}>
                  <div className="flex gap-3 items-center">
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${isDone?'bg-green-600 text-white': isCurrent?'bg-blue-600 text-white': 'bg-gray-300 text-gray-700'}`}>{isDone?'✓': lvl.order}</div>
                    <div>
                      <div className="font-semibold text-sm">Level {lvl.order} — {lvl.name}</div>
                      <div className="text-xs text-gray-500">{lvl.slug} • {lvl.granted?'Access Granted': lvl.order===1 && !lvl.granted?'Waiting for HOD/Guide grant':''}</div>
                    </div>
                  </div>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${lvl.status==='APPROVED'?'bg-green-100 text-green-700': lvl.status==='LOCKED'?'bg-slate-800 text-white': lvl.status==='SUBMITTED'?'bg-yellow-100 text-yellow-800': lvl.status==='CHANGES_REQUIRED'?'bg-red-100 text-red-700': 'bg-gray-200 text-gray-600'}`}>{lvl.status}</span>
                </div>

                {!sub || lvl.status==='NOT_STARTED' ? <div className="p-6 text-center text-sm text-gray-400">No submission yet — student hasn't filled this level. Previous levels must be completed first.</div> : <div className="p-4">
                  <div className="bg-blue-50 p-3 rounded border">
                    <div className="text-xs font-bold text-blue-900">Student's submission:</div>
                    <div className="text-sm mt-1 bg-white p-3 rounded border max-h-40 overflow-auto">
                      {typeof sub.content==='object' ? Object.entries(sub.content).map(([k,v]:any)=><div key={k} className="py-1 border-b last:border-0"><span className="font-medium">{k}:</span> {String(v).slice(0,200)}</div>) : <div>{String(sub.content).slice(0,500)}</div>}
                      {!sub.content || Object.keys(sub.content).length===0 && <span className="text-gray-400">Empty — student submitted blank</span>}
                    </div>
                    {sub.review_remarks && <div className="text-xs mt-2 p-2 bg-amber-50 border border-amber-200 rounded">Your last remark: {sub.review_remarks}</div>}
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <button onClick={()=>doAction(sub,'approve')} className="bg-green-600 text-white px-4 py-2 rounded text-sm">✓ Approve — unlock next level</button>
                    <button onClick={()=>doAction(sub,'changes')} className="bg-amber-500 text-white px-4 py-2 rounded text-sm">✎ Request Changes (add remark)</button>
                    <button onClick={()=>doAction(sub,'lock')} className="bg-slate-800 text-white px-4 py-2 rounded text-sm">🔒 Lock (finalize)</button>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Approve → next level becomes clickable for student. Request Changes → student sees your remark and resubmits. Lock → no further edits.</div>

                  {criteria.length>0 && <div className="mt-5">
                    <div className="text-sm font-bold">Marks — enter per criterion (easy table)</div>
                    <div className="text-xs text-gray-500">Enter obtained marks ≤ max, add remark, Save. All criteria must have marks before you can finalize the review.</div>
                    <table className="w-full mt-2 border text-sm">
                      <thead className="bg-gray-100"><tr><th className="p-2 text-left">Criterion</th><th className="p-2">Max</th><th className="p-2">Obtained *</th><th className="p-2">Remark</th><th className="p-2"></th></tr></thead>
                      <tbody>
                        {criteria.map((c:any)=><tr key={c.id} className="border-t">
                          <td className="p-2"><div className="font-medium">{c.name}</div><div className="text-xs text-gray-500">{c.description?.slice(0,60)}</div></td>
                          <td className="p-2 text-center">{c.max_marks}</td>
                          <td className="p-2"><input id={`obt-${c.id}`} placeholder="0" className="border p-1 rounded w-20 text-center" defaultValue={c.obtained_marks||''} /></td>
                          <td className="p-2"><input id={`rem-${c.id}`} placeholder="Good" className="border p-1 rounded w-full text-xs" /></td>
                          <td className="p-2"><button onClick={()=>{
                            const v=(document.getElementById(`obt-${c.id}`) as HTMLInputElement)?.value
                            const r=(document.getElementById(`rem-${c.id}`) as HTMLInputElement)?.value
                            saveMark(c, selected.group_id, v, r)
                          }} disabled={saving===c.id} className="bg-blue-600 text-white px-3 py-1 rounded text-xs disabled:opacity-50">{saving===c.id?'Saving...':'Save'}</button></td>
                        </tr>)}
                      </tbody>
                    </table>
                  </div>}
                  {criteria.length===0 && <div className="text-xs text-gray-400 mt-3">No criteria for this level — marks are entered only for Review levels (HOD configures rubrics). For other levels, just Approve/Request Changes.</div>}
                </div>}
              </div>
            })}
          </div>
          {msg&&<div className="mt-4 p-3 rounded bg-blue-50 text-blue-800 text-sm border border-blue-200">{msg}</div>}
        </div>}
      </div>
    </div>
  </div>
}
