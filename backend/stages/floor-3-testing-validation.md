---
course_id: "sdlc"
topic_name: "Testing and Validation"
floor: 3
enemy_name: "The Regression Gremlin"
enemy_max_hp: 30
turn_1_enemy_intent: "Hides in the gap between two modules that each pass their own unit tests"
turn_1_enemy_damage: 10
turn_2_enemy_intent: "Breaks a feature that worked yesterday while the team fixes something else"
turn_2_enemy_damage: 10
turn_1_hand:
  - card_id: "f3-t1-premium"
    title: "Integration Test"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f3-t1-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f3-t1-defend"
    title: "Rubber Duck"
    energy_cost: 1
    value: 8
    card_type: "Defend"
    correct_choice: false
turn_2_hand:
  - card_id: "f3-t2-premium"
    title: "Regression Test Suite"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f3-t2-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f3-t2-curse"
    title: "Skip Tests and Ship"
    energy_cost: 1
    value: 5
    card_type: "Curse"
    correct_choice: false
---

# Floor 3 Battle: Testing and Validation

## The Incident Brief

A learning app has an AI tutor module that generates questions from a source text, and a chat module that shows those questions to students. Every unit test passes for both modules, yet in the combined app the chat screen crashes because the tutor module returns the question list in a different format than the chat module expects. Each module is correct on its own, and the bug only appears when they are put together.

The team fixes the format and adds a new feature in the same week. After the release, the student progress page stops working even though nobody touched it. A change in one place has quietly broken something that used to be correct. The Regression Gremlin is behind both failures.

## Quick Reference

- Turn 1, Integration Test wins. Unit tests check individual units in isolation, so a calling module can misunderstand the interface of a called module without any unit test noticing. Integration testing combines modules and tests them as a group.
- Turn 2, Regression Test Suite wins. Regression is the misbehavior of a previously correct feature after a modification such as a bug fix or a new feature. Existing test cases are re-run, and test automation makes this fast, for example running tens of thousands of unit tests on every pull request.
- Confirmation testing re-runs the tests that failed before to check the fix, while regression testing checks that unchanged areas still work.
- System testing checks the whole system against the requirements, including functionality, robustness, performance, scalability and reliability. Acceptance testing lets customers or end users judge whether the right system was built, with alpha tests at the developer's site and beta tests at user sites.
- Verification asks whether the product is built right, using code review and testing. Validation asks whether the right product is built, using prototyping, acceptance and usability testing.
- Skip Tests and Ship is the curse. Releasing without tests moves the bugs to production where they cost more.
- Quick Patch and Rubber Duck are generic moves. They do not reveal interface mismatches or regressions.
