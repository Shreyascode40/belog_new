import { createContext, useContext, useEffect, useRef, useState } from 'react'
import client from '../api/client'

type Update = { submissions: any[]; documents: any[]; notifications: any[]; has_updates: boolean; server_time: string }
const RealtimeContext = createContext<{tick:number; last: Update | null}>({tick:0, last:null})

export function RealtimeProvider({children}:{children:React.ReactNode}){
  const [tick,setTick]=useState(0)
  const [last,setLast]=useState<Update|null>(null)
  const [toast,setToast]=useState<string>('')
  const sinceRef=useRef<string>(new Date(Date.now()-30000).toISOString())
  const pollRef=useRef<number | null>(null)

  useEffect(()=>{
    if(!localStorage.getItem('access')) return
    let es: EventSource | null = null
    try{
      const token=localStorage.getItem('access')
      if(token && typeof window !== 'undefined' && 'EventSource' in window){
        es=new EventSource(`/api/v1/realtime/stream/?token=${encodeURIComponent(token)}`)
        es.onmessage=(e)=>{
          try{
            const d=JSON.parse(e.data)
            if(d.type==='update' && d.has_updates){
              setTick(t=>t+1)
              setToast('New update received')
              setTimeout(()=>setToast(''),3000)
            }
          }catch{}
        }
        es.onerror=()=>{ try{ es?.close()}catch{}; es=null }
      }
    }catch{}

    const poll=async()=>{
      try{
        const r=await client.get('/api/v1/realtime/updates/', {params:{since:sinceRef.current}})
        const d=r.data.data as Update
        sinceRef.current=d.server_time
        setLast(d)
        if(d.has_updates){
          setTick(t=>t+1)
          if(d.notifications.length){
            const n=d.notifications[0]
            setToast(n.title)
            setTimeout(()=>setToast(''),4000)
            if(typeof Notification !== 'undefined' && Notification.permission==='granted'){
              try{ new Notification(n.title,{body:n.message})}catch{}
            }
          } else if(d.submissions.length){
            const s=d.submissions[0]
            setToast(`Submission ${s.status} — Group ${s.group}`)
            setTimeout(()=>setToast(''),3500)
          }
        }
      }catch{}
    }
    poll()
    const id=window.setInterval(poll, 3000)
    pollRef.current=id
    const onVis=()=>{ if(document.visibilityState==='visible') poll() }
    document.addEventListener('visibilitychange', onVis)
    if(typeof Notification !== 'undefined' && Notification.permission==='default'){
      try{ Notification.requestPermission()}catch{}
    }
    return ()=>{
      window.clearInterval(id)
      document.removeEventListener('visibilitychange', onVis)
      if(es) try{ es.close()}catch{}
    }
  },[])

  return <RealtimeContext.Provider value={{tick, last}}>
    {children}
    {toast && <div className="fixed bottom-4 right-4 bg-slate-900 text-white text-sm px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm">{toast}</div>}
  </RealtimeContext.Provider>
}

export const useRealtime=()=> useContext(RealtimeContext)
export const useRealtimeTick=()=> useContext(RealtimeContext).tick
