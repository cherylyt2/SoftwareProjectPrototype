<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiRequest } from '../api'

type Role = 'admin' | 'instructor' | 'student'
interface Card { card_id: string; title: string; energy_cost: number; value: number; card_type: 'Attack' | 'Defend' | 'Curse'; correct_choice?: boolean }
interface Stage {
  course_id: string; topic_name: string; floor: number; enemy_name: string; enemy_max_hp: number
  turn_1_enemy_intent: string; turn_1_enemy_damage: number; turn_2_enemy_intent: string; turn_2_enemy_damage: number
  turn_1_hand: Card[]; turn_2_hand: Card[]; title: string; incident_brief: string; quick_reference: string
}

const PLAYER_MAX_HP = 40
const TURN_ENERGY = 3

const props = defineProps<{ role: Role }>()
const stages = ref<Stage[]>([])
const loading = ref(false)
const errorMessage = ref('')
const moduleSelected = ref(false)
const active = ref<Stage | null>(null)
const turn = ref<1 | 2>(1)
const playerHp = ref(PLAYER_MAX_HP)
const enemyHp = ref(0)
const block = ref(0)
const energy = ref(TURN_ENERGY)
const played = ref<string[]>([])
const outcome = ref<'' | 'won' | 'lost'>('')
const log = ref<string[]>([])

const hand = computed(() => (active.value ? (turn.value === 1 ? active.value.turn_1_hand : active.value.turn_2_hand) : []))
const intent = computed(() => (active.value ? (turn.value === 1 ? active.value.turn_1_enemy_intent : active.value.turn_2_enemy_intent) : ''))
const intentDamage = computed(() => (active.value ? (turn.value === 1 ? active.value.turn_1_enemy_damage : active.value.turn_2_enemy_damage) : 0))
const resultText = computed(() => {
  if (outcome.value === 'won') return 'The bug is defeated. Floor cleared.'
  return playerHp.value <= 0 ? 'You were overwhelmed by the bug.' : 'The bug survived both turns.'
})

function paragraphs(text: string): string[] {
  return text.split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean)
}

function bullets(text: string): string[] {
  return text.split('\n').map((line) => line.replace(/^-\s*/, '').trim()).filter(Boolean)
}

function cardEffect(card: Card): string {
  const label = { Attack: 'damage', Defend: 'block', Curse: 'self-damage' }[card.card_type]
  return `${card.card_type} · ${card.energy_cost} energy · ${card.value} ${label}`
}

function studentCardSummary(card: Card): string {
  return `${card.card_type} · ${card.energy_cost} energy`
}

function cardDescription(card: Card): string {
  const descriptions: Record<string, string> = {
    'Testable Requirement Rewrite': 'Turn a vague request into a specific, verifiable requirement.',
    'MoSCoW Prioritization': 'Sort requests into Must, Should, Could, and Won’t to control scope.',
    'Quick Patch': 'A fast change may ease a symptom without fixing its root cause.',
    'Rubber Duck': 'Explain the problem aloud to clarify your reasoning.',
    'Gold Plating': 'Adding unrequested features expands scope instead of meeting priorities.',
    'Env File and Gitignore': 'Keep development secrets in .env and exclude that file from version control.',
    'Platform Environment Variables': 'Store production secrets in the hosting platform, outside frontend code.',
    'Hardcoded Secret': 'A secret in source code can leak to the repository or browser.',
    'Integration Test': 'Check that combined modules agree on their interfaces and data.',
    'Regression Test Suite': 'Rerun existing tests to catch previously working features that broke.',
    'Skip Tests and Ship': 'Skipping verification can send defects straight to production.',
    'Monitoring and Alerting': 'Watch service metrics and notify the team when they cross thresholds.',
    'Canary Deployment': 'Release to a small portion first, then expand when results look healthy.',
    'Big Bang Deploy': 'Replace the whole release at once, increasing downtime and rollback risk.',
  }
  return descriptions[card.title] ?? 'Use this tool to respond to the incident.'
}

