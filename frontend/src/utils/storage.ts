export const setTokens=(a:string,r:string)=>{localStorage.setItem('access',a);localStorage.setItem('refresh',r)}
export const getRole=()=>{try{const t=localStorage.getItem('access');if(!t) return null;return JSON.parse(atob(t.split('.')[1])).role||null}catch{return null}}
