import {ReactNode,useState} from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {X,ArrowUpRight,FileText,ArrowRight,LoaderCircle} from 'lucide-react';
import {Link} from 'react-router-dom';
import {cva} from 'class-variance-authority';
import {clsx} from 'clsx';
import {twMerge} from 'tailwind-merge';
export const buttonVariants=cva('button',{variants:{variant:{default:'primary',outline:'outline',ghost:'ghost'}},defaultVariants:{variant:'default'}});
export function Button({children,variant='default',className,...props}:React.ButtonHTMLAttributes<HTMLButtonElement>&{variant?:'default'|'outline'|'ghost'}){return <button className={twMerge(clsx(buttonVariants({variant}),className))} {...props}>{children}</button>}
export function Badge({children,tone='blue'}:{children:ReactNode;tone?:string}){return <span className={'badge '+tone}>{children}</span>}
export function PageHeading({eyebrow,title,description,action}:{eyebrow:string;title:string;description?:string;action?:ReactNode}){return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description&&<p>{description}</p>}</div>{action}</div>}
export function Loading(){return <div className="loading" role="status"><LoaderCircle className="spin"/> Loading research…</div>}
export function ErrorBox({error}:{error:unknown}){return error?<div role="alert" className="error">{error instanceof Error?error.message:String(error)}</div>:null}
export function Empty({children}:{children:ReactNode}){return <div className="empty"><FileText size={30}/><p>{children}</p></div>}
export function Modal({title,trigger,children,open,onOpenChange}:{title:string;trigger?:ReactNode;children:ReactNode;open?:boolean;onOpenChange?:(v:boolean)=>void}){return <Dialog.Root open={open} onOpenChange={onOpenChange}>{trigger&&<Dialog.Trigger asChild>{trigger}</Dialog.Trigger>}<Dialog.Portal><Dialog.Overlay className="modal-overlay"/><Dialog.Content className="modal"><Dialog.Title>{title}</Dialog.Title><Dialog.Description className="sr-only">Complete the fields below.</Dialog.Description><Dialog.Close className="modal-close" aria-label="Close"><X/></Dialog.Close>{children}</Dialog.Content></Dialog.Portal></Dialog.Root>}
export function DocCard({doc}:{doc:any}){return <Link to={'/repository/'+doc.id} className="doc-card"><div className="card-top"><span className="document-icon"><FileText size={22}/></span><Badge tone={doc.region==='Arctic'?'purple':'blue'}>{doc.region}</Badge></div><div className="meta">{doc.category} <span>·</span> {doc.year}</div><h3>{doc.title}</h3><p>{doc.abstract}</p><div className="card-bottom"><span>{doc.domain}</span><ArrowUpRight size={18}/></div>{doc.moderation!=='PUBLISHED'&&<Badge tone="amber">{doc.moderation.replace('_',' ')}</Badge>}</Link>}
export function SectionTitle({title,to,label='View all'}:{title:string;to?:string;label?:string}){return <div className="section-title"><h2>{title}</h2>{to&&<Link to={to}>{label} <ArrowRight size={16}/></Link>}</div>}
export function useAction(){const[error,setError]=useState('');const[busy,setBusy]=useState(false);const[success,setSuccess]=useState('');return{error,busy,success,run:async(fn:()=>Promise<any>,message='Saved')=>{setError('');setSuccess('');setBusy(true);try{const result=await fn();setSuccess(message);return result}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}}
