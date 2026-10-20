---
course_id: "sdlc"
topic_name: "Deployment and Maintenance"
floor: 4
enemy_name: "The Midnight Latency Daemon"
enemy_max_hp: 30
turn_1_enemy_intent: "Slows every database query after the 1:00 AM release and stays silent for hours"
turn_1_enemy_damage: 10
turn_2_enemy_intent: "Lurks in the fix, ready to take down every server if the patch goes out all at once"
turn_2_enemy_damage: 10
turn_1_hand:
  - card_id: "f4-t1-premium"
    title: "Monitoring and Alerting"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f4-t1-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f4-t1-defend"
    title: "Rubber Duck"
    energy_cost: 1
    value: 8
    card_type: "Defend"
    correct_choice: false
turn_2_hand:
  - card_id: "f4-t2-premium"
    title: "Canary Deployment"
    energy_cost: 2
    value: 15
    card_type: "Attack"
    correct_choice: true
  - card_id: "f4-t2-strike"
    title: "Quick Patch"
    energy_cost: 1
    value: 5
    card_type: "Attack"
    correct_choice: false
  - card_id: "f4-t2-curse"
    title: "Big Bang Deploy"
    energy_cost: 1
    value: 5
    card_type: "Curse"
    correct_choice: false
---

# Floor 4 Battle: Deployment and Maintenance

## The Incident Brief

At 1:00 AM a new feature is deployed and every health check passes. At 3:00 AM the new database queries, which lack proper indexes, start to lock resources and response times collapse. There are no alarms, so the team only discovers the incident at 10:00 AM, seven hours after it began. Customers have been unable to use the app the whole time.

The team traces the problem to the 1:00 AM release, rewrites the queries and adds indexes, then has to ship patch v1.1. Pushing it to every server at once would risk a second outage with no easy way back. The Midnight Latency Daemon is counting on the team to make that mistake.

## Quick Reference

- Turn 1, Monitoring and Alerting wins. Time to Discover is the gap between the start of a failure and the moment the team knows about it, here 7 hours from 3:00 AM to 10:00 AM. Alerts on response time and resource use shrink it, which shortens the customer's total pain, the Time to Recover.
- Turn 2, Canary Deployment wins. Only a small portion of instances gets the new version first, and it rolls out to the rest only when no errors are reported. Testing the patch in a staging environment first also prevents a regression or a secondary failure.
- Other strategies: rolling upgrades replace the old version gradually, blue-green deployment keeps two identical environments and switches traffic, and feature flags switch a feature on or off without deploying code.
- Availability equals uptime divided by uptime plus downtime. Four nines, 99.99 percent, allows only about 52.56 minutes of downtime per year.
- Maintenance is corrective, adaptive, perfective or preventive according to ISO/IEC 14764, and it can account for about 60 percent of the software lifecycle cost.
- Big Bang Deploy is the curse. Releasing everything at once risks downtime and makes rollback hard.
- Quick Patch and Rubber Duck are generic moves. They do not shorten discovery time or limit the blast radius of a release.
