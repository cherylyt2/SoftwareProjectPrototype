import { flushPromises, mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import { describe, expect, it, vi } from 'vitest'
import CourseWorkspace from './CourseWorkspace.vue'

const course = {
  id: 'course-1',
  title: 'Plant science',
  description: 'An introduction to plants.',
  is_open: true,
  revision: 2,
  revision_id: 'revision-2',
  instructor: { display_name: 'Tara Teacher' },
  content: { modules: [{
    key: 'module-1', title: 'Photosynthesis', content: 'Plants use light to make sugars.',
    activities: [{ type: 'quiz', questions: [{ key: 'question-1', prompt: 'What do plants use?', answer: 'light' }] }],
  }] },
}

function jsonResponse(data: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data }
}

describe('CourseWorkspace', () => {
  it('loads a course and records a student quiz attempt', async () => {
    const fetchMock = vi.fn().mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/api/courses') return jsonResponse({ courses: [course] })
      if (path === '/api/courses/course-1' && options?.method !== 'POST') return jsonResponse({ course })
      if (path === '/api/courses/course-1/attempts' && options?.method === 'POST') return jsonResponse({ score: 100 }, 201)
      if (path === '/api/courses/course-1/attempts') return jsonResponse({ attempts: [] })
      return jsonResponse({ error: 'Unexpected request' }, 404)
    })
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(CourseWorkspace, {
      props: { role: 'student', activeSection: 'courses' },
      global: { plugins: [Quasar] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Plant science')
    await wrapper.get('.course-open').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Plants use light to make sugars.')
    await wrapper.find('input[placeholder="Your answer"]').setValue('light')
    await wrapper.get('.attempt-button').trigger('click')
    await flushPromises()

    const submission = fetchMock.mock.calls.find(([path, options]) => path.endsWith('/attempts') && options?.method === 'POST')
    expect(JSON.parse(submission?.[1]?.body as string).revision_id).toBe('revision-2')
    expect(JSON.parse(submission?.[1]?.body as string).answers['question-1']).toBe('light')
    expect(wrapper.text()).toContain('Attempt recorded: 100%')
    wrapper.unmount()
    vi.unstubAllGlobals()
  })
})