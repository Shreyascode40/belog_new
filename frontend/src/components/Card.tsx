export default function Card({title,value,sub}:{title:string;value:string|number;sub?:string}){
  return <div className="bg-white p-5 rounded-xl shadow-sm border">
    <div className="text-sm text-gray-500">{title}</div>
    <div className="text-2xl font-bold mt-1">{value}</div>
    {sub&&<div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
}
