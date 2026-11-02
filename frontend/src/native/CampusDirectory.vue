<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
import InstituteRegistration from './InstituteRegistration.vue'
const query=ref(''), page=ref(0), rows=ref([]), more=ref(false), busy=ref(false), error=ref(''), selected=ref(null)
async function load(target=0){
  if(busy.value)return
  busy.value=true;error.value=''
  try{
    const result=await request('campus_join','directory',{query:query.value,page:target},'GET')
    rows.value=result.institutes;more.value=result.has_more;page.value=target
  }catch(e){error.value=e.message;rows.value=[];more.value=false}
  finally{busy.value=false}
}
onMounted(()=>load())
</script>
<template>
  <section class="campus-directory" aria-labelledby="institute-directory-heading">
    <h2 id="institute-directory-heading">Find your institute</h2>
    <p>Students can register with an institute to receive their student number. Joining does not enroll you in classes.</p>
    <form @submit.prevent="load(0)" class="directory-search"><label for="institute-search">Institute name</label><input id="institute-search" v-model="query" maxlength="80" placeholder="Search institutes" :disabled="busy"><button :disabled="busy">Search</button></form>
    <p v-if="busy" role="status">Finding institutes…</p>
    <p v-if="error" role="alert">{{error}} <button @click="load(page)" :disabled="busy">Try again</button></p>
    <p v-else-if="!busy&&!rows.length">No institutes found. Try another name or check back when your institute has joined SISU.</p>
    <div class="directory-cards" :aria-busy="busy"><article v-for="institute in rows" :key="institute.name"><h3>{{institute.display_name}}</h3><p>Institute</p><button @click="selected=institute" :disabled="busy">Register as a student →</button></article></div>
    <nav v-if="!error&&(page||more)" aria-label="Institute results"><button :disabled="busy||page===0" @click="load(page-1)">Previous</button><span>Page {{page+1}}</span><button :disabled="busy||!more" @click="load(page+1)">Next</button></nav>
    <InstituteRegistration v-if="selected" :institute="selected" @close="selected=null"/>
  </section>
</template>
<style scoped>
.campus-directory{margin:32px 0;text-align:left}.campus-directory p{line-height:1.6}.directory-search{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.directory-search label{width:100%}.directory-search input{flex:1;min-width:140px;padding:12px;border:1px solid #dcd3e9;border-radius:10px;font:inherit}.campus-directory button{padding:12px 18px;border:1px solid #ddd2ed;border-radius:10px;background:#f4eefb;color:#502785;font:inherit;cursor:pointer}.campus-directory button:disabled{opacity:.55;cursor:default}.directory-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(240px,100%),1fr));gap:16px}.directory-cards article{padding:20px;border:1px solid #e7deef;border-radius:16px;background:white}.directory-cards h3{margin:0;font-size:20px}.campus-directory nav{display:flex;align-items:center;gap:16px;margin-top:24px}
</style>
