<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { apiRequest } from '../api'

type Role = 'admin' | 'instructor' | 'student'
interface Question { key: string; prompt: string; answer: string }
interface Module { key: string; title: string; content?: string; activities?: { type: string; questions?: Question[] }[] }
interface Course {
  id: string; title: string; description: string; is_open: boolean; revision: number
  revision_id: string | null; content: { modules?: Module[]; levels?: { modules?: Module[] }[] }
  instructor: { display_name: string }
}
interface Student { id: string; display_name: string; username: string }
interface Attempt { id: string; module_key: string; score: number; revision_id: string; submitted_at: string }
interface DraftModule { key: string; title: string; content: string; prompt: string; answer: string }

const props = defineProps<{ role: Role; activeSection: string }>()
const courses = ref<Course[]>([])
const selectedCourse = ref<Course | null>(null)
const attempts = ref<Attempt[]>([])
const enrolledStudents = ref<Student[]>([])
const allStudents = ref<Student[]>([])
const selectedStudentId = ref('')
const answers = ref<Record<string, Record<string, string>>>({})
const message = ref('')
const errorMessage = ref('')
const loading = ref(false)
const dialogOpen = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)
const draft = ref({ title: '', description: '' })
const draftModules = ref<DraftModule[]>([])
const aiLoading = ref(false)
const uploadLoading = ref(false)
const sourceFile = ref<File | null>(null)
const aiForm = ref({ topic: '', level: '', requirements: '', teaching_content: '' })

function moduleList(course: Course): Module[] {
  return [
    ...(course.content?.modules ?? []),
    ...(course.content?.levels ?? []).flatMap((level) => level.modules ?? []),
  ]
}

function questionsFor(module: Module): Question[] {
  return (module.activities ?? []).filter((activity) => activity.type === 'quiz').flatMap((activity) => activity.questions ?? [])
}

function setAnswer(moduleKey: string, questionKey: string, value: string) {
  answers.value[moduleKey] ??= {}
  answers.value[moduleKey][questionKey] = value
}

async function loadCourses() {
  if (!['overview', 'courses', 'scores'].includes(props.activeSection)) return
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await apiRequest<{ courses: Course[] }>('/api/courses')
    courses.value = response.courses
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load courses.'
  } finally {
    loading.value = false
  }
}

async function openCourse(course: Course) {
  try {
    const response = await apiRequest<{ course: Course }>(`/api/courses/${course.id}`)
    selectedCourse.value = response.course
    const history = await apiRequest<{ attempts: Attempt[] }>(`/api/courses/${course.id}/attempts`)
    attempts.value = history.attempts
    if (props.role !== 'student') await loadRoster(response.course.id)
    answers.value = {}
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not open this course.'
  }
}

async function loadRoster(courseId: string) {
  const [roster, directory] = await Promise.all([
    apiRequest<{ students: Student[] }>(`/api/courses/${courseId}/students`),
    apiRequest<{ students: Student[] }>('/api/users/students'),
  ])
  enrolledStudents.value = roster.students
  allStudents.value = directory.students
}