function turnsOf(stage: Stage) {
  return [
    { turn: 1, intent: stage.turn_1_enemy_intent, damage: stage.turn_1_enemy_damage, hand: stage.turn_1_hand },
    { turn: 2, intent: stage.turn_2_enemy_intent, damage: stage.turn_2_enemy_damage, hand: stage.turn_2_hand },
  ]
}

async function loadStages() {
  loading.value = true
  errorMessage.value = ''
  try {
    stages.value = (await apiRequest<{ stages: Stage[] }>('/api/stages')).stages
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load the battle floors.'
  } finally {
    loading.value = false
  }
}

function startBattle(stage: Stage) {
  active.value = stage
  turn.value = 1
  playerHp.value = PLAYER_MAX_HP
  enemyHp.value = stage.enemy_max_hp
  block.value = 0
  energy.value = TURN_ENERGY
  played.value = []
  outcome.value = ''
  log.value = []
}

function canPlay(card: Card): boolean {
  return !outcome.value && !played.value.includes(card.card_id) && card.energy_cost <= energy.value
}

function playCard(card: Card) {
  if (!canPlay(card)) return
  energy.value -= card.energy_cost
  played.value.push(card.card_id)
  if (card.card_type === 'Attack') {
    enemyHp.value = Math.max(0, enemyHp.value - card.value)
    log.value.push(`${card.title} strikes the bug.`)
  } else if (card.card_type === 'Defend') {
    block.value += card.value
    log.value.push(`${card.title} raises a guard.`)
  } else {
    playerHp.value = Math.max(0, playerHp.value - card.value)
    log.value.push(`${card.title} weakens you.`)
  }
  if (enemyHp.value <= 0) outcome.value = 'won'
  else if (playerHp.value <= 0) outcome.value = 'lost'
}

function endTurn() {
  if (!active.value || outcome.value) return
  const damage = Math.max(0, intentDamage.value - block.value)
  playerHp.value = Math.max(0, playerHp.value - damage)
  log.value.push(`${active.value.enemy_name} attacks through your guard.`)
  if (playerHp.value <= 0 || turn.value === 2) {
    outcome.value = 'lost'
    return
  }
  turn.value = 2
  energy.value = TURN_ENERGY
  block.value = 0
  played.value = []
}

onMounted(loadStages)
</script>

