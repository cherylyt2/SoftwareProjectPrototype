---
course_id: "sdlc"
topic_name: "Requirements Analysis"
floor: 1
enemy_name: "The Vague Requirement Wraith"
enemy_max_hp: 30
turn_1_enemy_intent: "Whispers that the app must be fast and user friendly, and nobody can say how to check it"
turn_1_enemy_damage: 10
turn_2_enemy_intent: "Splits the stakeholders so every one of them insists their feature is the top priority"
turn_2_enemy_damage: 10
turn_1_hand:
  - card_id: "f1-t1-premium"
    title: "Testable Requirement Rewrite"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f1-t1-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f1-t1-defend"
    title: "Rubber Duck"
    energy_cost: 1
    value: 8
    card_type: "Defend"
    correct_choice: false
turn_2_hand:
  - card_id: "f1-t2-premium"
    title: "MoSCoW Prioritization"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f1-t2-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f1-t2-curse"
    title: "Gold Plating"
    energy_cost: 1
    value: 5
    card_type: "Curse"
    correct_choice: false
---

# Floor 1 Battle: Requirements Analysis

## The Incident Brief

A learning platform team has a kickoff meeting with a client. The client says the new app should be fast and user friendly, and the meeting ends with everyone nodding. Two weeks later the developers have built what they guessed the client meant, and the client rejects it. Nobody can prove whether the app is fast or friendly, because those words were never turned into anything that can be checked.

Then the stakeholders disagree. Teachers want course authoring first, students want progress tracking first, and the administrator wants account management first. Every request is labelled urgent, the backlog keeps growing, and the team cannot finish anything. The Vague Requirement Wraith feeds on both problems.

## Quick Reference

- Turn 1, Testable Requirement Rewrite wins. A functional requirement states what the system does, and a non-functional requirement states how well it does it. Vague statements must be converted into specific, testable requirements or business rules, for example "a search returns results in under two seconds for 95 percent of queries".
- Requirements come from elicitation: identify stakeholders, collect information with interviews, surveys, observation, document analysis, focus groups or prototyping, then document what was learned. Asking open questions and using the 5 Whys reaches root causes instead of symptoms.
- Turn 2, MoSCoW Prioritization wins. It sorts requirements into Must, Should, Could and Won't so stakeholders agree on what is essential now and what can wait. Prioritization, change management and verification and validation make up requirements management.
- Gold Plating is the curse. Adding extras nobody prioritized causes scope creep and delays the Must have work.
- Quick Patch and Rubber Duck are generic moves. They help a little, but they do not address the underlying requirements problem.