async function enrollStudent() {
  if (!selectedCourse.value || !selectedStudentId.value) return
  try {
    await apiRequest(`/api/courses/${selectedCourse.value.id}/students`, {
      method: 'POST', body: JSON.stringify({ student_id: selectedStudentId.value }),
    })
    selectedStudentId.value = ''
    await loadRoster(selectedCourse.value.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not enroll this student.'
  }
}

async function removeStudent(student: Student) {
  if (!selectedCourse.value) return
  try {
    await apiRequest(`/api/courses/${selectedCourse.value.id}/students/${student.id}`, { method: 'DELETE' })
    await loadRoster(selectedCourse.value.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not remove this student.'
  }
}

function startCreate() {
  editingId.value = null
  draft.value = { title: '', description: '' }
  draftModules.value = [{ key: crypto.randomUUID(), title: '', content: '', prompt: '', answer: '' }]
  aiForm.value = { topic: '', level: '', requirements: '', teaching_content: '' }
  sourceFile.value = null
  dialogOpen.value = true
}

function addModule() {
  draftModules.value.push({ key: crypto.randomUUID(), title: '', content: '', prompt: '', answer: '' })
}

function startEdit(course: Course) {
  editingId.value = course.id
  draft.value = { title: course.title, description: course.description }
  draftModules.value = moduleList(course).map((module) => {
    const question = questionsFor(module)[0]
    return { key: module.key, title: module.title, content: module.content ?? '', prompt: question?.prompt ?? '', answer: question?.answer ?? '' }
  })
  if (!draftModules.value.length) draftModules.value.push({ key: crypto.randomUUID(), title: '', content: '', prompt: '', answer: '' })
  aiForm.value = { topic: course.title, level: '', requirements: '', teaching_content: '' }
  dialogOpen.value = true
}

function serializeModules() {
  return draftModules.value.filter((module) => module.title.trim()).map((module) => ({
    key: module.key,
    title: module.title.trim(),
    content: module.content.trim(),
    activities: module.prompt.trim() && module.answer.trim() ? [{
      type: 'quiz',
      questions: [{ key: 'question-1', prompt: module.prompt.trim(), answer: module.answer.trim() }],
    }] : [],
  }))
}

async function generateCourseDraft() {
  aiLoading.value = true
  errorMessage.value = ''
  try {
    const response = await apiRequest<{ draft: { title: string; description: string; levels: { modules: Module[] }[] } }>(
      '/api/ai/course-draft', { method: 'POST', body: JSON.stringify(aiForm.value) },
    )
    draft.value = { title: response.draft.title, description: response.draft.description }
    draftModules.value = response.draft.levels.flatMap((level) => level.modules).map((module) => {
      const question = questionsFor(module)[0]
      return { key: module.key, title: module.title, content: module.content ?? '', prompt: question?.prompt ?? '', answer: question?.answer ?? '' }
    })
    message.value = 'AI draft ready. Review and edit it before saving.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not generate this draft.'
  } finally {
    aiLoading.value = false
  }
}

async function extractSource(file: File | null) {
  if (!file) return
  uploadLoading.value = true
  errorMessage.value = ''
  try {
    const body = new FormData()
    body.append('file', file)
    const response = await apiRequest<{ text: string }>('/api/ai/extract', { method: 'POST', body })
    aiForm.value.teaching_content = [aiForm.value.teaching_content, response.text].filter(Boolean).join('\n\n')
    message.value = 'Source text extracted for this draft. The uploaded original was discarded.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not extract this document.'
  } finally {
    uploadLoading.value = false
    sourceFile.value = null
  }
}

async function saveCourse() {
  saving.value = true
  errorMessage.value = ''
  const content = { modules: serializeModules() }
  try {
    if (editingId.value) {
      await apiRequest(`/api/courses/${editingId.value}`, {
        method: 'PATCH', body: JSON.stringify({ ...draft.value, content }),
      })
      message.value = 'Course changes saved as a new revision.'
    } else {
      await apiRequest('/api/courses', { method: 'POST', body: JSON.stringify({ ...draft.value, content }) })
      message.value = 'Course created as a draft.'
    }
    dialogOpen.value = false
    await loadCourses()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not save the course.'
  } finally {
    saving.value = false
  }
}

async function setCourseAccess(course: Course) {
  errorMessage.value = ''
  try {
    await apiRequest(`/api/courses/${course.id}/access`, {
      method: 'PATCH', body: JSON.stringify({ is_open: !course.is_open }),
    })
    await loadCourses()
    if (selectedCourse.value?.id === course.id) selectedCourse.value.is_open = !course.is_open
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not update course access.'
  }
}

async function submitAttempt(module: Module) {
  if (!selectedCourse.value?.revision_id) return
  const responses = answers.value[module.key] ?? {}
  try {
    const result = await apiRequest<{ score: number }>(`/api/courses/${selectedCourse.value.id}/attempts`, {
      method: 'POST',
      body: JSON.stringify({ revision_id: selectedCourse.value.revision_id, module_key: module.key, answers: responses }),
    })
    message.value = `Attempt recorded: ${result.score}%`
    const history = await apiRequest<{ attempts: Attempt[] }>(`/api/courses/${selectedCourse.value.id}/attempts`)
    attempts.value = history.attempts
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not submit this attempt.'
  }
}

onMounted(loadCourses)
watch(() => [props.role, props.activeSection], loadCourses)
</script>

<template>
  <section class="role-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span>{{ role === 'admin' ? 'PLATFORM' : role === 'instructor' ? 'TEACHING' : 'LEARNING' }}</p>
        <h2>{{ selectedCourse ? selectedCourse.title : role === 'admin' ? 'All courses' : role === 'instructor' ? 'My courses' : activeSection === 'scores' ? 'Score history' : 'My learning' }}</h2>
        <p class="page-description">{{ selectedCourse ? selectedCourse.description || 'Course content and activity.' : role === 'instructor' ? 'Create and refine courses you own.' : role === 'admin' ? 'Review course content, instructors, and access.' : 'Open a course to continue or retry a module.' }}</p>
      </div>
      <q-btn v-if="role === 'instructor' && !selectedCourse" unelevated no-caps class="primary-button" icon="add" label="Create course" @click="startCreate" />
      <q-btn v-if="selectedCourse" flat round icon="west" aria-label="Back to courses" @click="selectedCourse = null; message = ''; errorMessage = ''" />
    </div>

    <q-banner v-if="errorMessage" rounded class="error-banner">{{ errorMessage }}</q-banner>
    <q-banner v-if="message" rounded class="success-banner">{{ message }}</q-banner>

    <template v-if="selectedCourse">
      <div class="course-toolbar">
        <span>Revision {{ selectedCourse.revision }} <span class="status-dot" :class="selectedCourse.is_open ? 'open' : 'locked'"></span>{{ selectedCourse.is_open ? 'Open to enrolled students' : 'Locked' }}</span>
        <q-btn v-if="role === 'instructor'" flat no-caps icon="edit" label="Edit course" @click="startEdit(selectedCourse)" />
        <q-btn v-if="role === 'admin'" flat no-caps :icon="selectedCourse.is_open ? 'lock' : 'lock_open'" :label="selectedCourse.is_open ? 'Lock course' : 'Open course'" @click="setCourseAccess(selectedCourse)" />
      </div>
      <div v-if="role === 'admin'" class="course-detail-meta"><span>Instructor</span><strong>{{ selectedCourse.instructor.display_name }}</strong></div>
      <section v-if="role !== 'student'" class="roster-panel">
        <div class="roster-heading"><h3>Enrolled students</h3><span>{{ enrolledStudents.length }}</span></div>
        <div class="roster-add"><q-select v-model="selectedStudentId" outlined dense emit-value map-options label="Add student" :options="allStudents.filter((student) => !enrolledStudents.some((enrolled) => enrolled.id === student.id)).map((student) => ({ label: student.display_name, value: student.id }))" /><q-btn unelevated no-caps class="primary-button" icon="person_add" label="Enroll" :disable="!selectedStudentId" @click="enrollStudent" /></div>
        <div v-for="student in enrolledStudents" :key="student.id" class="roster-person"><q-avatar size="30px" class="person-avatar">{{ student.display_name.slice(0, 1).toUpperCase() }}</q-avatar><span>{{ student.display_name }}</span><small>{{ student.username }}</small><q-btn flat round dense icon="person_remove" aria-label="Remove student" @click="removeStudent(student)" /></div>
        <p v-if="!enrolledStudents.length" class="roster-empty">No students enrolled yet.</p>
      </section>
      <div v-for="(module, index) in moduleList(selectedCourse)" :key="module.key" class="module-row">
        <div class="module-index">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="module-body">
          <h3>{{ module.title }}</h3>
          <p v-if="module.content" class="lesson-content">{{ module.content }}</p>
          <div v-for="question in questionsFor(module)" :key="question.key" class="question-block">
            <p>{{ question.prompt }}</p>
            <q-input v-if="role === 'student'" :model-value="answers[module.key]?.[question.key] ?? ''" outlined dense placeholder="Your answer" @update:model-value="setAnswer(module.key, question.key, String($event ?? ''))" />
            <p v-else class="question-answer">Answer key: {{ question.answer }}</p>
          </div>
          <q-btn v-if="role === 'student' && questionsFor(module).length" unelevated no-caps class="primary-button attempt-button" label="Submit attempt" icon-right="arrow_forward" @click="submitAttempt(module)" />
          <span v-if="!questionsFor(module).length" class="module-note">Lesson content</span>
        </div>
      </div>
      <div v-if="role === 'student' && attempts.length" class="attempt-history">
        <h3>Recent attempts</h3>
        <div v-for="attempt in attempts" :key="attempt.id" class="attempt-line"><span>{{ attempt.module_key }}</span><strong>{{ attempt.score }}%</strong><small>Revision {{ attempt.revision_id === selectedCourse.revision_id ? selectedCourse.revision : 'previous' }}</small></div>
      </div>
      <div v-if="!moduleList(selectedCourse).length" class="empty-inline">No modules have been added to this course yet.</div>
    </template>

    <div v-else-if="loading" class="loading-state"><q-spinner-dots size="28px" color="primary" /> Loading courses…</div>
    <div v-else-if="!courses.length" class="empty-inline">{{ role === 'student' ? 'You are not enrolled in any open courses yet.' : 'No courses here yet.' }}</div>
    <div v-else class="course-list">
      <article v-for="course in courses" :key="course.id" class="course-row">
        <button class="course-open" @click="openCourse(course)">
          <span class="course-symbol"><q-icon name="menu_book" size="19px" /></span>
          <span class="course-summary"><strong>{{ course.title }}</strong><small>{{ course.description || 'No description yet.' }}</small></span>
        </button>
        <span v-if="role === 'admin'" class="instructor-label">{{ course.instructor.display_name }}</span>
        <span class="course-state" :class="course.is_open ? 'is-open' : 'is-locked'">{{ course.is_open ? 'Open' : 'Locked' }}</span>
        <span class="revision-label">R{{ course.revision }}</span>
        <q-btn v-if="role === 'instructor'" flat round dense icon="edit" aria-label="Edit course" @click="startEdit(course)" />
        <q-btn v-if="role === 'admin'" flat round dense :icon="course.is_open ? 'lock_open' : 'lock'" :aria-label="course.is_open ? 'Lock course' : 'Open course'" @click="setCourseAccess(course)" />
        <q-btn flat round dense icon="arrow_forward" aria-label="View course" @click="openCourse(course)" />
      </article>
    </div>

    <q-dialog v-model="dialogOpen">
      <q-card class="editor-card">
        <q-card-section class="editor-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> COURSE EDITOR</p><h2>{{ editingId ? 'Refine your course' : 'Create a course' }}</h2></div><q-btn flat round dense icon="close" aria-label="Close" @click="dialogOpen = false" /></q-card-section>
        <q-form class="editor-form" @submit.prevent="saveCourse">
          <label class="field-label" for="course-title">Course title</label><q-input id="course-title" v-model="draft.title" outlined dense maxlength="160" :rules="[(value) => value.trim().length >= 2 || 'Enter a course title']" />
          <label class="field-label" for="course-description">Description</label><q-input id="course-description" v-model="draft.description" outlined dense type="textarea" autogrow maxlength="2000" />
          <details class="ai-details">
            <summary><q-icon name="auto_awesome" size="18px" /> Build a first draft with AI</summary>
            <div class="ai-fields">
              <label class="field-label">Topic</label><q-input v-model="aiForm.topic" outlined dense maxlength="160" />
              <label class="field-label">Learner level</label><q-input v-model="aiForm.level" outlined dense maxlength="80" placeholder="Beginner, intermediate, grade level…" />
              <label class="field-label">Requirements</label><q-input v-model="aiForm.requirements" outlined dense type="textarea" autogrow maxlength="4000" placeholder="Learning objectives, number of lessons, activity style…" />
              <label class="field-label">Teaching material <span class="optional-label">Optional</span></label><q-input v-model="aiForm.teaching_content" outlined dense type="textarea" autogrow maxlength="12000" placeholder="Paste reference notes or extract from a document below." />
              <q-file v-model="sourceFile" outlined dense accept=".pdf,.pptx,.doc,.docx" label="Extract PDF, PowerPoint, or Word text" :loading="uploadLoading" @update:model-value="extractSource" />
              <q-btn unelevated no-caps class="primary-button ai-generate" icon="auto_awesome" label="Generate editable draft" :loading="aiLoading" :disable="!aiForm.topic || !aiForm.level || !aiForm.requirements" @click="generateCourseDraft" />
            </div>
          </details>
          <div class="editor-section-title"><h3>Modules and practice</h3><q-btn flat no-caps icon="add" label="Add module" @click="addModule" /></div>
          <div v-for="(module, index) in draftModules" :key="module.key" class="module-editor">
            <div class="module-editor-heading"><strong>Module {{ index + 1 }}</strong><q-btn v-if="draftModules.length > 1" flat round dense icon="delete_outline" aria-label="Remove module" @click="draftModules.splice(index, 1)" /></div>
            <label class="field-label">Module title</label><q-input v-model="module.title" outlined dense maxlength="120" />
            <label class="field-label">Lesson content</label><q-input v-model="module.content" outlined dense type="textarea" autogrow maxlength="6000" />
            <label class="field-label">Quiz question <span class="optional-label">Optional</span></label><q-input v-model="module.prompt" outlined dense placeholder="Ask a question to check understanding" />
            <label class="field-label">Correct answer</label><q-input v-model="module.answer" outlined dense placeholder="Answer key" />
          </div>
          <div class="editor-actions"><q-btn flat no-caps label="Cancel" @click="dialogOpen = false" /><q-btn type="submit" unelevated no-caps class="primary-button" :loading="saving" label="Save course" icon-right="arrow_forward" /></div>
        </q-form>
      </q-card>
    </q-dialog>
  </section>
</template>