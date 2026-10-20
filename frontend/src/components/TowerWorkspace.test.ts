import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import TowerWorkspace from './TowerWorkspace.vue'

const card = (id: string, title: string, cost: number, value: number, type: string, correct?: boolean) => ({
  card_id: id, title, energy_cost: cost, value, card_type: type, ...(correct === undefined ? {} : { correct_choice: correct }),
})

function stage(withAnswers: boolean) {
  const flag = (value: boolean) => (withAnswers ? value : undefined)
  return {
    course_id: 'sdlc', topic_name: 'Requirements Analysis', floor: 1, enemy_name: 'The Vague Requirement Wraith', enemy_max_hp: 30,
    turn_1_enemy_intent: 'Whispers vague wishes', turn_1_enemy_damage: 10,
    turn_2_enemy_intent: 'Splits the stakeholders', turn_2_enemy_damage: 10,
    turn_1_hand: [card('a1', 'Testable Requirement Rewrite', 2, 15, 'Attack', flag(true)), card('s1', 'Quick Patch', 1, 5, 'Attack', flag(false)), card('d1', 'Rubber Duck', 1, 8, 'Defend', flag(false))],
    turn_2_hand: [card('a2', 'MoSCoW Prioritization', 2, 15, 'Attack', flag(true)), card('s2', 'Quick Patch', 1, 5, 'Attack', flag(false)), card('c2', 'Gold Plating', 1, 5, 'Curse', flag(false))],
    title: 'Floor 1 Battle: Requirements Analysis',
    incident_brief: 'The client wants it fast.',
    quick_reference: '- Rewrite vague wishes as testable requirements.\n- Use MoSCoW to prioritize.',
  }
}

function mountFor(role: 'student' | 'admin' | 'instructor') {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ stages: [stage(role !== 'student')] }) }))
  return mount(TowerWorkspace, { props: { role }, global: { plugins: [Quasar] } })
}

afterEach(() => vi.unstubAllGlobals())

describe('Code Spire battle floors', () => {
  it('lets a student win by playing both Premium Attacks', async () => {
    const wrapper = mountFor('student')
    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text().includes('Enter floor 1'))?.trigger('click')

    await wrapper.findAll('button.hand-card')[0].trigger('click')
    await wrapper.find('button.end-turn').trigger('click')
    expect(wrapper.text()).toContain('Turn 2 of 2')
    expect(wrapper.find('.player-hp').text()).toContain('30 / 40')

    await wrapper.findAll('button.hand-card')[0].trigger('click')

    expect(wrapper.find('.enemy-hp').text()).toContain('0 / 30')
    expect(wrapper.text()).toContain('Floor cleared')
    expect(wrapper.text()).toContain('MoSCoW to prioritize')
    wrapper.unmount()
  })

  it('stops a student from spending more than 3 energy and loses when the bug survives', async () => {
    const wrapper = mountFor('student')
    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text().includes('Enter floor 1'))?.trigger('click')

    const cards = wrapper.findAll('button.hand-card')
    await cards[0].trigger('click')
    await cards[1].trigger('click')
    expect(wrapper.find('.energy').text()).toContain('0 / 3')
    expect(cards[2].attributes('disabled')).toBeDefined()

    await wrapper.find('button.end-turn').trigger('click')
    await wrapper.find('button.end-turn').trigger('click')

    expect(wrapper.text()).toContain('The bug survived both turns')
    wrapper.unmount()
  })

  it('shows staff the floors read-only with the correct cards marked', async () => {
    const wrapper = mountFor('instructor')
    await flushPromises()

    expect(wrapper.text()).toContain('Floor 1 Battle: Requirements Analysis')
    expect(wrapper.findAll('.correct-tag')).toHaveLength(2)
    expect(wrapper.text()).toContain('Rewrite vague wishes')
    expect(wrapper.find('button.hand-card').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Enter floor')
    wrapper.unmount()
  })
})
