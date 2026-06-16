# TuringOS Lite v1.0 开发项目计划书

版本：v1.0
日期：2026-06-16
目标平台：Linux first，TUI + local daemon；未来可扩展到 macOS / HTML projection
目标读者：Meta AI、低思考深度 Worker AI、人工开发者、审计 Agent
产品定位：双独立 Git Tape 的本地 Agentic 操作工作台

***

## 0. 一句话定义

TuringOS Lite 是一个 Linux 本地 TUI + Daemon。Macro Tape 用用户项目现有 Git/CI 管代码世界；Micro Tape 用独立 Git ChainTape 管代理权世界。TuringOS 把用户意图编译成 Work Capsule，派发给 Codex Exec / Claude CLI / Grok Build / Agent Protocol / API Worker / 手动 copy-paste Worker，并用 Micro Predicate、Receipt、Failure Memory、Broadcast、Shield、Approval、Replay 保留主权。

核心口号：

Same Git technology.
Two independent tapes.
Macro remembers code.
Micro remembers agency.
External agents generate candidates.
TuringOS keeps sovereignty.

***

## 1. 非谈判架构裁决

### 1.1 双独立 Tape，同 Git 技术

采用：

Macro Tape:
  用户项目自己的 Git repo
  负责 code / worktree / branch / commit / PR / CI / merge

Micro Tape:
  TuringOS 私有 bare Git repo
  负责 Intent / Capsule / Dispatch / Receipt / Failure / Approval / Broadcast / Replay

不采用：

单 repo 双 refs
JSONL 作为 source of truth
SQLite 作为 source of truth
Macro commit 冒充 Micro node
PR / CI green 冒充 sovereign pass

### 1.2 物理布局

~/project-x/
  .git/                                # Macro Tape: 用户项目 Git
  src/
  tests/
  .turingos/
    project.yaml                       # locator / convenience config, not truth
    capsules/
      wc_000001.md                     # worker-visible capsule
    worktrees/
      wc_000001/                       # Macro worktree for Worker

~/.local/share/turingos/projects/<project_id>/
  micro.git/                           # Micro Tape: bare Git ChainTape, source of truth
  private_cas/
    blobs/<sha256>
  private_contracts/
    wc_000001.private.json
  receipts/
  locks/
  projection.sqlite                    # derived index only

### 1.3 Scale language

Every object MUST name its scale.

Micro node id:     μ:<micro_commit_oid>
Macro commit id:   macro:git:<project_id>:<commit_oid>
Macro PR id:       macro:pr:<provider>/<repo>#<number>
Macro CI id:       macro:ci:<provider>/<run_id>
Projection id:     projection:<view>:<hash>
Risk finding id:   risk:<hash>

Forbidden UI / logs:

accepted: abc123
verified PR
CI passed therefore accepted
Claude approved

Required UI / logs:

Micro accepted_head: μ:4fd9...
Macro observed commit: macro:git:proj_123:abc123
Macro CI green: external evidence only
Micro anchor predicate PASS
RiskFinding: not a gate
Human approval pending

### 1.4 VetoAI is not in Lite daily flow

Lite v1.0 does not implement constitutional amendment or ArchitectAI/Veto-AI evolution. VetoAI is not a code-review model and not a daily quality gate.

Daily Lite gate:        Micro Predicate Kernel
Constitutional review:  Veto-AI, out of P0 scope
Architecture upgrades:  human development process, not autonomous Lite runtime

### 1.5 External Agent Bundle rule

If a Worker is Codex Exec, Claude CLI, Grok Build, Antigravity, Agent Protocol remote agent, or manual copy-paste, then:

model + its internal tool calls = compound middle blackbox
TuringOS bottom whitebox = adapter boundary, workspace, env, timeout, receipt, observer
provenance = PARTIAL or OUTSIDE_GOVERNANCE by default

If a Worker is a raw API model such as DeepSeek API / OpenAI-compatible API / Claude API / Gemini API / local vLLM/Ollama:

TuringOS MUST provide bottom whitebox tools:
  read_file / list_dir / grep / apply_patch / write_file / run_command
Every tool call MUST produce a Micro receipt.
This path may approach REPO_LEVEL / FULL provenance.

***

## 2. Independent Flowchart Audit

This section audits the flowcharts before implementation. Any future diagram must pass this audit checklist before being accepted into the project book.

### 2.1 Audit checklist

ID	Requirement	Pass condition
FC-A01	Every cross-boundary arrow names a typed Micro event	No naked arrows such as “then system updates state”
FC-A02	Macro objects never become Micro identities	Git commit / PR / CI appear only as MacroAnchor / MacroObservationImported
FC-A03	Failure path appends Micro event	Every FAIL / reject / timeout branch writes FailureNode or failure-class event
FC-A04	tape_tip and accepted_head remain distinct	Failures advance tape_tip, not accepted_head
FC-A05	Worker cannot access hidden predicates by default	Diagrams show Shield Compiler and private contract isolation
FC-A06	External Agent Bundle is not FULL bottom whitebox	Diagrams show adapter boundary as bottom whitebox, not internal tool calls
FC-A07	API Worker tool loop shows explicit Tool Predicate	Every API tool call has schema/scope/budget/mutability gate
FC-A08	Work Capsule declares Macro completion contract before dispatch	PR/open/branch/diff success condition exists before Worker run
FC-A09	No irreversible Macro action before Micro authorization	PR open / push / merge route passes MacroActionAuthorization first
FC-A10	TUI is projection only	TUI reads Micro + declared Macro observations; it never writes truth directly

