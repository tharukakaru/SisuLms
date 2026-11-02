<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const rows=ref([]),error=ref('')
onMounted(async()=>{try{rows.value=await request('registration','account_notifications',{},'GET')}catch(e){error.value=e.message}})
</script><template><section class="panel" style="padding:24px"><h2>Notifications</h2><p v-if="error" role="alert">{{error}}</p><article v-for="row in rows" :key="row.name" style="padding:16px 0"><strong>{{row.subject}}</strong><p>{{row.creation}}</p></article><p v-if="!rows.length&&!error">Your account and registration confirmations will appear here.</p></section></template>
