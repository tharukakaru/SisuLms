<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
const props=defineProps({provider:Boolean})
const chosen=computed(()=>institutes.value.find(i=>i.institute===selected.value))
const institutes=ref([]),selected=ref(''),loading=ref(true),saving=ref(false),error=ref('')
async function load(){loading.value=true;error.value='';try{const data=await request('campus_context','choices',{},'GET');institutes.value=data.institutes;selected.value=data.selected||''}catch(e){error.value=e.message}finally{loading.value=false}}
async function change(){saving.value=true;error.value='';try{await request('campus_context',selected.value?'select':'clear',selected.value?{institute:selected.value}:{});window.location.assign('/campus')}catch(e){error.value=e.message;saving.value=false}}
onMounted(()=>{load();window.addEventListener('sisu-memberships',load)})
onBeforeUnmount(()=>window.removeEventListener('sisu-memberships',load))
</script>
<template>
  <section class="campus-switcher" :class="{provider}" :aria-label="provider?'Your teaching workspaces':'Your institutes'">
    <div class="campus-switcher-head">
      <small>{{provider?"YOUR TEACHING SPACE":"YOUR LEARNING SPACE"}}</small>
      <h2>{{provider?"Choose your teaching workspace":"Choose your institute"}}</h2>
      <p>{{provider?"Open a workspace where you have an active role, or explore institutes.":"Choose a workspace and role. Access and permissions stay specific to that workspace."}}</p>
    </div>

    <p v-if="loading" class="campus-switcher-status" role="status">Loading your institutes…</p>

    <form v-else class="campus-switcher-form" @submit.prevent="change">
      <div class="campus-choice-cards" role="group" :aria-label="provider?'Workspace choices':'Institute choices'">
        <button
          v-for="item in institutes"
          :key="item.institute"
          type="button"
          class="campus-choice-card"
          :class="{active:selected===item.institute}"
          :aria-pressed="selected===item.institute"
          :disabled="saving"
          @click="selected=item.institute"
        >
          <div>
            <strong>{{item.title}}</strong>
            <span>{{item.role || 'Active membership'}}{{item.student_number ? ` · ID: ${item.student_number}` : ''}}</span>
          </div>
          <i aria-hidden="true">{{selected===item.institute ? '✓' : '→'}}</i>
        </button>

        <button
          type="button"
          class="campus-choice-card"
          :class="{active:selected===''}"
          :aria-pressed="selected===''"
          :disabled="saving"
          @click="selected=''"
        >
          <div>
            <strong>{{provider ? 'My teaching workspace' : 'Personal Student account'}}</strong>
            <span>{{provider ? 'Explore institutes — no institute workspace selected.' : 'Your classes, student profile and learning tools.'}}</span>
          </div>
          <i aria-hidden="true">{{selected==='' ? '✓' : '→'}}</i>
        </button>
      </div>

      <label for="campus-choice" class="campus-select-label">
        <span>{{provider?"Teaching workspace":"Institute"}}</span>
        <select id="campus-choice" v-model="selected" :disabled="saving">
          <option value="">{{provider?"Explore institutes — no workspace selected":"None — overall dashboard"}}</option>
          <option v-for="item in institutes" :key="item.institute" :value="item.institute">{{item.title}} · {{item.student_number||item.role}}</option>
        </select>
      </label>

      <p v-if="chosen?.student_number" class="campus-student-id">Your student ID: <strong>{{chosen.student_number}}</strong></p>

      <button type="submit" class="button primary campus-submit-pill" :disabled="saving">
        <span>{{saving?'Opening…':provider?'Open workspace':'Open campus'}}</span>
        <span aria-hidden="true">→</span>
      </button>
    </form>

    <p v-if="!loading&&!error&&!institutes.length" class="campus-empty-note">{{provider?"Your approved teaching workspaces will appear here.":"You haven’t joined an institute yet. Your registered institutes will appear here."}}</p>

    <div v-if="error" class="campus-error-box" role="alert">
      <p>{{error}}</p>
      <button type="button" class="button subtle campus-retry-pill" :disabled="saving" @click="load">Try again →</button>
    </div>
  </section>
