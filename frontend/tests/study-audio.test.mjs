import test from 'node:test'
import assert from 'node:assert/strict'
import { createStudyAudio } from '../src/study/audio.js'

test('local music starts on play, switches cleanly, and releases media on disposal', async () => {
  const previous = globalThis.Audio, instances = []
  globalThis.Audio = class {
    constructor(src) { this.src = src; this.paused = true; instances.push(this) }
    async play() { this.paused = false }
    pause() { this.paused = true }
    removeAttribute() { this.src = '' }
    load() { this.released = true }
  }
  try {
    const audio = createStudyAudio()
    assert.equal(instances.length, 0)
    assert.equal(await audio.play('music', .25, '/one.mp3'), true)
    assert.equal(instances[0].loop, true)
    assert.equal(instances[0].paused, false)
    audio.volume(.6)
    assert.equal(instances[0].volume, .6)
    await audio.play('music', .25, '/two.mp3')
    assert.equal(instances[0].released, true)
    assert.equal(instances[0].paused, true)
    await audio.dispose()
    assert.equal(instances[1].released, true)
    assert.equal(instances[1].paused, true)
  } finally { globalThis.Audio = previous }
})

test('stopping during loading prevents stale playback from becoming active', async () => {
  const previous = globalThis.Audio
  let finish, media
  globalThis.Audio = class {
    constructor() { media = this }
    play() { return new Promise(resolve => { finish = resolve }) }
    pause() { this.paused = true }
    removeAttribute() {}
    load() {}
  }
  try {
    const audio = createStudyAudio()
    const pending = audio.play('music', .25, '/slow.mp3')
    audio.stop()
    finish()
    assert.equal(await pending, false)
    assert.equal(media.paused, true)
  } finally { globalThis.Audio = previous }
})
