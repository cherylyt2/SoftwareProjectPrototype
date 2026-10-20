<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import CourseWorkspace from './components/CourseWorkspace.vue'
import LearningPathWorkspace from './components/LearningPathWorkspace.vue'
import PeopleWorkspace from './components/PeopleWorkspace.vue'

type Role = 'admin' | 'instructor' | 'student'
type Screen = 'welcome' | 'login' | 'workspace'

const screen = ref<Screen>('welcome')
const role = ref<Role>('student')
const username = ref('')
const password = ref('')
const errorMessage = ref('')
const loading = ref(false)
const profileMenu = ref(false)
const activeSection = ref('overview')
const userName = ref('')
const mustChangePassword = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const passwordError = ref('')
const passwordLoading = ref(false)
const settingsDialog = ref(false)
const settingsSaving = ref(false)
const settingsError = ref('')
const displayName = ref('')

const roleDetails: Record<Role, { title: string; description: string; icon: string }> = {
  admin: { title: 'Administrator', description: 'Manage people, courses, and access.', icon: 'shield' },
  instructor: { title: 'Instructor', description: 'Build courses and guide your students.', icon: 'auto_stories' },
  student: { title: 'Student', description: 'Continue learning and track progress.', icon: 'school' },
}

const roleInfo = computed(() => roleDetails[role.value])
const navigation = computed(() => {
  const common = [{ id: 'overview', label: 'Overview', icon: 'space_dashboard' }]
  if (role.value === 'admin') {
    return [...common, { id: 'courses', label: 'All courses', icon: 'menu_book' }, { id: 'people', label: 'People', icon: 'groups' }]
  }
  if (role.value === 'instructor') {
    return [...common, { id: 'courses', label: 'My courses', icon: 'menu_book' }, { id: 'students', label: 'Students', icon: 'groups' }]
  }
  return [...common, { id: 'courses', label: 'My learning', icon: 'menu_book' }, { id: 'path', label: 'Self-learning', icon: 'route' }, { id: 'scores', label: 'Scores', icon: 'insights' }]
})
const pageTitle = computed(() => activeSection.value === 'overview'
  ? 'Your learning space'
  : navigation.value.find((item) => item.id === activeSection.value)?.label ?? 'Overview')

async function signIn() {
  errorMessage.value = ''
  loading.value = true
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username: username.value, password: password.value, role: role.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error ?? 'Unable to sign in.')
    userName.value = data.user.display_name || data.user.username
    displayName.value = data.user.display_name || data.user.username
    mustChangePassword.value = data.user.must_change_password
    screen.value = 'workspace'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Unable to reach the sign-in service.'
  } finally {
    loading.value = false
  }
}

async function restoreSession() {
  try {
    const response = await fetch('/api/auth/session', { credentials: 'include' })
    if (!response.ok) return
    const data = await response.json()
    if (!data.user) return
    role.value = data.user.role
    userName.value = data.user.display_name || data.user.username
    displayName.value = data.user.display_name || data.user.username
    mustChangePassword.value = data.user.must_change_password
    screen.value = 'workspace'
  } catch {
    // Keep the welcome screen usable when the API is unavailable.
  }
}

async function saveProfile() {
  settingsSaving.value = true
  settingsError.value = ''
  try {
    const response = await fetch('/api/auth/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ display_name: displayName.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error ?? 'Unable to update your profile.')
    userName.value = data.user.display_name
    settingsDialog.value = false
  } catch (error) {
    settingsError.value = error instanceof Error ? error.message : 'Unable to update your profile.'
  } finally {
    settingsSaving.value = false
  }
}

async function signOut() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => undefined)
  screen.value = 'welcome'
  activeSection.value = 'overview'
  username.value = ''
  password.value = ''
}

