<script setup>
import {ref,onMounted} from 'vue'
import OnboardingWelcomePanel from './OnboardingWelcomePanel.vue'
import InstituteJoinPicker from './InstituteJoinPicker.vue'
import SubscriptionBilling from './SubscriptionBilling.vue'
const joinMode=ref('')
const props=defineProps({role:String});const emit=defineEmits(['changed']);const panel=ref(null)
onMounted(()=>panel.value?.focus())
</script>
<template>
  <main class="provider-gate">
    <div class="provider-gate-split">
      <OnboardingWelcomePanel variant="connect" />

      <section ref="panel" class="subscription-overlay" tabindex="-1" aria-labelledby="gate-title">
        <a class="sisu-back-link" href="/api/method/logout">← Back to sign in</a>
        <h1 id="gate-title">Welcome to your {{role==='Teacher'?'teacher':'institute'}} workspace</h1>
        <p class="provider-gate-lead">{{role==='Teacher'?'Choose how you want to begin. Manage your own classes with an individual plan, or request access to an institute’s teaching workspace.':'Choose a plan for your institute to continue.'}}</p>

        <nav v-if="role==='Teacher'" class="join-links" aria-label="Teacher workspace options">
          <button
            type="button"
            class="join-pill join-pill-primary"
            :aria-pressed="!joinMode"
            @click="joinMode=''"
          >
            <div>
              <strong>Continue as individual teacher</strong>
              <span>Teach independently — your classes, students and personal subscription.</span>
            </div>
            <i aria-hidden="true">→</i>
          </button>

          <button
            type="button"
            class="join-pill join-pill-secondary"
            :aria-pressed="joinMode==='Existing teacher confirmation'"
            @click="joinMode='Existing teacher confirmation'"
          >
            <div>
              <strong>Join your registered institute</strong>
              <span>I teach at an institute — ask your institute to confirm your teaching access.</span>
            </div>
            <i aria-hidden="true">→</i>
          </button>

          <button
            type="button"
            class="join-pill join-pill-quiet"
            :aria-pressed="joinMode==='New application'"
            @click="joinMode='New application'"
          >
            <div>
              <strong>Apply to an institute</strong>
              <span>Find an institute and apply to join a new teaching community.</span>
            </div>
            <i aria-hidden="true">→</i>
          </button>
        </nav>

        <div class="provider-gate-content">
          <InstituteJoinPicker v-if="joinMode" :key="joinMode" :purpose="joinMode" @back="joinMode=''"/>
          <SubscriptionBilling v-else standalone @changed="emit('changed')"/>
        </div>
      </section>
    </div>
  </main>
</template>
<style scoped>
.provider-gate {
  min-height: 100vh;
  min-height: 100dvh;
  background: #ffffff;
  color: #19182e;
  padding: clamp(16px, 2vw, 24px);
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.provider-gate-split {
  display: grid;
  grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
  gap: clamp(20px, 2.8vw, 40px);
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: center;
}

.subscription-overlay {
  position: relative;
  width: 100%;
  max-width: 620px;
  background: #ffffff;
  border-radius: 24px;
  padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  box-sizing: border-box;
}

.subscription-overlay:focus {
  outline: none;
}

.sisu-back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: clamp(8px, 1.2vh, 12px);
  font-size: 12.5px;
  font-weight: 500;
  color: #56288d;
  text-decoration: none;
}

.sisu-back-link:hover {
  text-decoration: underline;
}

.subscription-overlay > h1 {
  margin: 0 0 clamp(4px, 0.7vh, 8px);
  font: 800 clamp(22px, 3vh, 30px)/1.15 'Manrope', sans-serif;
  letter-spacing: -0.03em;
  color: #19182e;
}

.provider-gate-lead {
  margin: 0 0 clamp(12px, 1.8vh, 18px);
  font-size: 13.5px;
  color: #787788;
  line-height: 1.45;
}

.join-links {
  display: grid;
  gap: clamp(8px, 1.2vh, 12px);
  margin: clamp(10px, 1.6vh, 16px) 0;
}

.join-links button.join-pill {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 100%;
  min-height: clamp(44px, 5.8vh, 52px);
  padding: clamp(10px, 1.5vh, 14px) 20px;
  border-radius: 24px;
  text-align: left;
  text-decoration: none;
  font: inherit;
  cursor: pointer;
  box-sizing: border-box;
  transition: transform 0.12s ease, border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.join-links button.join-pill > div {
  display: grid;
  gap: 4px;
}

.join-links strong {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.35;
}

.join-links span {
  font-size: 12px;
  line-height: 1.4;
  opacity: 0.88;
}

.join-links i {
  font-style: normal;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

.join-pill-primary {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
}

.join-pill-primary span {
  color: rgba(255, 255, 255, 0.84);
}

.join-pill-secondary {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
}

.join-pill-secondary span {
  color: #787788;
}

.join-pill-secondary i {
  color: #56288d;
}

.join-pill-quiet {
  background: #ffffff;
  border: 1px solid #e9e8ef;
  color: #19182e;
}

.join-pill-quiet span {
  color: #787788;
}

.join-pill-quiet i {
  color: #56288d;
}

.join-links button[aria-pressed='true'] {
  box-shadow: 0 0 0 2px #6c6aee;
}

.join-links button:focus-visible {
  outline: 3px solid #b9b5fa;
  outline-offset: 3px;
}

.provider-gate-content {
  margin-top: 16px;
}

.subscription-overlay :deep(.billing-standalone) {
  min-height: 0;
  padding: 0;
}

.subscription-overlay :deep(.billing-page) {
  max-width: 100%;
}

@media (max-width: 1040px) {
  .provider-gate-split {
    grid-template-columns: minmax(0, 1fr);
    max-width: 680px;
    gap: 20px;
  }

  .subscription-overlay {
    padding: 24px 20px;
  }
}

@media (max-width: 640px) {
  .provider-gate {
    justify-content: flex-start;
    padding: 12px 12px 24px;
  }

  .provider-gate-split {
    gap: 12px;
  }

  .subscription-overlay {
    padding: 20px;
    border-radius: 24px;
  }

  .sisu-back-link {
    margin-bottom: 12px;
  }

  .subscription-overlay > h1 {
    font-size: 28px;
    line-height: 1.18;
    margin: 0 0 8px;
  }

  .provider-gate-lead {
    font-size: 15px;
    margin: 0 0 14px;
  }

  .join-links {
    gap: 10px;
    margin: 14px 0 18px;
  }

  .join-links button.join-pill {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
    gap: 10px;
  }
}

@media (max-width: 380px) {
  .subscription-overlay {
    padding: 16px;
  }

  .subscription-overlay > h1 {
    font-size: 24px;
  }
}
</style>
