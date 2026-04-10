# ADR 0005: Evidence-Gated Completion

## Status

Accepted

## Decision

Do not allow tasks to move to `done` unless completion readiness passes.

Current readiness requires:

- at least one passing or warning check, or at least one artifact
- no unresolved blocking dependencies
- no open waiting questions

## Why

- the control plane should explain why work is done
- operators should not need to infer completion from raw terminal output
- reviewer/verifier workflows are stronger when `done` means something concrete

## Consequences

- the gate must live in the shared service layer
- UI and MCP should expose readiness directly so humans and agents can act on it
- future acceptance-criteria features should extend this gate rather than bypass
  it
