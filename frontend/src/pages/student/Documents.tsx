import { useRealtimeTick } from '../../contexts/RealtimeContext'
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function Documents(){
  const tick=useRealtimeTick()
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [list,setList]=useState<any[]>([])
  const [title,setTitle]=useState('')
  const [type,setType]=useState('report')
  const [file,setFile]=useState<File|null>(null)
  const [msg,setMsg]=useState('')
  const load=async()=>{
    setLoading(true)
    try{const r=await client.get('/api/v1/student/documents/');setList(r.data.data||[])}catch(e:any){setError(e.response?.data?.message||'Failed')}
    setLoading(false)
  }
  useEffect(()=>{load()},[tick])
  const upload=async()=>{
    if(!file) {setMsg('Select file');return}
    const fd=new FormData();fd.append('file',file);fd.append('title',title||file.name);fd.append('doc_type',type)
    try{await client.post('/api/v1/student/documents/',fd,{headers:{'Content-Type':'multipart/form-data'}});setMsg('Uploaded');setFile(null);setTitle('');load()}catch(e:any){setMsg(e.response?.data?.message||'Upload failed')}
  }
  if(loading) return <div className="bg-white border rounded-xl p-12 text-center text-sm text-gray-500">Loading documents...</div>
  if(error) return <div className="bg-white border rounded-xl p-8 text-center text-sm text-red-600">{error}</div>
  return <div className="max-w-5xl mx-auto">
    <h1 className="text-xl font-bold">Documents</h1>
    <div className="bg-white border rounded-xl p-4 mt-4 flex flex-wrap gap-3 items-end">
      <label className="text-xs">Title<input value={title} onChange={e=>setTitle(e.target.value)} className="ml-2 border rounded p-2 text-sm" placeholder="SRS.pdf"/></label>
      <label className="text-xs">Type<select value={type} onChange={e=>setType(e.target.value)} className="ml-2 border rounded p-2 text-sm"><option value="synopsis">Synopsis</option><option value="report">Report</option><option value="uml_diagram">UML</option><option value="research_paper">Paper</option><option value="ppt">PPT</option><option value="source_code">Source</option><option value="other">Other</option></select></label>
      <input type="file" onChange={e=>setFile(e.target.files?.[0]||null)} className="border rounded p-2 text-sm"/>
      <button onClick={upload} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">Upload</button>
      {msg && <span className="text-xs text-green-600">{msg}</span>}
    </div>
    <div className="bg-white border rounded-xl mt-4 overflow-hidden">
      {list.length===0 ? <div className="p-12 text-center text-sm text-gray-400">No documents yet</div> :
      <table className="w-full text-sm">
        <thead><tr className="text-xs text-gray-400 bg-gray-50"><th className="text-left p-3">Document</th><th className="text-left p-3">Version</th><th className="text-left p-3">Uploaded By</th><th className="text-left p-3">Date</th><th className="text-left p-3">Status</th><th className="text-left p-3">Versions</th></tr></thead>
        <tbody>{list.map((d:any)=><tr key={d.id} className="border-t"><td className="p-3 font-medium">{d.title}</td><td className="p-3">v{d.current_version}</td><td className="p-3 text-xs">{d.uploaded_by}</td><td className="p-3 text-xs">{new Date(d.created_at).toLocaleDateString()}</td><td className="p-3 text-xs">{d.status}</td><td className="p-3 text-xs">{d.versions?.length>1? d.versions.map((v:any)=>`v${v.version_number}`).join(', '): '-'}</td></tr>)}</tbody>
      </table>}
    </div>
  </div>
}