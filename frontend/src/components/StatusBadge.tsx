export default function StatusBadge({status}:{status:string}){
  const m:Record<string,string>={
    draft:'bg-gray-200 text-gray-700',
    submitted:'bg-blue-100 text-blue-700',
    under_review:'bg-yellow-100 text-yellow-800',
    underReview:'bg-yellow-100 text-yellow-800',
    submitted_lower:'bg-blue-100 text-blue-700',
    approved:'bg-green-100 text-green-700',
    changes_required:'bg-red-100 text-red-700',
    changes_requested:'bg-red-100 text-red-700',
    locked:'bg-slate-800 text-white',
    resubmitted:'bg-orange-100 text-orange-700',
    not_started:'bg-gray-100 text-gray-500',
  }
  const key=status?.toLowerCase()
  const cls=m[key]||'bg-gray-100 text-gray-600'
  return <span className={`text-xs px-2 py-1 rounded-full font-medium ${cls}`}>{status?.replace(/_/g,' ').toUpperCase()}</span>
}
