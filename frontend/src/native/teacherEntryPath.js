// A tab-local navigation preference, never an account type or permission.
const key='sisu-teacher-entry-path'
const lifetime=24*60*60*1000
const valid=path=>path==='individual'||path==='institute'
const isTeacher=session=>session?.role==='Teacher'||(!session?.member&&session?.onboarding_kind==='Teacher')

export function rememberTeacherPath(storage,path,now=Date.now()){
  try{
    if(valid(path))storage.setItem(key,JSON.stringify({path,createdAt:now}))
    else storage.removeItem(key)
  }catch{/* Navigation still works when browser storage is unavailable. */}
}

export function resolveTeacherPath(storage,session,now=Date.now()){
  try{
    const saved=JSON.parse(storage.getItem(key)||'null')
    if(!saved)return ''
    if(!valid(saved.path)||!Number.isFinite(saved.createdAt)||now-saved.createdAt>lifetime||saved.createdAt>now){storage.removeItem(key);return ''}
    if(!session?.authenticated){if(saved.user)storage.removeItem(key);return ''}
    const teacher=isTeacher(session)
    if(!teacher||session.control_plane||!session.user||(saved.user&&saved.user!==session.user)){storage.removeItem(key);return ''}
    storage.setItem(key,JSON.stringify({...saved,user:session.user}))
    return saved.path
  }catch{return ''}
}

export function teacherEntryView(session,path,completingGoogleSignup=false){
  if(!session?.authenticated||session.control_plane||completingGoogleSignup)return ''
  const teacher=isTeacher(session)
  if(!teacher)return ''
  if(path==='institute'&&(session.member||session.shared_campus))return 'institute'
  if(path==='individual'&&!session.member&&session.shared_campus)return 'setup'
  return ''
}
