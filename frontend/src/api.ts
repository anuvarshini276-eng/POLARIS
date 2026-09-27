import {create} from 'zustand';
export type User={id:string;name:string;email:string;role:string};
type Session={user:User|null;token:string;refresh:string;set:(data:any)=>void;clear:()=>void};
export const useSession=create<Session>(set=>({user:null,token:'',refresh:'',set:data=>set({user:data.user,token:data.access_token,refresh:data.refresh_token}),clear:()=>set({user:null,token:'',refresh:''})}));
let refreshing:Promise<void>|null=null;
export async function api(path:string,options:RequestInit={},retry=true):Promise<any>{
 const session=useSession.getState(); const headers:Record<string,string>={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(session.token?{Authorization:`Bearer ${session.token}`}:{})};
 const response=await fetch('/api/v1'+path,{...options,headers:{...headers,...options.headers}});
 if(response.status===401&&session.refresh&&retry&&!path.startsWith('/auth')){
  if(!refreshing)refreshing=api('/auth/refresh',{method:'POST',body:JSON.stringify({refresh_token:session.refresh})},false).then(data=>useSession.getState().set(data)).catch(()=>useSession.getState().clear()).finally(()=>{refreshing=null});
  await refreshing; return api(path,options,false);
 }
 if(!response.ok){const data=await response.json().catch(()=>({detail:'Request failed'}));throw new Error(typeof data.detail==='string'?data.detail:'Please check the form fields.');}
 return response.json();
}
export const post=(path:string,data:any)=>api(path,{method:'POST',body:JSON.stringify(data)});
export async function download(path:string,name:string){const r=await fetch('/api/v1'+path,{headers:useSession.getState().token?{Authorization:'Bearer '+useSession.getState().token}:{}});if(!r.ok)throw new Error('Download unavailable');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);}
