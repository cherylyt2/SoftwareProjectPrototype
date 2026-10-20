---
course_id: "sdlc"
topic_name: "Design and Implementation"
floor: 2
enemy_name: "The Leaked Key Gremlin"
enemy_max_hp: 30
turn_1_enemy_intent: "Scans the public repository for a secret key that was committed with the code"
turn_1_enemy_damage: 10
turn_2_enemy_intent: "Waits for the deployed app to ship the same key to every visitor's browser"
turn_2_enemy_damage: 10
turn_1_hand:
  - card_id: "f2-t1-premium"
    title: "Env File and Gitignore"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f2-t1-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f2-t1-defend"
    title: "Rubber Duck"
    energy_cost: 1
    value: 8
    card_type: "Defend"
    correct_choice: false
turn_2_hand:
  - card_id: "f2-t2-premium"
    title: "Platform Environment Variables"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f2-t2-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f2-t2-curse"
    title: "Hardcoded Secret"
    energy_cost: 1
    value: 5
    card_type: "Curse"
    correct_choice: false
---

# Floor 2 Battle: Design and Implementation

## The Incident Brief

The team is building a GenAI powered chat app. A Flask API backend receives questions from the React frontend, sends them to the AI service, and returns the answers, while a database stores past chats. In a rush before a demo, a developer pastes the AI service key straight into a source file and pushes it to a public GitHub repository. Automated scanners find secret keys within minutes, and the key is soon used by strangers.

After the key is rotated, the team deploys the app. A tempting shortcut is to call the AI service directly from the frontend with the key included, which would hand the secret to anyone who opens the browser developer tools. The Leaked Key Gremlin is waiting for either mistake.

## Quick Reference

- Turn 1, Env File and Gitignore wins. During development the secret keys live in a .env file that is read as local environment variables, and the .gitignore file keeps .env and other sensitive files out of version control. Secret keys must never appear in the remote repository.
- Turn 2, Platform Environment Variables wins. In production the keys are stored in the hosting platform's settings, for example Vercel's environment variables, and are injected into the running application during deployment. They stay hidden from the public and from frontend code, so the frontend only talks to the backend API.
- Design says how the system does what the requirements say it should do. The backend API holds business logic and talks to the database and AI service, while the frontend handles the user interface.
- Hardcoded Secret is the curse. Anything committed to the repository or shipped to the browser should be treated as public.
- Quick Patch and Rubber Duck are generic moves. They do not stop a key from leaking.
