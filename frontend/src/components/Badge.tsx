export default function Badge({status}:{status:string}){
  const m:any={active:'bg-blue-100 text-blue-700',approved:'bg-green-100 text-green-700',submitted:'bg-yellow-100 text-yellow-700',draft:'bg-gray-100 text-gray-700',locked:'bg-slate-800 text-white'}
  return <span className={`px-2 py-1 rounded-full text-xs ${m[status]||'bg-gray-100'}`}>{status}</span>
}
