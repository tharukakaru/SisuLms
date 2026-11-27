export const ownerSections = [
  {name:'Overview',group:'Workspace',icon:'LayoutDashboard',description:'Review your campuses and the work that needs attention.'},
  {name:'People & connections',group:'Workspace',icon:'Users',description:'Explore students, teachers and institutes, and see how their workspaces and classes connect.',managersOnly:true},
  {name:'Admin access',group:'Workspace',icon:'ShieldCheck',description:'Create admins, send invitations and manage who has full authority.',managersOnly:true},
  {name:'Organizations',group:'Workspace',icon:'Building2',description:'Register and manage institutes with their own hosted website.'},
  {name:'Plans',group:'Workspace',icon:'Package',description:'Manage subscription prices, included tools and plan descriptions.'},
  {name:'Billing',group:'Finance',icon:'Receipt',description:'Review provider accounts, invoices and payment records.'},
  {name:'Student-count payments',group:'Finance',icon:'Users',description:'Set the monthly student rate, receiving bank details and review provider receipts.',managersOnly:true},
  {name:'Commerce',group:'Finance',icon:'Wallet',description:'Review commercial reports from your hosted websites.'},
  {name:'Site policies',group:'Platform',icon:'Settings2',description:'Manage website policies and check their delivery status.'},
  {name:'Provisioning',group:'Platform',icon:'Globe2',description:'Track institute website setup and operator tasks.'},
  {name:'Audit log',group:'Platform',icon:'ListChecks',description:'Review who changed platform settings and why.'},
  {name:'Readiness',group:'Platform',icon:'CircleCheck',description:'Check local services, reporting connections and email delivery.'},
  {name:'Platform guide',group:'Help',icon:'CircleHelp',description:'Find the right controls for your administration tasks.'},
  {name:'Profile',group:'Account',icon:'UserRound',description:'View your administrator account and manage your password.'},
]
export function ownerSection(hash='') {
  try { const name=decodeURIComponent(hash.replace(/^#/,'')); return ownerSections.some(s=>s.name===name)?name:'Overview' }
  catch { return 'Overview' }
}
export function isLocalOwner(location) {
  return location.protocol==='http:' && (['127.0.0.1','localhost'].includes(location.hostname)||location.hostname.endsWith('.localhost')) && location.port==='5401'
}
export function campusAdminUrl(campus,location) {
  if(isLocalOwner(location)) {
    const port={'sisuacademylk.com':'5400','staging.sisuacademylk.com':'5402','teen.sisuacademylk.com':'5403'}[campus.site]
    if(!port)return null
    const host=location.hostname.endsWith('.localhost')?{'5400':'campus','5402':'staging','5403':'teen'}[port]+'.localhost':location.hostname
    return `http://${host}:${port}/campus`
  }
  try {const url=new URL(campus.url);return url.protocol==='https:'&&url.hostname===campus.site&&!url.username&&!url.password?url.href:null}
  catch {return null}
}
