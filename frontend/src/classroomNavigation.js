export function classroomNavigation(role) {
  return [
    {id:'dashboard',icon:'LayoutDashboard'},
    {id:'classrooms',icon:'BookOpen'},
    {id:'schedule',icon:'CalendarDays'},
    {id:'study',icon:'Coffee'},
    ...(role==='Admin'?[{id:'team',icon:'Users'},{id:'people',icon:'Users'}]:[]),
    {id:'connections',icon:'Search'},
    {id:'payments',icon:'CreditCard'},
    {id:'subscription',icon:'Receipt'},
    ...(role!=='Student'?[{id:'workspace',icon:'Settings2'},{id:'wallet',icon:'Wallet'}]:[]),
    {id:'news',icon:'Newspaper'},
    ...(role==='Admin'?[{id:'storage',icon:'HardDrive'}]:[]),
    {id:'profile',icon:'IdCard'},
    {id:'guide',icon:'CircleHelp'},
  ]
}

// Old bookmarks remain useful: choose a classroom, then open its matching tab.
export function classroomDestination(page) {
  if(page==='programmes')return {group:'Programmes',tab:'Overview'}
  const tabs={hub:'Overview',learning:'Papers & assignments',liveclasses:'Sessions',live:'Sessions',videos:'Recordings',library:'Recordings',lessons:'Recordings',purchases:'Recordings',papers:'Papers & assignments',quizzes:'Papers & assignments',results:'Papers & assignments'}
  return tabs[page]?{group:'Classes',tab:tabs[page]}:null
}
