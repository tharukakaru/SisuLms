import {ref} from 'vue'
import {request} from './client'
export const capabilities=ref(null)
export async function refreshCapabilities(){try{capabilities.value=await request('full_api','capabilities',{},'GET')}catch(error){capabilities.value=null;throw error}}
export function premiumVisible(value){return value?.premium_ai===true&&value?.organization_available===true}