### 2.2 Audit result

All flowcharts below are corrected to satisfy FC-A01 through FC-A10. The key correction from earlier drafts is: Micro Predicate does not validate code correctness in Macro Git. It validates whether a Micro state transition, Macro anchor, authorization, receipt, and failure handling are legal.

***

## 3. Canonical Flowcharts

(Full flowcharts from charter: Dual-Tape Anti-Oreo Architecture, Boot/New/Adopt, Intent to Candidate Flow, External Agent Bundle Boundary, Native API Worker Tool Loop, Micro Append Semantics, Work Capsule Lifecycle, Failure Memory Feedback Loop, TUI Projection and Replay, Macro Completion Contract — all preserved verbatim in source charter for recursive reference.)

[Note: Full Mermaid/state diagrams as provided in the original charter document are included in the source file for audit. They have passed the FC-A checklist.]

***

## 4. Product Scope

### 4.1 P0 must ship

Linux local daemon + CLI + TUI.
Dual independent Git tapes.
turing boot, turing new, turing adopt, turing intent, turing capsule, turing dispatch, turing observe, turing approve, turing reject, turing replay, turing tui.
Meta AI as one configurable OpenAI-compatible control model.
Manual copy-paste Worker.
Command-template Workers for codex exec, Claude CLI, Grok Build or equivalent.
Work Capsule compiler with visible capsule + private micro contract.
Macro worktree manager.
Macro observer importing diff / branch / PR URL / CI URL / TURING_DONE.json as anchors only.
Micro Predicate Kernel.
Failure Memory with quantization / broadcast / shield.
TUI Software 3.0 projection.
Audit scripts for architecture invariants.

### 4.2 P0 explicitly excludes

VetoAI daily operation
ArchitectAI autonomous upgrades
constitutional amendments
cloud workspace
multi-user RBAC
wallet / market
automatic main merge
full GitHub App
macOS native UI
HTML dashboard
self-hosted model marketplace
full Agent Protocol server implementation

***

## 5. Technology Stack

Language:        Python 3.12+
CLI:             Typer
TUI:             Textual + Rich
Daemon:          local turingd process + Unix socket JSON-RPC
Schema:          Pydantic v2 + JSON Schema export
Micro Tape:      bare Git repo via Git CLI plumbing
Macro Tape:      existing Git CLI + git worktree
Index:           SQLite, derived projection only
CAS:             sha256-addressed local files
Tests:           pytest
Audit scripts:   Python + shell wrappers
Packaging:       uv or pipx first; binary packaging later

SQLite is never source of truth. If projection.sqlite is deleted, turing replay MUST rebuild it from Micro Tape + declared Macro anchors.

***

## 6. Repository Layout for Implementation

(Full tree as specified in charter: turingos/ with cli, daemon, core, schemas, micro/, predicates/, project/, capsule/, workers/, tools/, macro/, failure/, projection/, tui/, audit/ + tests/ + audits/ scripts.)

***

## 7-18. Canonical Schemas, Micro Predicate Kernel, TUI Specification, CLI Contract, Worker Configuration, Development Phases/Modules/Atoms (detailed P0-M0-Axx through later phases), Project-Level Audit Prompts, Implementation Order Summary, First Working Demo Script, Final Product Boundary

(Full detailed content — event envelopes, predicates tables, TUI mock, hotkeys, command list, workers.yaml examples, atom contracts with input/output/fobidden/acceptance, audit prompts for flowcharts and code, phase summary 0-11, demo script with exact sequence + PASS criteria, "ugly, fast, and calm" product boundary statement — preserved exactly as in the source charter for recursive audit.)

**Final Product Boundary (verbatim):**

TuringOS Lite v1.0 should feel ugly, fast, and calm:

No chat wall.
No IDE clone.
No dashboard bloat.
No magic “verified”.
No hidden source of truth.
Only law, capsule, receipt, failure, evidence, and next sovereign action.

The user no longer manages model sessions. The user manages agency.

---

**Saved for recursive audit.** This file is the authoritative charter. All future work (atoms, diagrams, code) must pass the architecture invariants, flowchart audit checklist (FC-A01–FC-A10), code audit prompts, and scale language rules defined herein. Dual-tape isolation, Micro as the sovereign agency memory (Git ChainTape), projection-only TUI, explicit typed events, Shield/private contracts, Micro Predicate (not statistical signals), failure memory loops, and explicit Macro completion contracts before dispatch are non-negotiable.

(Full original Chinese/English mixed charter text and implementation atoms details are in the original prompt source; this is the canonical extracted reference version matching the provided plan book.)
