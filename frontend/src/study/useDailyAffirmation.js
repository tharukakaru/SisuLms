import {computed, ref, onMounted, onBeforeUnmount} from 'vue'
import affirmations from './affirmations.json'
import {dailyAffirmationIndex} from './dailyAffirmation.js'

export function useDailyAffirmation() {
  const index = ref(dailyAffirmationIndex())
  const update = () => { index.value = dailyAffirmationIndex() }
  let timer
  onMounted(() => {
    timer = setInterval(update, 30000)
    window.addEventListener('focus', update)
    document.addEventListener('visibilitychange', update)
  })
  onBeforeUnmount(() => {
    clearInterval(timer)
    window.removeEventListener('focus', update)
    document.removeEventListener('visibilitychange', update)
  })
  return computed(() => ({day:index.value + 1, text:affirmations[index.value]}))
}
