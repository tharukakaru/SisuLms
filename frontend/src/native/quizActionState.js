// Visibility uses classroom permissions, never quiz count or the selected filter.
export function quizActionState({classroom,role,permission,readiness,busy=false}) {
  const manager=role==='Teacher'||role==='Admin'
  const visible=!!classroom&&manager&&(permission===true||readiness.can_manage===true||permission==null)
  const disabled=busy||readiness.status!=='ready'||readiness.can_manage!==true
  let message=''
  if(readiness.status==='loading')message='Checking quiz setup…'
  else if(readiness.status==='error')message='Unable to check quiz setup. '+readiness.error
  else if(readiness.can_manage===false)message='Classroom management access is required to create quizzes.'
  else if(readiness.status==='setup')message='Quiz setup required: the classroom quiz schema has not been migrated. Ask the deployment administrator to coordinate migration of IL Classroom Quiz and IL Classroom Quiz Submission. Do not migrate the shared preview database from this local Bench.'
  return {visible,disabled,message,retry:readiness.status==='error'||readiness.status==='setup'}
}
