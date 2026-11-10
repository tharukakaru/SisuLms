<script setup>
import {computed} from 'vue'
import BrandLogo from '../BrandLogo.vue'
import discoverImg from '../assets/onboarding-discover.png'
import connectImg from '../assets/onboarding-connect.png'
import growImg from '../assets/onboarding-grow.png'

const props = defineProps({
  variant: {type: String, default: 'discover'},
  compact: {type: Boolean, default: false},
})

const scenes = {
  discover: {
    kicker: 'A LITTLE SPARK. A BIGGER WORLD.',
    titleLine1: 'Big dreams.',
    titleLine2: 'Start here.',
    subtitle: 'A place for curious minds, inspiring teachers and all the things you’ll become.',
    image: discoverImg,
    imageAlt: 'SISU mascot and learners exploring new ideas together',
    waveBg: '#604bc6',
    waveText: '#ffffff',
  },
  connect: {
    kicker: 'GOOD PEOPLE. BRIGHT FUTURES.',
    titleLine1: 'Learning is better.',
    titleLine2: 'Together.',
    subtitle: 'Meet your people. Share what you know. Build something brighter together.',
    image: connectImg,
    imageAlt: 'SISU mascot, teachers, and students collaborating around a table',
    waveBg: '#dccbfa',
    waveText: '#56288d',
  },
  grow: {
    kicker: 'YOUR JOURNEY IS ONLY BEGINNING.',
    titleLine1: 'Little steps.',
    titleLine2: 'Limitless you.',
    subtitle: 'Make space for your next chapter. We’ll be here, cheering you on.',
    image: growImg,
    imageAlt: 'SISU mascot climbing stacked books toward a glowing star',
    waveBg: '#472074',
    waveText: '#ffffff',
  },
}

const currentScene = computed(() => scenes[props.variant] || scenes.discover)
</script>

<template>
  <aside
    class="sisu-welcome-panel"
    :class="[`sisu-welcome-${variant}`, { 'sisu-welcome-compact': compact }]"
    :style="{ '--wave-bg': currentScene.waveBg, '--wave-text': currentScene.waveText }"
    aria-label="SISU onboarding story"
  >
    <div class="sisu-welcome-brand">
      <BrandLogo />
      <span class="sisu-welcome-mobile-pill">Learn · Connect · Grow</span>
    </div>

    <div class="sisu-welcome-story">
      <p class="sisu-welcome-kicker">{{ currentScene.kicker }}</p>
      <h2 class="sisu-welcome-heading">
        <span>{{ currentScene.titleLine1 }}</span>
        <span>{{ currentScene.titleLine2 }}</span>
      </h2>
      <p class="sisu-welcome-subtitle">{{ currentScene.subtitle }}</p>
    </div>

    <div class="sisu-welcome-art" aria-hidden="true">
      <img :src="currentScene.image" :alt="currentScene.imageAlt" loading="eager" />
    </div>

    <div class="sisu-welcome-footer">
      <svg
        class="sisu-welcome-wave"
        viewBox="0 0 600 172"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M0,42 C148,-8 292,68 446,32 C514,16 565,6 600,14 L600,172 L0,172 Z"
          fill="var(--wave-bg)"
        />
      </svg>
      <div class="sisu-welcome-promise">
        <strong>More than lessons. A place to belong.</strong>
        <span>Learn  ·  Connect  ·  Grow</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sisu-welcome-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  max-width: 520px;
  height: clamp(520px, calc(100dvh - 32px), 780px);
  min-height: 0;
  background: #ffffff;
  border-radius: 28px;
  overflow: hidden;
  box-sizing: border-box;
  border: 1px solid rgba(86, 40, 141, 0.08);
  box-shadow: 0 20px 50px rgba(25, 24, 46, 0.04);
  user-select: none;
}