async function updatePassword() {
  passwordError.value = ''
  passwordLoading.value = true
  try {
    const response = await fetch('/api/auth/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ current_password: currentPassword.value, new_password: newPassword.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error ?? 'Unable to update password.')
    mustChangePassword.value = false
    currentPassword.value = ''
    newPassword.value = ''
  } catch (error) {
    passwordError.value = error instanceof Error ? error.message : 'Unable to update password.'
  } finally {
    passwordLoading.value = false
  }
}

function chooseRole(nextRole: Role) {
  role.value = nextRole
  errorMessage.value = ''
  screen.value = 'login'
}

onMounted(restoreSession)
</script>

<template>
  <main v-if="screen !== 'workspace'" class="entry-screen">
    <header class="entry-header">
      <a class="wordmark" href="#" @click.prevent="screen = 'welcome'">
        <span class="wordmark-mark"><q-icon name="flare" size="21px" /></span>
        <span>northstar<span class="wordmark-period">.</span></span>
      </a>
      <span class="entry-caption">LEARNING PLATFORM</span>
    </header>

    <section v-if="screen === 'welcome'" class="welcome-stage">
      <div class="welcome-copy">
        <p class="eyebrow"><span class="eyebrow-line"></span> A place to keep growing</p>
        <h1>Learning moves<br />you <em>forward.</em></h1>
        <p class="welcome-intro">Thoughtful courses, curious minds, and a clearer view of how far you can go.</p>
        <div class="welcome-actions">
          <q-btn unelevated no-caps class="primary-button" label="Enter your learning space" icon-right="arrow_forward" @click="screen = 'login'" />
          <!-- <span class="welcome-note">Choose your role to continue</span> -->
        </div>
      </div>
      <div class="welcome-art" aria-label="A course preview showing a learning path">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <div class="art-label">YOUR NEXT CHAPTER</div>
        <div class="path-card">
          <div class="path-card-top"><span>LEARNING PATH</span><q-icon name="north_east" size="17px" /></div>
          <div class="path-title">Ideas into<br />understanding.</div>
          <div class="path-progress"><span></span></div>
          <div class="path-meta"><span>Take it one step at a time</span><strong>01 / 04</strong></div>
        </div>
        <div class="art-stamp"><q-icon name="auto_awesome" size="19px" /><span>Made for<br />your pace</span></div>
        <div class="art-number">01</div>
      </div>
      <!-- <button class="scroll-cue" aria-label="Continue to role selection" @click="screen = 'login'">
        <span>SCROLL TO BEGIN</span><q-icon name="south" size="16px" />
      </button> -->
    </section>

    <section v-else class="login-stage">
      <div class="login-aside">
        <p class="eyebrow"><span class="eyebrow-line"></span> Welcome back</p>
        <h1>Good things<br />start <em>here.</em></h1>
        <p class="welcome-intro">Choose your place in the learning community.</p>
        <div class="role-list" role="group" aria-label="Choose your role">
          <button v-for="(details, key) in roleDetails" :key="key" class="role-option" :class="{ selected: role === key }" @click="chooseRole(key as Role)">
            <span class="role-icon"><q-icon :name="details.icon" size="20px" /></span>
            <span class="role-copy"><strong>{{ details.title }}</strong><small>{{ details.description }}</small></span>
            <q-icon v-if="role === key" name="check_circle" size="19px" class="role-check" />
          </button>
        </div>
      </div>
      <q-form class="login-form" @submit.prevent="signIn">
        <div class="form-heading">
          <span class="form-icon"><q-icon :name="roleInfo.icon" size="22px" /></span>
          <div><p class="eyebrow">SIGN IN AS</p><h2>{{ roleInfo.title }}</h2></div>
        </div>
        <label class="field-label" for="username">Username</label>
        <q-input id="username" v-model="username" outlined dense autocomplete="username" placeholder="Your username" :rules="[(value) => !!value || 'Enter your username']" />
        <label class="field-label" for="password">Password</label>
        <q-input id="password" v-model="password" outlined dense autocomplete="current-password" type="password" placeholder="Your password" :rules="[(value) => !!value || 'Enter your password']" />
        <q-banner v-if="errorMessage" rounded class="error-banner">{{ errorMessage }}</q-banner>
        <q-btn type="submit" unelevated no-caps class="primary-button login-submit" :loading="loading" label="Sign in" icon-right="arrow_forward" />
        <button class="back-link" type="button" @click="screen = 'welcome'"><q-icon name="west" size="15px" /> Back to welcome</button>
      </q-form>
    </section>
  </main>

  <div v-else class="workspace-shell">
    <aside class="sidebar">
      <a class="wordmark sidebar-brand" href="#" @click.prevent="activeSection = 'overview'">
        <span class="wordmark-mark"><q-icon name="flare" size="21px" /></span><span>northstar<span class="wordmark-period">.</span></span>
      </a>
      <div class="workspace-label">WORKSPACE</div>
      <nav class="side-nav" aria-label="Main navigation">
        <button v-for="item in navigation" :key="item.id" class="nav-item" :aria-label="item.label" :class="{ active: activeSection === item.id }" @click="activeSection = item.id">
          <q-icon :name="item.icon" size="19px" /><span>{{ item.label }}</span>
        </button>
      </nav>
      <div class="sidebar-bottom">
        <div class="help-note"><span class="help-icon"><q-icon name="lightbulb" size="17px" /></span><span>Small steps<br />add up to a lot.</span></div>
        <div class="sidebar-foot">LEARNING PLATFORM <span>·</span> 2026</div>
      </div>
    </aside>

    <section class="workspace-main">
      <header class="workspace-header">
        <div class="breadcrumb"><span>Workspace</span><q-icon name="chevron_right" size="16px" /><strong>{{ pageTitle }}</strong></div>
        <!-- <q-btn flat round dense icon="notifications_none" class="header-icon" aria-label="Notifications" /> -->
        <q-btn flat no-caps class="profile-button" @click="profileMenu = !profileMenu">
          <q-avatar size="34px" class="profile-avatar">{{ userName.slice(0, 1).toUpperCase() }}</q-avatar>
          <span class="profile-name">{{ userName }}</span><q-icon name="expand_more" size="18px" />
        </q-btn>
        <q-menu v-model="profileMenu" anchor="bottom right" self="top right" class="profile-menu">
          <q-list dense style="min-width: 170px">
            <q-item clickable v-close-popup @click="settingsDialog = true"><q-item-section avatar><q-icon name="settings" /></q-item-section><q-item-section>Settings</q-item-section></q-item>
            <q-separator />
            <q-item clickable v-close-popup @click="signOut"><q-item-section avatar><q-icon name="logout" /></q-item-section><q-item-section>Sign out</q-item-section></q-item>
          </q-list>
        </q-menu>
      </header>

      <main class="workspace-content">
        <div class="content-intro">
          <div><p class="eyebrow"><span class="eyebrow-line"></span> {{ roleInfo.title }} SPACE</p><h1>{{ pageTitle }}<span class="title-period">.</span></h1><p class="content-subtitle">A good place to pick up where you are.</p></div>
        </div>
        <CourseWorkspace v-if="['overview', 'courses', 'scores'].includes(activeSection)" :role="role" :active-section="activeSection" />
        <PeopleWorkspace v-else-if="['people', 'students'].includes(activeSection)" :role="role" />
        <LearningPathWorkspace v-else-if="activeSection === 'path'" />
        <footer class="content-footer"><span>Make room for what’s next.</span><span>Northstar Learning</span></footer>
      </main>
    </section>
    <q-dialog :model-value="mustChangePassword" persistent>
      <q-card class="password-card">
        <q-card-section>
          <p class="eyebrow"><span class="eyebrow-line"></span> ACCOUNT SECURITY</p>
          <h2>Choose a new password</h2>
          <p class="password-copy">Update your temporary password before continuing.</p>
        </q-card-section>
        <q-form class="password-form" @submit.prevent="updatePassword">
          <label class="field-label" for="current-password">Current password</label>
          <q-input id="current-password" v-model="currentPassword" outlined dense type="password" autocomplete="current-password" />
          <label class="field-label" for="new-password">New password</label>
          <q-input id="new-password" v-model="newPassword" outlined dense type="password" autocomplete="new-password" hint="Use at least 12 characters." :rules="[(value) => value.length >= 12 || 'Use at least 12 characters']" />
          <q-banner v-if="passwordError" rounded class="error-banner">{{ passwordError }}</q-banner>
          <q-btn type="submit" unelevated no-caps class="primary-button login-submit" :loading="passwordLoading" label="Update password" icon-right="arrow_forward" />
        </q-form>
      </q-card>
    </q-dialog>
    <q-dialog v-model="settingsDialog">
      <q-card class="password-card">
        <q-card-section><p class="eyebrow"><span class="eyebrow-line"></span> PROFILE</p><h2>Settings</h2><p class="password-copy">Update how your name appears across the platform.</p></q-card-section>
        <q-form class="password-form" @submit.prevent="saveProfile">
          <label class="field-label" for="display-name">Display name</label><q-input id="display-name" v-model="displayName" outlined dense maxlength="120" :rules="[(value) => value.trim().length > 0 || 'Enter a display name']" />
          <q-banner v-if="settingsError" rounded class="error-banner">{{ settingsError }}</q-banner>
          <div class="editor-actions"><q-btn flat no-caps label="Cancel" @click="settingsDialog = false" /><q-btn type="submit" unelevated no-caps class="primary-button" :loading="settingsSaving" label="Save settings" /></div>
        </q-form>
      </q-card>
    </q-dialog>
  </div>
</template>