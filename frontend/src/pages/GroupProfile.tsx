import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import client from '../api/client'

type MemberForm = { name: string; roll_number: string; email: string; role: 'leader' | 'member' }

export default function GroupProfile() {
  const [searchParams] = useSearchParams()
  const groupIdParam = searchParams.get('group_id')
  const [loading, setLoading] = useState(true)
  const [group, setGroup] = useState<any>(null)
  const [canEdit, setCanEdit] = useState(false)
  const [isLocked, setIsLocked] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [editProject, setEditProject] = useState(false)
  const [projectForm, setProjectForm] = useState({ title: '', area_domain: '', description: '' })
  const [projectErrors, setProjectErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberForm, setMemberForm] = useState<MemberForm>({ name: '', roll_number: '', email: '', role: 'member' })
  const [memberErrors, setMemberErrors] = useState<Record<string, string>>({})
  const [editingMember, setEditingMember] = useState<any>(null)
  const [editMemberForm, setEditMemberForm] = useState<MemberForm>({ name: '', roll_number: '', email: '', role: 'member' })

  const fetchProfile = async () => {
    setLoading(true); setError(''); setSuccess('')
    try {
      const url = groupIdParam ? `/api/v1/groups/${groupIdParam}/profile/` : '/api/v1/groups/my-profile/'
      const res = await client.get(url)
      const data = res.data.data
      if (!data) { setGroup(null); setLoading(false); return }
      setGroup(data)
      setCanEdit(!!data.can_edit)
      setIsLocked(!!data.is_locked)
      setProjectForm({ title: data.project_detail?.title || '', area_domain: data.project_detail?.area_domain || '', description: data.project_detail?.description || '' })
    } catch (e: any) {
      setError(e.response?.data?.message || 'Failed to load group profile')
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchProfile() }, [groupIdParam])

  const validateProject = () => {
    const err: Record<string, string> = {}
    if (!projectForm.title.trim()) err.title = 'Project Title is required'
    else if (projectForm.title.trim().length < 5) err.title = 'Title must be at least 5 characters'
    if (!projectForm.area_domain.trim()) err.area_domain = 'Domain/Area is required'
    setProjectErrors(err)
    return Object.keys(err).length === 0
  }

  const saveProject = async () => {
    if (!validateProject()) return
    setSaving(true); setError(''); setSuccess('')
    try {
      const res = await client.patch(`/api/v1/groups/${group.id}/profile/`, { project_title: projectForm.title, area_domain: projectForm.area_domain, description: projectForm.description })
      setGroup(res.data.data)
      setCanEdit(!!res.data.data.can_edit)
      setSuccess('Project details saved')
      setEditProject(false)
    } catch (e: any) {
      const d = e.response?.data
      setError(d?.message || 'Save failed')
      if (d?.errors) setProjectErrors(Object.fromEntries(Object.entries(d.errors).map(([k, v]: any) => [k === 'project_title' ? 'title' : k === 'area' ? 'area_domain' : k, Array.isArray(v) ? v[0] : v])))
    } finally { setSaving(false) }
  }

  const cancelProject = () => {
    setProjectForm({ title: group.project_detail?.title || '', area_domain: group.project_detail?.area_domain || '', description: group.project_detail?.description || '' })
    setProjectErrors({}); setEditProject(false)
  }

  const validateMember = (f: MemberForm) => {
    const err: Record<string, string> = {}
    if (!f.name.trim()) err.name = 'Name required'
    if (!f.roll_number.trim()) err.roll_number = 'PRN/Roll required'
    if (!f.email.trim()) err.email = 'Email required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) err.email = 'Invalid email'
    if (!['leader', 'member'].includes(f.role)) err.role = 'Role required'
    return err
  }

  const addMember = async () => {
    const errs = validateMember(memberForm)
    setMemberErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true); setError(''); setSuccess('')
    try {
      await client.post(`/api/v1/groups/${group.id}/add-member-direct/`, { name: memberForm.name, roll_number: memberForm.roll_number, email: memberForm.email.toLowerCase().trim(), role: memberForm.role })
      setSuccess('Member added')
      setMemberForm({ name: '', roll_number: '', email: '', role: 'member' })
      setShowAddMember(false)
      fetchProfile()
    } catch (e: any) {
      const d = e.response?.data
      setError(d?.message || 'Add member failed')
      if (d?.errors) setMemberErrors(Object.fromEntries(Object.entries(d.errors).map(([k, v]: any) => [k, Array.isArray(v) ? v[0] : v])))
    } finally { setSaving(false) }
  }

  const startEditMember = (m: any) => {
    setEditingMember(m)
    setEditMemberForm({ name: m.student_detail?.name || '', roll_number: m.student_detail?.roll_number || '', email: m.student_detail?.email || '', role: m.role })
    setMemberErrors({})
  }

  const saveEditMember = async () => {
    const errs = validateMember(editMemberForm)
    setMemberErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true); setError(''); setSuccess('')
    try {
      if (editingMember.student_detail?.id) {
        await client.patch(`/api/v1/students/${editingMember.student_detail.id}/`, { name: editMemberForm.name, roll_number: editMemberForm.roll_number, email: editMemberForm.email.toLowerCase().trim() })
      }
      await client.patch(`/api/v1/group-members/${editingMember.id}/`, { role: editMemberForm.role })
      setSuccess('Member updated')
      setEditingMember(null)
      fetchProfile()
    } catch (e: any) {
      setError(e.response?.data?.message || e.response?.data?.errors?.roll_number?.[0] || e.response?.data?.errors?.email?.[0] || 'Update failed')
    } finally { setSaving(false) }
  }

  const removeMember = async (m: any) => {
    if (!confirm(`Remove ${m.student_detail?.name || m.student_detail?.email}?`)) return
    try {
      await client.delete(`/api/v1/group-members/${m.id}/`)
      setSuccess('Member removed')
      fetchProfile()
    } catch (e: any) { setError(e.response?.data?.message || 'Remove failed') }
  }

  if (loading) return <div className="max-w-5xl mx-auto p-8"><div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading group profile...</div></div>
  if (error && !group) return <div className="max-w-5xl mx-auto p-8"><div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm">{error}</div><Link to="/cover" className="mt-4 inline-block text-blue-600 text-sm underline">Go to Cover</Link></div>
  if (!group) return <div className="max-w-5xl mx-auto p-6">
    <div className="bg-white border rounded-xl p-10 text-center">
      <h2 className="text-lg font-semibold text-slate-800">No Group Found</h2>
      <p className="text-sm text-gray-500 mt-1">You are not part of any group yet. Create your group to set up the profile.</p>
      <Link to="/cover" className="mt-4 inline-block bg-blue-600 text-white px-5 py-2 rounded-lg text-sm">Create Group</Link>
    </div>
  </div>

  const maxMembers = group.group_members_config?.max ?? 4
  const currentMembers = group.members?.length ?? 0

  return <div className="max-w-5xl mx-auto pb-8">
    <div className="bg-white border border-slate-200 rounded-xl p-6 flex flex-wrap justify-between gap-4">
      <div>
        <div className="text-xs font-semibold tracking-widest text-blue-600 uppercase">BE Project Log Book</div>
        <h1 className="text-2xl font-bold text-slate-900 mt-1">Group {group.group_number} <span className="font-normal text-slate-500">— {group.project_detail?.title || 'Untitled Project'}</span></h1>
        <div className="text-xs text-gray-500 mt-1">Academic Year {group.academic_year_detail?.year_label} • {group.department_detail?.name} {group.semester ? `• ${group.semester.name}` : ''}</div>
      </div>
      <div className="text-right">
        <div className="text-xs text-gray-400">Created {new Date(group.created_at).toLocaleDateString()} • Updated {new Date(group.updated_at).toLocaleDateString()} {group.updated_by_email ? `by ${group.updated_by_email}` : ''}</div>
        {isLocked && <div className="mt-2 inline-block bg-amber-100 text-amber-800 text-xs px-3 py-1 rounded-full font-medium">Locked — submitted/approved, edits disabled</div>}
        {!isLocked && canEdit && <div className="mt-2 inline-block bg-green-50 text-green-700 text-xs px-3 py-1 rounded-full">Editable — you can update this profile</div>}
        {!canEdit && !isLocked && <div className="mt-2 inline-block bg-slate-100 text-slate-600 text-xs px-3 py-1 rounded-full">Read-only</div>}
      </div>
    </div>

    {success && <div className="bg-green-50 border border-green-200 text-green-800 text-sm p-3 rounded-xl mt-4">{success}</div>}
    {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl mt-4">{error}</div>}

    <div className="grid md:grid-cols-2 gap-4 mt-6">
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Group Information</h3>
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div><div className="text-xs text-gray-400">Group Number</div><div className="font-medium text-slate-800">{group.group_number}</div></div>
          <div><div className="text-xs text-gray-400">Academic Year</div><div className="font-medium text-slate-800">{group.academic_year_detail?.year_label || '-'}</div></div>
          <div><div className="text-xs text-gray-400">Department</div><div className="font-medium text-slate-800">{group.department_detail?.name || '-'} <span className="text-gray-400">({group.department_detail?.code || ''})</span></div></div>
          <div><div className="text-xs text-gray-400">Semester</div><div className="font-medium text-slate-800">{group.semester ? `${group.semester.name} (#${group.semester.number})` : '—'}</div></div>
          <div className="col-span-2"><div className="text-xs text-gray-400">Status</div><div className="font-medium text-slate-800 capitalize">{group.status}</div></div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Guide Details</h3>
          <span className="text-xs text-gray-400">{group.guide_detail ? 'Assigned' : 'Pending'}</span>
        </div>
        {group.guide_detail ? <div className="mt-4 text-sm space-y-1">
          <div className="font-medium text-slate-800">{group.guide_detail.name}</div>
          <div className="text-gray-600">{group.guide_detail.email}</div>
          <div className="text-xs text-gray-500">{group.guide_detail.designation} {group.guide_detail.department ? `• ${group.guide_detail.department}` : ''}</div>
        </div> : <div className="mt-4 bg-slate-50 border border-dashed rounded-lg p-4 text-center text-sm text-gray-400">No guide assigned yet — HOD will allocate</div>}
      </div>
    </div>

    <div className="bg-white border border-slate-200 rounded-xl p-5 mt-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Project Details</h3>
        {canEdit && !isLocked && !editProject && <button onClick={() => setEditProject(true)} className="text-xs border border-slate-200 px-3 py-1.5 rounded-lg hover:bg-slate-50">Edit</button>}
        {editProject && <div className="flex gap-2">
          <button onClick={cancelProject} className="text-xs border px-3 py-1.5 rounded-lg">Cancel</button>
          <button onClick={saveProject} disabled={saving} className="text-xs bg-blue-600 text-white px-4 py-1.5 rounded-lg disabled:opacity-50">{saving ? 'Saving...' : 'Save'}</button>
        </div>}
      </div>
      {!editProject ? <div className="mt-4 space-y-3 text-sm">
        <div><div className="text-xs text-gray-400">Project Title</div><div className="font-medium text-slate-800">{group.project_detail?.title || '-'}</div></div>
        <div><div className="text-xs text-gray-400">Domain / Area</div><div className="font-medium text-slate-800">{group.project_detail?.area_domain || '-'}</div></div>
        <div><div className="text-xs text-gray-400">Description</div><div className="text-slate-700 whitespace-pre-wrap">{group.project_detail?.description || <span className="text-gray-400">No description</span>}</div></div>
      </div> : <div className="mt-4 space-y-3">
        <div><label className="text-xs font-medium text-slate-700">Project Title *</label><input value={projectForm.title} onChange={e => setProjectForm({ ...projectForm, title: e.target.value })} className="mt-1 w-full border rounded-lg p-2.5 text-sm" placeholder="e.g. AI Based Logbook System" />{projectErrors.title && <div className="text-xs text-red-600 mt-1">{projectErrors.title}</div>}</div>
        <div><label className="text-xs font-medium text-slate-700">Domain / Area *</label><input value={projectForm.area_domain} onChange={e => setProjectForm({ ...projectForm, area_domain: e.target.value })} className="mt-1 w-full border rounded-lg p-2.5 text-sm" placeholder="e.g. AI/ML, IoT, Web" />{projectErrors.area_domain && <div className="text-xs text-red-600 mt-1">{projectErrors.area_domain}</div>}</div>
        <div><label className="text-xs font-medium text-slate-700">Description</label><textarea value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} rows={3} className="mt-1 w-full border rounded-lg p-2.5 text-sm" placeholder="Brief project description" /></div>
      </div>}
    </div>

    <div className="bg-white border border-slate-200 rounded-xl p-5 mt-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Group Members <span className="font-normal normal-case text-gray-400">({currentMembers}/{maxMembers})</span></h3>
        {canEdit && !isLocked && currentMembers < maxMembers && <button onClick={() => setShowAddMember(!showAddMember)} className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg">{showAddMember ? 'Close' : '+ Add Member'}</button>}
      </div>
      <p className="text-xs text-gray-400 mt-1">Limit of {maxMembers} members is enforced by backend (college rule). Role distinguishes Leader vs Member.</p>

      {showAddMember && <div className="mt-4 border border-blue-100 bg-blue-50/50 rounded-xl p-4 grid md:grid-cols-4 gap-3">
        <div><label className="text-xs font-medium">Name *</label><input value={memberForm.name} onChange={e => setMemberForm({ ...memberForm, name: e.target.value })} className="mt-1 w-full border rounded-lg p-2 text-sm" placeholder="Full name" />{memberErrors.name && <div className="text-xs text-red-600">{memberErrors.name}</div>}</div>
        <div><label className="text-xs font-medium">PRN / Roll *</label><input value={memberForm.roll_number} onChange={e => setMemberForm({ ...memberForm, roll_number: e.target.value })} className="mt-1 w-full border rounded-lg p-2 text-sm" placeholder="41001" />{memberErrors.roll_number && <div className="text-xs text-red-600">{memberErrors.roll_number}</div>}</div>
        <div><label className="text-xs font-medium">Email *</label><input value={memberForm.email} onChange={e => setMemberForm({ ...memberForm, email: e.target.value })} className="mt-1 w-full border rounded-lg p-2 text-sm" placeholder="email@college.edu" />{memberErrors.email && <div className="text-xs text-red-600">{memberErrors.email}</div>}</div>
        <div><label className="text-xs font-medium">Role *</label><select value={memberForm.role} onChange={e => setMemberForm({ ...memberForm, role: e.target.value as any })} className="mt-1 w-full border rounded-lg p-2 text-sm"><option value="member">Member</option><option value="leader">Leader</option></select></div>
        <div className="md:col-span-4 flex gap-2"><button onClick={addMember} disabled={saving} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">{saving ? 'Adding...' : 'Add Member'}</button><button onClick={() => setShowAddMember(false)} className="border px-4 py-2 rounded-lg text-sm">Cancel</button></div>
      </div>}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-xs text-gray-400 border-b"><th className="text-left py-2 font-medium">#</th><th className="text-left py-2 font-medium">Name</th><th className="text-left py-2 font-medium">PRN / Roll</th><th className="text-left py-2 font-medium">Email</th><th className="text-left py-2 font-medium">Role</th>{canEdit && !isLocked && <th className="text-right py-2 font-medium">Actions</th>}</tr></thead>
          <tbody>
            {group.members.map((m: any, idx: number) => <tr key={m.id} className="border-b last:border-0">
              <td className="py-3 text-gray-500">{idx + 1}</td>
              {editingMember?.id === m.id ? <>
                <td><input value={editMemberForm.name} onChange={e => setEditMemberForm({ ...editMemberForm, name: e.target.value })} className="border rounded p-1.5 text-sm w-full" /></td>
                <td><input value={editMemberForm.roll_number} onChange={e => setEditMemberForm({ ...editMemberForm, roll_number: e.target.value })} className="border rounded p-1.5 text-sm w-full" /></td>
                <td><input value={editMemberForm.email} onChange={e => setEditMemberForm({ ...editMemberForm, email: e.target.value })} className="border rounded p-1.5 text-sm w-full" /></td>
                <td><select value={editMemberForm.role} onChange={e => setEditMemberForm({ ...editMemberForm, role: e.target.value as any })} className="border rounded p-1.5 text-sm"><option value="member">Member</option><option value="leader">Leader</option></select></td>
                <td className="text-right"><div className="flex justify-end gap-1"><button onClick={saveEditMember} className="text-xs bg-blue-600 text-white px-2 py-1 rounded">Save</button><button onClick={() => setEditingMember(null)} className="text-xs border px-2 py-1 rounded">Cancel</button></div></td>
              </> : <>
                <td className="py-3 font-medium text-slate-800">{m.student_detail?.name || m.student_detail?.email}</td>
                <td className="py-3 text-slate-600">{m.student_detail?.roll_number || '-'}</td>
                <td className="py-3 text-slate-600">{m.student_detail?.email || '-'}</td>
                <td className="py-3"><span className={`text-xs px-2 py-0.5 rounded-full ${m.role === 'leader' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>{m.role}</span></td>
                {canEdit && !isLocked && <td className="py-3 text-right"><div className="flex justify-end gap-2"><button onClick={() => startEditMember(m)} className="text-xs text-blue-600 hover:underline">Edit</button><button onClick={() => removeMember(m)} className="text-xs text-red-600 hover:underline">Remove</button></div></td>}
              </>}
            </tr>)}
            {group.members.length === 0 && <tr><td colSpan={6} className="py-8 text-center text-gray-400">No members yet</td></tr>}
          </tbody>
        </table>
      </div>
      {currentMembers >= maxMembers && <div className="mt-3 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2">Maximum of {maxMembers} members reached (college rule).</div>}
      {editingMember && memberErrors.email && <div className="text-xs text-red-600 mt-2">{memberErrors.email}</div>}
    </div>

    <div className="text-xs text-gray-400 mt-4 text-center">This profile is the single source of truth for dashboards, submissions, reviews, audit trail, progress and final PDF.</div>
  </div>
}