.sisu-welcome-brand {
  padding: clamp(16px, 2.4vh, 28px) clamp(24px, 3vw, 38px) 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.sisu-welcome-mobile-pill {
  display: none;
  padding: 6px 12px;
  border-radius: 999px;
  background: #f2f0fc;
  color: #56288d;
  font-family: 'Manrope', sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.sisu-welcome-story {
  padding: clamp(10px, 1.8vh, 20px) clamp(24px, 3vw, 38px) 0;
  display: flex;
  flex-direction: column;
  gap: clamp(6px, 1vh, 12px);
  z-index: 2;
  flex-shrink: 0;
}

.sisu-welcome-kicker {
  margin: 0;
  font-family: 'Manrope', sans-serif;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #56288d;
}

.sisu-welcome-heading {
  margin: 0;
  display: flex;
  flex-direction: column;
  font-family: 'Outfit', 'Manrope', sans-serif;
  font-size: clamp(28px, min(3.2vw, 4.8vh), 44px);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -0.03em;
  color: #56288d;
}

.sisu-welcome-subtitle {
  margin: 0;
  max-width: 420px;
  font-family: 'Manrope', sans-serif;
  font-size: clamp(13px, 1.7vh, 15px);
  font-weight: 700;
  line-height: 1.38;
  color: #56288d;
}

.sisu-welcome-art {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 16px 0;
  margin-top: auto;
  margin-bottom: -10px;
  z-index: 1;
}

.sisu-welcome-art img {
  width: auto;
  max-width: 100%;
  height: 100%;
  max-height: clamp(160px, 34vh, 320px);
  object-fit: contain;
  display: block;
}

.sisu-welcome-footer {
  position: relative;
  width: 100%;
  min-height: clamp(84px, 12.5vh, 120px);
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  padding: clamp(22px, 3.5vh, 36px) clamp(24px, 3vw, 38px) clamp(14px, 2.2vh, 24px);
  box-sizing: border-box;
  z-index: 2;
}

.sisu-welcome-wave {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}

.sisu-welcome-promise {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--wave-text, #ffffff);
}

.sisu-welcome-promise strong {
  font-family: 'Manrope', sans-serif;
  font-size: clamp(13.5px, 1.8vh, 15px);
  font-weight: 700;
  line-height: 1.3;
}

.sisu-welcome-promise span {
  font-family: 'Manrope', sans-serif;
  font-size: 11.5px;
  font-weight: 500;
  letter-spacing: 0.03em;
  opacity: 0.92;
}

:global(.entry-dark .sisu-welcome-panel),
:global([data-student-theme='dark'] .sisu-welcome-panel) {
  background: #171429 !important;
  border-color: rgba(164, 132, 233, 0.18) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45) !important;
}

:global(.entry-dark .sisu-welcome-kicker),
:global([data-student-theme='dark'] .sisu-welcome-kicker) {
  color: #c4b5fd !important;
}

:global(.entry-dark .sisu-welcome-heading),
:global([data-student-theme='dark'] .sisu-welcome-heading) {
  color: #ffffff !important;
}

:global(.entry-dark .sisu-welcome-subtitle),
:global([data-student-theme='dark'] .sisu-welcome-subtitle) {
  color: #d1c7e8 !important;
}

:global(.entry-dark .sisu-welcome-mobile-pill),
:global([data-student-theme='dark'] .sisu-welcome-mobile-pill) {
  background: #25203b !important;
  color: #c4b5fd !important;
}

:global(.entry-dark .sisu-welcome-panel.sisu-welcome-discover),
:global([data-student-theme='dark'] .sisu-welcome-panel.sisu-welcome-discover) {
  --wave-bg: #4a34a8 !important;
  --wave-text: #ffffff !important;
}

:global(.entry-dark .sisu-welcome-panel.sisu-welcome-connect),
:global([data-student-theme='dark'] .sisu-welcome-panel.sisu-welcome-connect) {
  --wave-bg: #321c56 !important;
  --wave-text: #e9dffb !important;
}

:global(.entry-dark .sisu-welcome-panel.sisu-welcome-grow),
:global([data-student-theme='dark'] .sisu-welcome-panel.sisu-welcome-grow) {
  --wave-bg: #3b1766 !important;
  --wave-text: #ffffff !important;
}

@media (max-width: 1040px) {
  .sisu-welcome-panel {
    max-width: 100%;
    height: auto;
    min-height: auto;
    border-radius: 26px;
  }

  .sisu-welcome-brand {
    padding: 22px 26px 0;
  }

  .sisu-welcome-story {
    padding: 16px 26px 0;
    gap: 8px;
  }

  .sisu-welcome-heading {
    font-size: clamp(26px, 5vw, 36px);
  }

  .sisu-welcome-subtitle {
    font-size: 14px;
  }

  .sisu-welcome-art {
    padding: 6px 16px 0;
    margin-bottom: -10px;
  }

  .sisu-welcome-art img {
    max-height: 210px;
  }

  .sisu-welcome-footer {
    min-height: 104px;
    padding: 30px 26px 20px;
  }
}

@media (max-width: 640px) {
  .sisu-welcome-panel {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 104px;
    grid-template-areas:
      'brand brand'
      'story art';
    align-items: center;
    border-radius: 22px;
    padding: 0;
    box-shadow: 0 8px 24px rgba(25, 24, 46, 0.04);
  }

  .sisu-welcome-brand {
    grid-area: brand;
    padding: 14px 18px 12px;
    border-bottom: 1px solid rgba(86, 40, 141, 0.08);
  }

  .sisu-welcome-mobile-pill {
    display: inline-flex;
    align-items: center;
  }

  .sisu-welcome-story {
    grid-area: story;
    padding: 14px 8px 16px 18px;
    gap: 4px;
  }

  .sisu-welcome-kicker {
    font-size: 9.5px;
    letter-spacing: 0.12em;
  }

  .sisu-welcome-heading {
    font-size: 20px;
    line-height: 1.15;
  }

  .sisu-welcome-subtitle {
    font-size: 12px;
    font-weight: 500;
    line-height: 1.38;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .sisu-welcome-art {
    grid-area: art;
    padding: 8px 12px 8px 0;
    margin: 0;
  }

  .sisu-welcome-art img {
    max-width: 96px;
    max-height: 86px;
  }

  .sisu-welcome-footer {
    display: none;
  }
}

@media (max-width: 380px) {
  .sisu-welcome-panel {
    grid-template-columns: minmax(0, 1fr) 84px;
  }

  .sisu-welcome-mobile-pill {
    font-size: 10px;
    padding: 5px 9px;
  }

  .sisu-welcome-heading {
    font-size: 18px;
  }
}
</style>

