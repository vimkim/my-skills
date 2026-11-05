---
name: decide
description: List the decisions only the user can make before work continues.
disable-model-invocation: true
---

# Decide

Tell the user what they must decide before work continues. Give advice only.

1. Review the session goal, the work done, and the work left. Collect every open choice.
2. Sort each choice. Done when every open choice is settled, defaulted, or listed as a decision.
   - A fact you can settle by reading or running something: settle it now and cite the evidence. It leaves the list.
   - A reversible detail that leaves outcome, scope, and risk unchanged: pick a default.
   - Everything else is a decision: product direction, priority, scope, an accepted risk, or an irreversible or outward action such as a push, deploy, deletion, or external message.
3. Reply with:
   - The decisions, the one blocking the most work first. For each, give the question, the options with what each changes, your recommendation and its reason, and the work it blocks.
   - The defaults you will apply unless the user says otherwise, one line each.
   - With no decisions, say so and name the next step you would take.
