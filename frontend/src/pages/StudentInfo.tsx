import { useEffect, useState } from 'react'
import client from '../api/client'
import { useNavigate } from 'react-router-dom'

type Form = { name: string; roll_number: string; mobile: string; exam_seat_number: string; email: string; te_result: string; contribution: string }

const emptyForm = (): Form => ({ name: '', roll_number: '', mobile: '', exam_seat_number: '', email: '', te_result: '', contribution: '' })

export default function StudentInfo() {
  const nav = useNavigate()
  const [group, setGroup] = useState<any>(null)
  const [members, setMembers] = useState<any[]>([])
  const [forms, setForms] = useState<Form[]>([emptyForm(), emptyForm(), emptyForm(), emptyForm()])
  const [msg, setMsg] = useState('')
  const [saving, setSaving] = useState(false)

  const load = async () => {
    const gRes = await client.get('/api/v1/groups/')
    const g = (gRes.data.results || gRes.data.data || gRes.data || [])[0]
    if (!g) return
    setGroup(g)
    const mRes = await client.get(`/api/v1/groups/${g.id}/`)
    const mems: any[] = mRes.data.members || []
    setMembers(mems)
    setForms(Array.from({ length: 4 }, (_, i) => {
      const m = mems[i]
      if (!m) return emptyForm()
      return {
        name: m.student_detail?.name || '',
        roll_number: m.student_detail?.roll_number || '',
        mobile: m.student_detail?.mobile || '',
        exam_seat_number: m.student_detail?.exam_seat_number || '',
        email: m.student_detail?.email || m.student || '',
        te_result: m.te_result || '',
        contribution: m.contribution || '',
      }
    }))
  }

  useEffect(() => { load() }, [])

  const setField = (idx: number, field: keyof Form, val: string) => {
    setForms(prev => prev.map((f, i) => i === idx ? { ...f, [field]: val } : f))
  }

  const saveAll = async () => {
    if (!group) return
    setSaving(true)
    setMsg('')
    let done = 0
    for (let i = 0; i < 4; i++) {
      const f = forms[i]
      const existing = members[i]
      const isEmpty = !f.name && !f.email && !f.roll_number
      if (isEmpty) continue
      if (!f.name || !f.roll_number || !f.email) {
        setMsg(`Member ${i + 1}: Name, Roll No. and Email are required`)
        setSaving(false)
        return
      }
      try {
        if (existing) {
          if (existing.student_detail?.id) {
            await client.patch(`/api/v1/students/${existing.student_detail.id}/`, {
              name: f.name, roll_number: f.roll_number, mobile: f.mobile, exam_seat_number: f.exam_seat_number, email: f.email
            })
            if (existing.student_detail.user_id) {
              try { await client.patch(`/api/v1/users/${existing.student_detail.user_id}/`, { email: f.email }) } catch {}
            }
          }
          await client.patch(`/api/v1/group-members/${existing.id}/`, { te_result: f.te_result, contribution: f.contribution })
          done++
        } else {
          await client.post(`/api/v1/groups/${group.id}/add-member-direct/`, f)
          done++
        }
      } catch (e: any) {
        const d = e.response?.data
        setMsg(d?.message || d?.errors?.roll_number?.[0] || d?.errors?.email?.[0] || `Member ${i + 1} save failed`)
        setSaving(false)
        return
      }
    }
    setMsg(done ? `${done} member(s) saved` : 'Nothing to save')
    setSaving(false)
    load()
  }

  const remove = async (idx: number) => {
    const m = members[idx]
    if (!m || !confirm(`Remove Member ${idx + 1} — ${m.student_detail?.name || ''}?`)) return
    await client.delete(`/api/v1/group-members/${m.id}/`)
    setMsg(`Member ${idx + 1} removed`)
    load()
  }

  const acknowledge = async () => {
    await client.post(`/api/v1/groups/${group.id}/acknowledge/`, {})
    setMsg('You acknowledged')
    load()
  }

  const submit = async () => {
    try {
      await client.post(`/api/v1/groups/${group.id}/submit-information/`)
      setMsg('Submitted — awaiting guide/HOD verification')
      setTimeout(() => nav('/'), 1000)
    } catch (e: any) {
      setMsg(e.response?.data?.message || 'Submit failed — need 4 members with all required fields and acknowledgement')
    }
  }

  if (!group) return <div className="max-w-3xl mx-auto p-8 bg-white rounded-xl border mt-6">No group yet — <a href="/cover" className="text-blue-600 underline">Create Cover</a> first. {msg && <div className="text-sm text-amber-600 mt-2">{msg}</div>}</div>

  const filled = members.length
  const allAcknowledged = members.length === 4 && members.every((m: any) => m.acknowledged)

  return <div className="max-w-5xl mx-auto">
    <h1 className="text-2xl font-bold">Student Information</h1>
    <p className="text-sm text-gray-500 mt-1">One member can fill details for <b>all 4 members</b> in one place. Fill the 4 cards below and click <b>Save All</b>.</p>

    <div className="bg-white border rounded-xl p-4 mt-4 flex flex-wrap gap-3 items-center justify-between">
      <div className="text-sm">Group <b>{group.group_number}</b> — {group.project?.title || 'Untitled'} <span className="text-gray-400">| {filled}/4 members</span></div>
      <div className="flex items-center gap-2">
        <div className="w-32 bg-gray-200 rounded-full h-2"><div className="bg-blue-600 h-2 rounded-full" style={{ width: `${(filled / 4) * 100}%` }} /></div>
        <span className="text-xs text-gray-500">{filled}/4</span>
      </div>
    </div>

    {filled > 0 && filled < 4 && <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm p-3 rounded-xl mt-3">Draft — {filled}/4 filled. Complete all 4 to submit.</div>}
    {filled === 4 && <div className="bg-green-50 border border-green-200 text-green-700 text-sm p-3 rounded-xl mt-3">4 members ready — save and submit for verification.</div>}

    <div className="grid md:grid-cols-2 gap-4 mt-6">
      {[0, 1, 2, 3].map(idx => {
        const m = members[idx]
        const f = forms[idx]
        const isLeader = idx === 0 && m?.role === 'leader'
        return <div key={idx} className={`border rounded-xl p-4 ${m ? 'bg-white' : 'bg-gray-50 border-dashed'}`}>
          <div className="flex justify-between items-center mb-3">
            <div className="font-semibold text-sm">Member {idx + 1} {isLeader && <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded ml-1">Leader</span>} {m?.acknowledged && <span className="text-green-600 text-xs ml-1">✓ Acknowledged</span>}</div>
            {m && <button onClick={() => remove(idx)} className="text-xs text-red-600 hover:underline">Remove</button>}
            {!m && <span className="text-xs text-gray-400">Empty slot</span>}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <label className="col-span-2 text-xs font-medium">Name *<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="Full name" value={f.name} onChange={e => setField(idx, 'name', e.target.value)} /></label>
            <label className="text-xs font-medium">Roll No. *<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="41001" value={f.roll_number} onChange={e => setField(idx, 'roll_number', e.target.value)} /></label>
            <label className="text-xs font-medium">TE Result<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="Distinction" value={f.te_result} onChange={e => setField(idx, 'te_result', e.target.value)} /></label>
            <label className="text-xs font-medium">Mobile *<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="10-digit" value={f.mobile} onChange={e => setField(idx, 'mobile', e.target.value)} /></label>
            <label className="text-xs font-medium">Exam Seat No. *<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="SEAT..." value={f.exam_seat_number} onChange={e => setField(idx, 'exam_seat_number', e.target.value)} /></label>
            <label className="col-span-2 text-xs font-medium">Email *<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="email@college.edu" value={f.email} onChange={e => setField(idx, 'email', e.target.value)} /></label>
            <label className="col-span-2 text-xs font-medium">Contribution<input className="mt-1 border rounded w-full p-2 text-sm" placeholder="e.g. Backend, Testing" value={f.contribution} onChange={e => setField(idx, 'contribution', e.target.value)} /></label>
          </div>
        </div>
      })}
    </div>

    <div className="bg-white border rounded-xl p-4 mt-6 flex flex-wrap gap-3">
      <button onClick={saveAll} disabled={saving} className="bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving...' : 'Save All Members'}</button>
      <button onClick={acknowledge} className="border px-6 py-2.5 rounded-lg text-sm">I Acknowledge</button>
      <button onClick={submit} disabled={filled !== 4 || !allAcknowledged} className="bg-green-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed" title={filled !== 4 ? 'Need 4 members' : !allAcknowledged ? 'All members must acknowledge' : ''}>Submit for Verification</button>
      <span className="text-xs text-gray-400 self-center">Save first, then submit. All 4 members need different Roll/Email.</span>
    </div>

    {msg && <div className="mt-4 text-sm p-3 rounded-xl bg-amber-50 border text-amber-800">{msg}</div>}

    <div className="bg-gray-50 border rounded-xl p-4 mt-4 text-xs text-gray-500">
      <b>How it works:</b> One group member fills all 4 cards here and clicks Save All — no invite needed. Each member's login email is set from the Email field. After all 4 acknowledge (each member logs in once to click I Acknowledge), Submit unlocks other stages.
    </div>
  </div>
}
