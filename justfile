python := env_var_or_default("SKILLS_SYNC_PYTHON", "python3")

# Reconcile this source checkout; Git refresh is a separate operation.
sync *args:
    {{quote(python)}} "{{justfile_directory()}}/scripts/sync_skills.py" --collection "{{justfile_directory()}}" {{args}}

sync-dry-run *args:
    {{quote(python)}} "{{justfile_directory()}}/scripts/sync_skills.py" --collection "{{justfile_directory()}}" --dry-run {{args}}

# List global skills available to the two intended agents.
list:
    npx --yes skills@1.7.0 list --global --agent claude-code --agent codex

# Explicit user removal; applies to these agents, regardless of collection ownership.
remove name:
    npx --yes skills@1.7.0 remove {{quote(name)}} --global --agent claude-code codex --yes

test:
    {{quote(python)}} -m unittest discover -s tests -v
