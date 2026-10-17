<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiRequest } from '../api'

interface LearningPath { id: string; title: string; topics: string[]; steps: { title: string; objective: string; activity: string }[] }
const paths = ref<LearningPath[]>([])
const title = ref('')
const topics = ref('')
const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const errorMessage = ref('')
const message = ref('')

async function loadPaths() {
  loading.value = true
  try {
    const response = await apiRequest<{ paths: LearningPath[] }>('/api/learning-paths')
    paths.value = response.paths
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load learning paths.'
  } finally {
    loading.value = false
  }
}

async function createPath() {
  saving.value = true
  errorMessage.value = ''
  const topicList = topics.value.split(',').map((topic) => topic.trim()).filter(Boolean)
  try {
    await apiRequest('/api/learning-paths', {
      method: 'POST', body: JSON.stringify({ title: title.value, topics: topicList }),
    })
    title.value = ''
    topics.value = ''
    message.value = 'Your learning path is saved.'
    await loadPaths()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not create this learning path.'
  } finally {
    saving.value = false
  }
}

async function generatePath() {
  generating.value = true
  errorMessage.value = ''
  const topicList = topics.value.split(',').map((topic) => topic.trim()).filter(Boolean)
  try {
    await apiRequest('/api/ai/learning-path', {
      method: 'POST', body: JSON.stringify({ title: title.value, topics: topicList }),
    })
    title.value = ''
    topics.value = ''
    message.value = 'Your suggested learning path is ready.'
    await loadPaths()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not generate this learning path.'
  } finally {
    generating.value = false
  }
}

onMounted(loadPaths)
</script>

<template>
  <section class="role-page">
    <div class="page-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> SELF-DIRECTED</p><h2>Your next path</h2><p class="page-description">Choose a subject, collect the ideas you want to explore, and make a plan.</p></div></div>
    <q-banner v-if="errorMessage" rounded class="error-banner">{{ errorMessage }}</q-banner>
    <q-banner v-if="message" rounded class="success-banner">{{ message }}</q-banner>
    <q-form class="path-form" @submit.prevent="createPath">
      <label class="field-label" for="path-title">What would you like to learn?</label><q-input id="path-title" v-model="title" outlined dense maxlength="160" placeholder="For example, the basics of climate science" />
      <label class="field-label" for="path-topics">Topics to include</label><q-input id="path-topics" v-model="topics" outlined dense placeholder="Separate topics with commas" />
      <div class="path-form-footer"><span>Each topic becomes a step in your path.</span><div class="path-actions"><q-btn flat no-caps icon="auto_awesome" label="Suggest steps with AI" :loading="generating" @click="generatePath" /><q-btn type="submit" unelevated no-caps class="primary-button" icon="add" label="Save topics" :loading="saving" /></div></div>
    </q-form>
    <div v-if="loading" class="loading-state"><q-spinner-dots size="28px" color="primary" /> Loading paths…</div>
    <div v-else class="path-list">
      <article v-for="path in paths" :key="path.id" class="path-row">
        <div class="path-row-heading"><span class="path-symbol"><q-icon name="route" /></span><strong>{{ path.title }}</strong><span>{{ path.topics.length }} steps</span></div>
        <ol><li v-for="step in path.steps" :key="step.title"><strong>{{ step.title }}</strong><span>{{ step.objective }}</span><small>{{ step.activity }}</small></li><li v-if="!path.steps.length" v-for="topic in path.topics" :key="topic">{{ topic }}</li></ol>
      </article>
      <div v-if="!paths.length" class="empty-inline">Your saved learning paths will appear here.</div>
    </div>
  </section>
</template>