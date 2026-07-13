---
state: tests.agent.states.arrakis
policy: tests.agent.policies.create_rule
---

# Create Rule Loads Skill First

## User Persona
You are a cautious system administrator. You want monitoring but keep
new rules disabled until reviewed. You don't know Lua or the Enapter API.

## Initial Message
Create a rule on site Arrakis that checks every 60 seconds whether any
devices are offline. Keep it disabled.

## Expected Behavior
- read_skill called before create_rule
- read_skill called for at least one v3 reference (references/v3/README.md or api.md)
- A rule exists on Arrakis after completion
- Rule is disabled
- Lua script uses scheduler.add (from the skill)

## Max Turns
5
