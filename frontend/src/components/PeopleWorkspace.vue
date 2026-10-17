<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { apiRequest } from '../api'

type Role = 'admin' | 'instructor' | 'student'
interface Person { id: string; username: string; display_name: string; role: string }
interface CourseOption { id: string; title: string }

const props = defineProps<{ role: Role }>()
const people = ref<Person[]>([])
const enrolledIds = ref(new Set<string>())
const courses = ref<CourseOption[]>([])
const courseId = ref('')
const selectedStudentId = ref('')
const dialogOpen = ref(false)
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const message = ref('')
const form = ref({ username: '', display_name: '', password: '', role: 'student' as 'student' | 'instructor' })
const title = computed(() => props.role === 'admin' ? 'People' : 'Students')
const availableStudents = computed(() => people.value.filter((person) => person.role === 'student' && !enrolledIds.value.has(person.id)))

async function loadPeople() {
  loading.value = true
  errorMessage.value = ''
  try {
    const endpoint = props.role === 'admin' ? '/api/users' : '/api/users/students'
    const response = await apiRequest<{ users?: Person[]; students?: Person[] }>(endpoint)
    people.value = response.users ?? response.students ?? []
    if (props.role === 'instructor') {
      const courseResponse = await apiRequest<{ courses: CourseOption[] }>('/api/courses')
      courses.value = courseResponse.courses
      if (!courseId.value && courses.value.length) courseId.value = courses.value[0].id
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load people.'
  } finally {
    loading.value = false
  }
}

async function createAccount() {
  saving.value = true
  errorMessage.value = ''
  try {
    await apiRequest('/api/users', { method: 'POST', body: JSON.stringify(form.value) })
    message.value = 'Account created. The user will set a new password at first sign-in.'
    form.value = { username: '', display_name: '', password: '', role: 'student' }
    dialogOpen.value = false
    await loadPeople()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not create this account.'
  } finally {
    saving.value = false
  }
}

async function loadEnrollment() {
  if (props.role !== 'instructor' || !courseId.value) return
  try {
    const response = await apiRequest<{ students: Person[] }>(`/api/courses/${courseId.value}/students`)
    enrolledIds.value = new Set(response.students.map((person) => person.id))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load this course roster.'
  }
}

async function addStudent() {
  if (!courseId.value || !selectedStudentId.value) return
  try {
    await apiRequest(`/api/courses/${courseId.value}/students`, {
      method: 'POST', body: JSON.stringify({ student_id: selectedStudentId.value }),
    })
    selectedStudentId.value = ''
    message.value = 'Student enrolled.'
    await loadEnrollment()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not enroll this student.'
  }
}

async function removeStudent(person: Person) {
  if (!courseId.value) return
  try {
    await apiRequest(`/api/courses/${courseId.value}/students/${person.id}`, { method: 'DELETE' })
    message.value = 'Student removed from this course.'
    await loadEnrollment()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not remove this student.'
  }
}

onMounted(loadPeople)
watch(courseId, loadEnrollment)
</script>

<template>
  <section class="role-page">
    <div class="page-heading">
      <div><p class="eyebrow"><span class="eyebrow-line"></span>{{ role === 'admin' ? 'ACCOUNT MANAGEMENT' : 'COURSE ENROLLMENT' }}</p><h2>{{ title }}</h2><p class="page-description">{{ role === 'admin' ? 'Create and review instructor and student accounts.' : 'Manage student access to your courses.' }}</p></div>
      <q-btn v-if="role === 'admin'" unelevated no-caps class="primary-button" icon="person_add" label="Create account" @click="dialogOpen = true" />
    </div>
    <q-banner v-if="errorMessage" rounded class="error-banner">{{ errorMessage }}</q-banner>
    <q-banner v-if="message" rounded class="success-banner">{{ message }}</q-banner>
    <div v-if="role === 'instructor'" class="enrollment-toolbar">
      <q-select v-model="courseId" outlined dense emit-value map-options label="Course" :options="courses.map((course) => ({ label: course.title, value: course.id }))" />
      <q-select v-model="selectedStudentId" outlined dense emit-value map-options label="Add student" :options="availableStudents.map((person) => ({ label: person.display_name, value: person.id }))" />
      <q-btn unelevated no-caps class="primary-button" icon="person_add" label="Enroll" :disable="!selectedStudentId || !courseId" @click="addStudent" />
    </div>
    <div v-if="loading" class="loading-state"><q-spinner-dots size="28px" color="primary" /> Loading…</div>
    <div v-else-if="!people.length" class="empty-inline">No accounts to show yet.</div>
    <div v-else class="people-list">
      <article v-for="person in people" :key="person.id" class="person-row">
        <q-avatar size="36px" class="person-avatar">{{ person.display_name.slice(0, 1).toUpperCase() }}</q-avatar>
        <div class="person-summary"><strong>{{ person.display_name }}</strong><small>{{ person.username }}</small></div>
        <span class="person-role">{{ role === 'instructor' ? enrolledIds.has(person.id) ? 'Enrolled' : 'Student' : person.role }}</span>
        <q-btn v-if="role === 'instructor' && enrolledIds.has(person.id)" flat round dense icon="person_remove" aria-label="Remove student" @click="removeStudent(person)" />
      </article>
    </div>
    <q-dialog v-model="dialogOpen">
      <q-card class="editor-card">
        <q-card-section class="editor-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> NEW ACCOUNT</p><h2>Create a user</h2></div><q-btn flat round dense icon="close" aria-label="Close" @click="dialogOpen = false" /></q-card-section>
        <q-form class="editor-form" @submit.prevent="createAccount">
          <label class="field-label">Role</label><q-btn-toggle v-model="form.role" unelevated no-caps spread toggle-color="primary" :options="[{ label: 'Student', value: 'student' }, { label: 'Instructor', value: 'instructor' }]" />
          <label class="field-label" for="new-display-name">Display name</label><q-input id="new-display-name" v-model="form.display_name" outlined dense maxlength="120" />
          <label class="field-label" for="new-username">Username</label><q-input id="new-username" v-model="form.username" outlined dense maxlength="80" />
          <label class="field-label" for="new-user-password">Temporary password</label><q-input id="new-user-password" v-model="form.password" outlined dense type="password" hint="At least 8 characters. User must change it on first sign-in." />
          <div class="editor-actions"><q-btn flat no-caps label="Cancel" @click="dialogOpen = false" /><q-btn type="submit" unelevated no-caps class="primary-button" :loading="saving" label="Create account" icon-right="arrow_forward" /></div>
        </q-form>
      </q-card>
    </q-dialog>
  </section>
</template>