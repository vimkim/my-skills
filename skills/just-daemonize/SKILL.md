---
name: just-daemonize
description: Make a project's long-running server, daemon, worker, gateway, or background process reproducible from a cloned repository through just commands. Use when adding or repairing service installation, setup, lifecycle operations, or new-host onboarding.
---

# Just daemonize

Make installation and routine operation reproducible through a small `just` interface. Keep process supervision in one suitable process manager.

## 1. Establish ownership

Inspect the runtime, existing commands, service definitions, configuration, and live processes before changing them. Record each persistent process, one-shot task, scheduled job, dependency, and external service, with its owner and state location.

Manage only this project's instances. Treat existing coding agents and shared gateways as dependencies unless the user explicitly adopts them. Include independent workers and collectors required by the feature. Preserve existing production processes while implementing and testing.

Finish with an inventory that distinguishes what the repository provisions from what the operator must supply.

## 2. Choose one process manager

Reuse a suitable existing manager. For Linux, consider systemd user services when the target host supports them. Compare PM2, Supervisor, Compose, or native platform services only when deployment requirements warrant another choice.

Account for runtime dependencies, privileges, logout and boot behavior, graceful shutdown, logs, and host integration. PM2 adds Node and still needs OS startup integration. Containers change host socket, path, and authentication integration. Use the selected manager's supervision rather than a custom supervisor. Reserve `nohup` for temporary detachment, not full service management.

Finish with one supported manager and a short rationale tied to the target environment. Implement additional backends only when requested.

## 3. Define the just interface

Adapt the following vocabulary to the repository's conventions. Preserve existing command contracts, especially `sync` semantics. Add only commands the project needs.

- `install` installs or builds pinned dependencies and executables.
- `setup` prepares local configuration, registers owned services, and reconciles scheduled jobs.
- `doctor` checks prerequisites, configuration, and required dependencies. Failed required checks return nonzero with an actionable remedy.
- `up`, `down`, and `restart` operate the owned service set. Define which components each command affects.
- `status` inspects without changing state. A successful inspection exits zero even when the service is stopped. Use nonzero for inspection errors.
- `logs` exposes the selected manager's logs with useful filtering or follow options.
- `serve`, when useful, runs in the foreground and refuses a duplicate instance using the same identity or state. Preserve signal handling and exit codes.
- Explicit autostart enable and disable commands control boot behavior when needed. Document any host or login prerequisites separately from starting now.

Keep activation explicit. Installation and setup must not silently start production services. If registration starts a process, defer registration to activation. Define graceful stop, restart, timeout, and automatic restart behavior for the actual application. Keep CLI output focused on state, failures, and the operator's next action.

Finish with a command contract that covers the whole feature, including scheduled work and independent workers.

## 4. Separate source from host state

Version dependency pins or lockfiles, installation and generation code, default configuration examples, scheduled-job definitions, and execution wrappers. Use upstream native service generation when available. Otherwise generate service definitions from portable source templates.

Resolve executable and repository paths at install time. Keep generated machine-specific absolute paths outside Git. Store secrets, runtime databases, logs, and machine or session bindings outside tracked source. Choose stable state locations that survive `down` and reinstallation.

Make setup converge after repetition or partial failure. Preserve credentials and user configuration. Reconcile owned jobs and registrations by stable identity so retries create no duplicates. Restrict replacement and cleanup to owned resources.

Finish when the committed source can recreate the installation without copied host-specific units or credentials.

## 5. Document the new-host flow

Document cloning and prerequisites, followed by the intended sequence:

```sh
just install
just setup
just doctor
just up
just status
```

Adapt that sequence when existing repository commands already provide the same contract. Identify the one-time credential input and host-specific bindings that must be recreated. State which external services remain prerequisites. If existing data must move, document the separate transfer. Explain where operators find configuration, persistent data, logs, and autostart controls.

## 6. Verify the lifecycle

Use an isolated installation, configuration, state directory, service identity, and network endpoints. Check that resolved settings target the isolated resources before running commands. Prefer a rerunnable behavioral check suited to the repository and tool impact over tests that inspect recipe text.

Verify the relevant behavior:

- Install and set up a clean instance. Repeat setup and resume an interrupted setup. Confirm no duplicate jobs or registrations and no loss of secrets, user configuration, or data.
- Start every required component. Check actual process liveness and application readiness. Check one-shot completion and scheduled-job execution. Stop, restart, and inspect the result. Confirm that unrelated processes survive and persistent state remains.
- Exercise foreground mode when present. Check duplicate-instance refusal, signal delivery, shutdown timeout behavior, exit codes, and log access. Observe the configured automatic restart policy after a controlled failure.
- Repeat from an alternate home and installation path. Check missing dependencies and confirm that `doctor` fails usefully while `status` remains read-only.
- Verify autostart registration when present. Claim reboot survival only after an actual reboot test. Report untested boot or logout behavior explicitly.

Finish with the changed files, chosen manager, exercised commands and observed results, remaining prerequisites, and verification limits. Keep service activation and deployment within the user's authorization.
