// Resolve Google signup before choosing a dashboard or onboarding view.
export async function googleSignupEntry(session, signup, request){
 if(!signup||!session?.authenticated)return null
 const policy=await request('portal_policy','public',{},'GET')
 const details=await request('registration','self_google_details',{},'GET')
 return {policy,accountExists:details.account_exists===true}
}