<template>
  <section class="role-page">
    <div class="page-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> SOFTWARE DEVELOPMENT LIFECYCLE</p><h2>Code Spire</h2><p class="page-description">Climb four floors. Each bug lasts two turns, so choose the right tool.</p></div></div>
    <q-banner v-if="errorMessage" rounded class="error-banner">{{ errorMessage }}</q-banner>
    <div v-if="loading" class="loading-state"><q-spinner-dots size="28px" color="primary" /> Loading floors…</div>

    <template v-else-if="!moduleSelected">
      <div class="tower-module-list">
        <article class="tower-module">
          <span class="tower-module-icon"><q-icon name="terminal" size="23px" /></span>
          <div class="tower-floor-copy"><strong>Software Development Lifecycle</strong><small>4 floors · Requirements through deployment and maintenance</small></div>
          <q-btn unelevated no-caps class="primary-button" label="Open module" icon-right="arrow_forward" @click="moduleSelected = true" />
        </article>
      </div>
    </template>

    <template v-else-if="props.role === 'student'">
      <div v-if="!active" class="tower-list">
        <div class="tower-battle-top"><div><p class="eyebrow"><span class="eyebrow-line"></span> SOFTWARE DEVELOPMENT LIFECYCLE</p><h3>Choose a floor</h3></div><q-btn flat no-caps icon="west" label="Back to modules" @click="moduleSelected = false" /></div>
        <article v-for="stage in stages" :key="stage.floor" class="tower-floor">
          <span class="tower-badge">Floor {{ stage.floor }}</span>
          <div class="tower-floor-copy"><strong>{{ stage.topic_name }}</strong><small>{{ stage.enemy_name }} · {{ stage.enemy_max_hp }} HP</small></div>
          <q-btn unelevated no-caps class="primary-button" :label="`Enter floor ${stage.floor}`" @click="startBattle(stage)" />
        </article>
      </div>

      <div v-else class="tower-battle">
        <div class="tower-battle-top"><div><span class="tower-badge">Floor {{ active.floor }}</span><h3>{{ active.title }}</h3></div><q-btn flat no-caps icon="west" label="Back to floors" @click="active = null" /></div>
        <p v-for="part in paragraphs(active.incident_brief)" :key="part" class="tower-text">{{ part }}</p>
        <div class="tower-stats">
          <div><span>You</span><strong class="player-hp">{{ playerHp }} / 40 HP</strong><q-linear-progress :value="playerHp / 40" color="positive" /></div>
          <div><span>{{ active.enemy_name }}</span><strong class="enemy-hp">{{ enemyHp }} / {{ active.enemy_max_hp }} HP</strong><q-linear-progress :value="enemyHp / active.enemy_max_hp" color="negative" /></div>
          <div><span>Turn {{ turn }} of 2</span><strong class="energy">{{ energy }} / 3 energy</strong><small>{{ block > 0 ? 'Guard active' : 'No guard' }}</small></div>
        </div>
        <p v-if="!outcome" class="tower-intent">Enemy intent: {{ intent }}</p>
        <div class="tower-hand">
          <button v-for="card in hand" :key="card.card_id" type="button" class="hand-card" :class="[card.card_type.toLowerCase(), { used: played.includes(card.card_id) }]" :disabled="!canPlay(card)" :title="cardDescription(card)" :aria-label="`${card.title}: ${cardDescription(card)} ${card.energy_cost} energy`" @click="playCard(card)">
            <strong>{{ card.title }}</strong><small>{{ studentCardSummary(card) }}</small>
          </button>
        </div>
        <div v-if="!outcome" class="tower-actions"><q-btn unelevated no-caps class="primary-button end-turn" label="End turn" @click="endTurn" /></div>
        <ul v-if="log.length" class="tower-log"><li v-for="(entry, index) in log" :key="index">{{ entry }}</li></ul>
        <div v-if="outcome" class="tower-result" :class="outcome">
          <h4>{{ resultText }}</h4>
          <ul><li v-for="line in bullets(active.quick_reference)" :key="line">{{ line }}</li></ul>
          <div class="tower-actions"><q-btn flat no-caps label="Try again" @click="startBattle(active)" /><q-btn unelevated no-caps class="primary-button" label="Back to floors" @click="active = null" /></div>
        </div>
      </div>
    </template>

    <div v-else class="tower-list">
      <div class="tower-battle-top"><div><p class="eyebrow"><span class="eyebrow-line"></span> SOFTWARE DEVELOPMENT LIFECYCLE</p><h3>Four floors</h3></div><q-btn flat no-caps icon="west" label="Back to modules" @click="moduleSelected = false" /></div>
      <article v-for="stage in stages" :key="stage.floor" class="tower-stage">
        <div class="tower-battle-top"><div><span class="tower-badge">Floor {{ stage.floor }}</span><h3>{{ stage.title }}</h3></div><small>{{ stage.enemy_name }} · {{ stage.enemy_max_hp }} HP</small></div>
        <p v-for="part in paragraphs(stage.incident_brief)" :key="part" class="tower-text">{{ part }}</p>
        <div v-for="item in turnsOf(stage)" :key="item.turn" class="tower-turn">
          <p class="tower-intent">Turn {{ item.turn }}: {{ item.intent }} ({{ item.damage }} damage)</p>
          <ul class="tower-cards"><li v-for="card in item.hand" :key="card.card_id" :class="{ correct: card.correct_choice }" :title="cardDescription(card)"><strong>{{ card.title }}</strong> <small>{{ cardEffect(card) }}</small><span v-if="card.correct_choice" class="correct-tag">Correct</span></li></ul>
        </div>
        <ul class="tower-reference"><li v-for="line in bullets(stage.quick_reference)" :key="line">{{ line }}</li></ul>
      </article>
    </div>
  </section>
</template>