</template>
<style scoped>
.campus-switcher {
  padding: 28px 32px;
  margin: 16px 0;
  border: 1px solid #e9e8ef;
  border-radius: 28px;
  background: #ffffff;
  color: #19182e;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-sizing: border-box;
}

.campus-switcher.provider {
  max-width: 960px;
  margin: 24px auto;
  padding: clamp(24px, 3.2vw, 36px);
  box-shadow: 0 16px 44px rgba(25, 24, 46, 0.05);
}

.campus-switcher-head small {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: #56288d;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.campus-switcher-head h2 {
  font-size: clamp(24px, 2.6vw, 32px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #19182e;
  margin: 0 0 8px;
}

.campus-switcher-head p {
  font-size: 15px;
  color: #787788;
  line-height: 1.5;
  margin: 0;
}

.campus-switcher-form {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.campus-choice-cards {
  display: grid;
  gap: 12px;
}

.campus-choice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding: 20px 24px;
  border-radius: 20px;
  background: #fcfcfe;
  border: 1px solid #e9e8ef;
  color: #19182e;
  text-align: left;
  font: inherit;
  cursor: pointer;
  box-sizing: border-box;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.campus-choice-card:hover:not(:disabled) {
  border-color: #56288d;
}

.campus-choice-card.active {
  background: #f5f2fc;
  border-color: #56288d;
}

.campus-choice-card > div {
  display: grid;
  gap: 6px;
}

.campus-choice-card strong {
  font-size: 18px;
  font-weight: 800;
  color: #19182e;
  line-height: 1.3;
}

.campus-choice-card span {
  font-size: 14px;
  color: #787788;
  line-height: 1.4;
}

.campus-choice-card i {
  font-style: normal;
  font-size: 16px;
  font-weight: 700;
  color: #56288d;
}

.campus-select-label {
  display: grid;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #19182e;
}

.campus-switcher select {
  min-height: 50px;
  padding: 13px 14px;
  border: 1px solid #e9e8ef;
  border-radius: 13px;
  background: #fcfcfe;
  color: #19182e;
  width: 100%;
  font: 400 14px 'Manrope', sans-serif;
  box-sizing: border-box;
}

.campus-student-id {
  margin: 0;
  font-size: 13px;
  color: #56288d;
}

.campus-submit-pill,
.campus-retry-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: 54px;
  padding: 12px 24px;
  border-radius: 27px;
  font: 700 14px 'Manrope', sans-serif;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.campus-submit-pill {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(86, 40, 141, 0.16);
}

.campus-submit-pill:hover:not(:disabled) {
  background: #472074;
}

.campus-retry-pill {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
  margin-top: 8px;
}

.campus-empty-note,
.campus-switcher-status {
  margin: 14px 0 0;
  font-size: 13px;
  color: #787788;
}

.campus-error-box {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 13px;
}

.campus-switcher :is(select, button):focus-visible {
  outline: 3px solid #b9b5fa;
  outline-offset: 2px;
}

@media (max-width: 640px) {
  .campus-switcher,
  .campus-switcher.provider {
    margin: 10px 0;
    padding: 20px;
    border-radius: 24px;
  }

  .campus-switcher-head h2 {
    font-size: 28px;
    line-height: 1.18;
  }

  .campus-switcher-head p {
    font-size: 15px;
    line-height: 1.5;
  }

  .campus-switcher-form {
    gap: 12px;
    margin-top: 14px;
  }

  .campus-choice-cards {
    gap: 10px;
  }

  .campus-choice-card {
    padding: 20px 16px;
    border-radius: 20px;
    gap: 12px;
  }

  .campus-choice-card strong {
    font-size: 20px;
    line-height: 1.35;
  }

  .campus-choice-card span {
    font-size: 14px;
    line-height: 1.42;
  }

  .campus-switcher select {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
  }

  .campus-submit-pill,
  .campus-retry-pill {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}

@media (max-width: 380px) {
  .campus-switcher,
  .campus-switcher.provider {
    padding: 16px;
  }

  .campus-switcher-head h2 {
    font-size: 24px;
  }

  .campus-choice-card strong {
    font-size: 18px;
  }
}
</style>
