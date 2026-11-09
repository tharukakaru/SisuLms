<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const rows=ref([]),error=ref('')
async function load(){try{rows.value=await request('registration','account_notifications',{},'GET')}catch(e){error.value=e.message}}
async function read(row){try{await request('registration','read_account_notice',{name:row.name});row.read=1;window.dispatchEvent(new Event('sisu-notifications'))}catch(e){error.value=e.message}}
onMounted(load)
</script><template><section class="panel" style="padding:24px"><h2>Notifications</h2><p v-if="error" role="alert">{{error}}</p><article v-for="row in rows" :key="row.name" class="receipt" :class="{unread:!row.read}"><strong>{{row.subject}}</strong><p>{{row.creation}}</p><p style="white-space:pre-wrap;overflow-wrap:anywhere">{{row.email_content}}</p><button v-if="!row.read" class="button subtle" @click="read(row)">Mark as read</button></article><p v-if="!rows.length&&!error">Your account and registration confirmations will appear here.</p></section></template>
<style scoped>.receipt{padding:16px;margin:12px 0;border-radius:12px}.receipt.unread{border-left:4px solid #d72d46;background:#fff5f7}</style>
