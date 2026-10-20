import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import AppRoot from './AppRoot.vue'

function jsonResponse(data: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data }
}

afterEach(() => vi.unstubAllGlobals())

describe('learning platform entry flow', () => {
  it('starts a role-specific prototype session without credential fields', async () => {
    const fetchMock = vi.fn().mockImplementation(async (path: string) => {
      if (path === '/api/auth/session') return jsonResponse({ user: null, prototype_mode: true })
      if (path === '/api/courses') return jsonResponse({ courses: [] })
      return jsonResponse({
        user: { username: 'prototype-instructor', display_name: 'Prototype Instructor', role: 'instructor', must_change_password: false },
      })
    })
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(AppRoot, { global: { plugins: [Quasar] } })
    await flushPromises()

    expect(wrapper.text()).toContain('Learning moves')
    const enterButton = wrapper.findAll('button').find((button) => button.text().includes('Enter your learning space'))
    await enterButton?.trigger('click')
    await wrapper.findAll('.role-option')[1].trigger('click')

    expect(wrapper.text()).toContain('Instructor')
    expect(wrapper.find('.login-form').exists()).toBe(true)
    expect(wrapper.find('input[autocomplete="username"]').exists()).toBe(false)
    await wrapper.find('.prototype-entry button.primary-button').trigger('click')
    await flushPromises()

    const sessionRequest = fetchMock.mock.calls.find(([path]) => path === '/api/auth/prototype-session')
    expect(JSON.parse(sessionRequest?.[1]?.body as string).role).toBe('instructor')
    expect(wrapper.find('.workspace-shell').exists()).toBe(true)
    wrapper.unmount()
  })

  it('sends the chosen role to the API and shows authentication failures', async () => {
    const fetchMock = vi.fn().mockImplementation(async (path: string) => {
      if (path === '/api/auth/session') return jsonResponse({ user: null, prototype_mode: false })
      return jsonResponse({ error: 'Username, password, or role is incorrect.' }, 401)
    })
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(AppRoot, { global: { plugins: [Quasar] } })
    await flushPromises()
    const enterButton = wrapper.findAll('button').find((button) => button.text().includes('Enter your learning space'))
    await enterButton?.trigger('click')
    await wrapper.findAll('.role-option')[1].trigger('click')
    await wrapper.find('input[autocomplete="username"]').setValue('teacher')
    await wrapper.find('input[autocomplete="current-password"]').setValue('bad-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const loginRequest = fetchMock.mock.calls.find(([path]) => path === '/api/auth/login')
    expect(JSON.parse(loginRequest?.[1]?.body as string).role).toBe('instructor')
    expect(wrapper.text()).toContain('Username, password, or role is incorrect.')
    wrapper.unmount()
  })
})