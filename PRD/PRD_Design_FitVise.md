# FitVise — Design Requirements Document
**Version:** 0.2 — For Design Team Review
**Prepared by:** Product (via AI Coach Specification)
**Status:** Draft — Updated after first architecture sync

> **Naming note:** This product was previously drafted as *CoachMCP* and has been renamed to **FitVise**.

---

## 1. Overview & Vision

FitVise is an **open-source** fitness and nutrition coaching web application. It serves as the **persistent data layer and logging interface** for a user's fitness journey. The intelligence layer (coaching, feedback, workout generation, check-ins) lives in the user's AI client — Claude or any MCP-compatible LLM — connected to FitVise via an MCP server.

The app itself is where users:
- View their programme
- Log workouts and diet
- Track progress over time
- Store body composition data

The AI, via MCP, reads and writes to this app — making it a shared source of truth between the user and their AI coach. The **conversational coaching** (onboarding, weekly check-ins, programme changes) happens **in the AI client**, invoked through FitVise's MCP prompts (slash commands) or copy-paste starter prompts.

**The design must reflect this relationship clearly: the app is the journal; the AI is the coach reading it.**

---

## 2. Target Users

| User Type | Description |
|---|---|
| **Primary User** | Individual on a structured fat loss / recomposition programme. Not a gym expert. Needs clarity, not density. |
| **Self-Hoster (single-user)** | Technically capable individual who runs the app locally for themselves. Cares about data privacy. Expects clean, modern UI. |
| **Self-Hoster (multi-user)** | Someone running a shared instance for several people (e.g., a coach hosting for clients). Multiple isolated users, same instance. |
| **Managed Subscriber** | User on the FitVise-hosted paid instance who just signs up and connects their AI client. |

**Device Priority:** Mobile-first. Most logging happens at the gym or kitchen — one hand, glancing at a screen, mid-workout.

---

## 3. Core Design Principles

### 3.1 Logging Must Be Fast
A user in the middle of a workout should be able to log a set in under 5 seconds. If it takes longer, they won't do it. Every logging interaction must be designed for speed and minimal friction.

### 3.2 Clarity Over Completeness
Do not show everything at once. Surface what matters right now — today's workout, today's log, this week's progress. Historical depth is accessible but not the default view.

### 3.3 Progress Feels Earned
Visual feedback — charts, streaks, milestones — should feel satisfying and meaningful. Not gamified in a hollow way. A waist measurement that has dropped 2 inches over 8 weeks deserves a moment, not just a line on a graph.

### 3.4 Honesty Without Shame
Weight fluctuates. Workouts get skipped. Diet slips happen. The interface must never make a user feel punished for missing a log or seeing a bad number. Language across the entire UI should be neutral and forward-looking.

### 3.5 The AI Coach Is Present But Not Intrusive
There should be a clear, consistent entry point to "talk to your coach" or "check in" — but it shouldn't dominate the interface. The app is the user's space. The AI is an advisor they summon in their own AI client.

---

## 4. Information Architecture

```
FitVise
├── Home / Dashboard
│   ├── Today's workout (quick view)
│   ├── Last logged weight + waist
│   ├── Weekly streak / session count
│   └── Check-in prompt (if Sunday or overdue)
│
├── Programme
│   ├── Current Week View
│   ├── Full 12-Week Overview
│   └── Exercise Library (with form notes, substitutions)
│
├── Log
│   ├── Log Workout (today or past)
│   ├── Log Diet (today or past)
│   └── Log Body Metrics (weight, waist, optional others)
│
├── Progress
│   ├── Weight Trend Chart
│   ├── Waist / Measurement Trend
│   ├── Workout Consistency Calendar
│   ├── Lift Progression (per exercise)
│   └── Non-Scale Victories
│
├── Journal
│   ├── Energy & Recovery Logs
│   ├── Behaviour Flags (slip moments)
│   ├── Check-in History (summaries from the AI)
│   └── Injury / Discomfort Notes
│
└── Settings
    ├── Profile & Goals
    ├── Dietary Preferences & Restrictions
    ├── Connect to AI / MCP Connection Info
    └── Data Export
```

---

## 5. Screen-by-Screen Design Specifications

### 5.0 Connect to Your AI Coach (post-registration)

**Purpose:** Bridge a freshly registered user to their AI client so onboarding can begin. The coaching conversation happens **in the AI client, not in the app** — this screen makes that connection effortless.

**Flow & content:**
- **Step 1 — Connect:** "Add FitVise to your AI client." For managed/multi-user, this launches the **OAuth connect/consent** flow (the user authorizes FitVise in Claude or their MCP client; no keys to copy). For single-user self-host, show the local stdio config + generated key.
- **Step 2 — Status:** a clear **connected / not-connected** indicator.
- **Step 3 — Start onboarding:** once connected, instruct the user to run the onboarding workflow. Two paths, shown together:
  - **Slash command:** "In your AI client, run `/mcp__fitvise__onboard`."
  - **Copy-paste fallback:** a ready starter prompt with a one-tap **Copy** button (for clients that don't surface MCP prompts).

**Design Notes:**
- This is the most important first-run screen — design it as a calm, guided 2–3 step checklist, not a wall of text.
- Make the copy-paste prompt a first-class, obviously-tappable block.
- The app **cannot push a prompt into the AI session** — the UI only provides the slash command and the copy-paste text. Set that expectation gently.

---

### 5.1 Onboarding Flow

**Purpose:** Capture everything the AI needs to generate a personalised programme. **Onboarding is conducted conversationally in the AI client** via the `onboard` MCP prompt (or copy-paste starter). The app's role is to launch it, hold a fallback form, and display the result.

**The app provides three things:**
1. **Launch (see §5.0):** the entry point into the AI-led onboarding conversation.
2. **Fallback in-app wizard:** a step-by-step form (one question per screen, "Step 3 of 8" progress, a short *why we ask* note per step) for users who prefer not to onboard in chat, or whose client lacks prompt support.
3. **Read-only profile display:** once `complete_onboarding` fires, show the captured profile and the locked-in programme; app features unlock at this point.

**Questions to capture (in order):**
1. Name and age
2. Current weight and height
3. Primary goal (fat loss / muscle gain / recomposition / general fitness)
4. Target weight or waist measurement (optional but encouraged)
5. **What kind of training do you want?** (gym / home workout / walk or run / classes such as Zumba / hybrid) — *new; not all users want the same modality*
6. Equipment available (if home/hybrid) and typical session length
7. Diet type (eggetarian / vegetarian / non-veg / vegan / other)
8. Any dietary restrictions or allergies
9. Days available per week for training (2–6)
10. Any injuries, joint issues, or medical considerations
11. Any specific preferences or things to avoid

**Design Notes:**
- The AI-led path should feel like a natural conversation; the fallback wizard mirrors the same questions with tappable option cards, number inputs, and a single free-text field (injuries/preferences). No dense forms.
- Make the **training-modality** question prominent — it changes the entire shape of the programme the AI authors.

---

### 5.2 Dashboard / Home

**Purpose:** Orient the user instantly. What do I do today? How am I doing?

**Layout (mobile):**

```
┌─────────────────────────────┐
│  Good morning, [Name] 👋    │
│  Week 6 · Tuesday           │
├─────────────────────────────┤
│  TODAY'S WORKOUT            │
│  Upper Pull                 │
│  6 exercises · ~50 min      │
│  [ Start Workout ]          │
├─────────────────────────────┤
│  LAST CHECK-IN              │
│  Sunday, 22 Jun             │
│  Weight: 122 kg (↓0.8kg)   │
│  Waist: 49.5 in (↓0.5in)   │
├─────────────────────────────┤
│  THIS WEEK                  │
│  ✅ Mon Rest                │
│  ✅ Tue Upper Pull          │
│  ○  Wed Upper Push          │
│  ○  Thu Lower A             │
│  ○  Fri Lower B             │
│  ○  Sat Full Body           │
│  ○  Sun Check-In            │
├─────────────────────────────┤
│  💬 Talk to your coach      │
└─────────────────────────────┘
```

**Design Notes:**
- The "Talk to your coach" CTA should be persistent but not dominant. A chip or floating button is preferable to a full-width banner.
- The weekly tracker should show rest days, missed sessions, and completed sessions with distinct visual states (don't make missed sessions look alarming — neutral is enough).
- "Start Workout" loads the session view directly with quick-log active.

---

### 5.3 Workout Viewer

**Purpose:** Display the day's exercises with enough detail to perform them confidently. Also show history for each exercise.

**Per Exercise Card:**
- Exercise name
- Sets × Reps target (e.g., 3 × 10–12)
- Last session's weight logged
- A "Form tip" or "Why this exercise" expandable note
- Substitution option (tappable, opens alternatives list)

**Session View (Active Logging Mode):**
- Current exercise highlighted
- Tap to log set: [Weight] × [Reps] — two large number inputs + checkmark
- Previous set visible as reference
- Swipe or "Next Exercise" to advance
- Rest timer (optional, user-toggled)

**Design Notes:**
- This screen is used mid-workout. Inputs must be large enough to tap without precision. No tiny dropdowns.
- Warm-up and cool-down blocks should be collapsible. Open by default for new users; collapsed after first 2 weeks.
- Personal best indicator on each exercise (subtle, not overbearing — perhaps a small gold dot or asterisk).
- For non-gym modalities (walk/run, classes), the session view adapts — e.g., a walk/run session shows distance/duration/pace fields instead of sets × reps.

---

### 5.4 Diet Log

**Purpose:** Quick, friction-free daily food logging focused on patterns, not macros.

**Logging Interface:**
- Four meal slots: Morning / Afternoon / Evening / Night
- Each slot has a free-text field: *"What did you eat?"*
- Optional protein quality tag (tap to add): `High Protein` / `No Protein` / `Mixed`
- Time stamp (auto-filled, editable)
- One-tap flags: `Late eating` / `Sugar craving` / `Skipped meal`

**Design Notes:**
- Do NOT include calorie counters, macro breakdowns, or food databases. This is intentional and should be reflected in the design — there is no search bar for foods.
- The interface should look like a journal entry, not a nutrition app.
- A subtle daily summary at the top: "You've logged 2 of 4 meals today."

---

### 5.5 Body Metrics Log

**Purpose:** Weekly (or ad hoc) body composition snapshot.

**Fields:**
- Weight (kg or lbs — user preference set in onboarding)
- Waist circumference
- Optional: Hip, Chest, Left Arm, Right Thigh
- Body fat % (if available from smart scale — with a visible caveat: *"This is directional only — impedance readings vary"*)
- Notes (free text — e.g., "Felt bloated, period week, travel")

**Design Notes:**
- Measurement fields beyond weight and waist should be hidden by default and revealed via "Add more measurements" toggle.
- The notes field is important — it contextualises anomalous readings. Design it as a first-class field, not an afterthought.
- After saving, show a comparison to the last entry: *"↓ 0.5 kg since last week · Waist unchanged"*

---

### 5.6 Progress Dashboard

**Purpose:** Give the user a meaningful view of their trajectory — not just today's number, but the shape of their journey.

**Components:**

**Weight Trend Chart**
- Line chart, last 12 weeks
- Show 7-day moving average as a smoothed overlay (reduces noise from daily fluctuation)
- Mark key events: check-ins, travel, notable flags
- Y-axis range should be adaptive (don't start at zero — show meaningful variation)

**Waist Trend Chart**
- Same format as weight
- This chart is often more motivating than weight — design it with equal visual prominence

**Workout Consistency Calendar**
- GitHub-style contribution heatmap
- Colour-coded by session type (pull / push / lower / full body / walk / run / class / rest)
- Missed sessions are empty, not red

**Lift Progression (Per Exercise)**
- Accessible from the exercise card (not the main nav)
- Simple bar chart: weight lifted over last 8 sessions
- Show PR clearly

**Non-Scale Victories**
- A simple scrollable log of user-entered wins
- Design like a highlight reel: large text, light background, date stamp
- Examples: *"Belt moved a notch" · "Climbed 3 floors without stopping" · "First time hitting 60 kg RDL"*

---

### 5.7 Energy & Recovery Log

**Purpose:** Capture the body signals that explain performance dips and inform the AI's coaching.

**Fields (daily, post-workout or end-of-day):**
- Energy level today: 1–5 (tap a face or numbered scale — no sliders)
- Sleep last night: number input (hours)
- Soreness: None / Mild / Significant (and location, if Significant)
- Stress level: 1–3 (Low / Medium / High)

**Design Notes:**
- This entire log should take under 30 seconds. If it takes longer, users won't do it.
- Consider making this a bottom sheet that appears after marking a workout complete.
- The history view should show these as small indicator dots on the workout calendar.

---

### 5.8 Behaviour Flag Log

**Purpose:** Identify recurring behavioural patterns without shame.

**How it works:**
- Accessible from the daily log or as a quick-add from anywhere
- User taps one or more predefined flags + optional note
- Flags: `Late night eating` / `Sugar craving` / `Skipped session` / `Stress eating` / `Emotional eating` / `Overate at meal` / `Good choice moment` *(positive flag)*

**Design Notes:**
- Include at least one positive flag ("Good choice moment") — the log should not only record slips.
- These are never shown as counts or statistics to the user directly (to avoid shame spirals). They are surfaced by the AI during check-ins as pattern observations.
- Design the flag UI as neutral chips — no red colour, no warning iconography.

---

### 5.9 Check-In Summary View

**Purpose:** Preserve and display the outcome of each AI check-in for reference.

**Each check-in record contains:**
- Date
- Metrics at time of check-in (weight, waist)
- Session summary that week (sessions completed vs. planned)
- The AI's written summary / key observations
- Next week's targets and goals (as set by the AI)

**Design Notes:**
- Read-only. These are records, not editable.
- Style like a coaching report — slightly different visual treatment from the rest of the app (perhaps a card with a subtle border or header strip).
- Should be searchable or filterable by date.

---

### 5.10 Injury / Discomfort Log

**Purpose:** Track physical issues so the AI can adjust programming proactively.

**Fields:**
- Body area (tap on a body silhouette or select from a list: Left Knee / Right Shoulder / Lower Back / etc.)
- Type: Pain / Discomfort / Stiffness / Swelling
- Severity: 1–5
- When it occurred: During workout / After workout / Unrelated
- Note (free text)

**Design Notes:**
- Body silhouette is a nice-to-have, not required for v1 — a simple dropdown list is acceptable.
- If a user logs the same area twice in 7 days, surface a gentle prompt: *"You've noted discomfort in your left knee twice this week. Consider mentioning this to your coach at your next check-in."*

---

## 6. Key UI Patterns & Components

### 6.1 Number Inputs (Workout Logging)
- Very large tap targets (minimum 48px)
- Increment/decrement buttons visible alongside manual input
- Comma / decimal support for weight (e.g., 22.5 kg)
- Last value pre-filled from previous session

### 6.2 "Talk to Your Coach" Entry Point
- Persistent across the app (bottom bar or floating button)
- The conversational workflows (onboarding, weekly check-in, change workout) are invoked **in the user's AI client** — via MCP prompts/slash commands (e.g. `/mcp__fitvise__weekly_checkin`) or the app's **copy-paste starter prompts**. This is **not** an in-app chat.
- Opens a contextual sheet that: explains "Your coach will see your full history and programme when you start a conversation," offers a one-tap **Copy starter prompt**, and links out to the user's configured AI client.

### 6.3 Contextual Reminders
- Not push notifications (self-hosted apps can't reliably send them)
- In-app banners for: overdue check-in / no workout logged today / no metrics this week
- These should disappear once the action is completed and never persist aggressively

### 6.4 Empty States
- Every screen needs a thoughtful empty state
- Example: empty Progress chart → *"Your first data point will appear after your first check-in. Keep going."*
- No generic "No data available" messages

### 6.5 Settings, Profile & Connection
- Units: kg / lbs, cm / inches — user preference
- Goal display: show current goal prominently, with edit access
- **Connect to AI / MCP info page:** explain what MCP is, walk through connecting (OAuth for managed/multi-user; stdio + key for single-user), show a status indicator (connected / not connected), and surface the FitVise MCP prompts + copy-paste starters
- Data export: JSON and CSV formats, all data the user has entered

---

## 7. Visual Tone & Style Direction

*This section offers direction, not prescription. The design team has full creative latitude within these guardrails.*

**Overall feel:** Clean, calm, and purposeful. Not a "fitness app" in the aggressive neon sense. Closer to a personal journal or a health tracker designed for adults who are serious about change.

**Typography:** Large, readable body text. The app is often used in low-light gym environments or while tired. Prioritise legibility over decorative choices.

**Colour system:** Suggest a restrained palette — one primary action colour, neutral greys for backgrounds and secondary text, with specific semantic colours (e.g., green for completed, amber for logged-but-incomplete, subtle blue for AI/coach-related elements).

**Charts:** Minimal — no 3D, no heavy gradients. Clean axis lines, readable labels, ample whitespace.

**Iconography:** Consistent icon set throughout. Avoid mixing styles. Icons should supplement text labels, not replace them, especially in navigation.

**Dark mode:** Required. Users log at gyms and in the evening. Dark mode should be a first-class experience, not an afterthought.

---

## 8. Open Questions for Design Team

1. How do we visually distinguish between "AI-generated content" (e.g., a workout programme, a check-in summary) and "user-generated content" (logs, metrics)?
2. What is the right model for the weekly training schedule — a horizontal scroll, a vertical list, or a calendar-style grid?
3. *(Resolved in direction)* Onboarding is conducted **in the AI client**, not in an in-app chat. The app needs: a clean "Connect & start onboarding" launch screen (§5.0), a fallback in-app wizard, and a read-only profile result view. How should these three be visually unified?
4. *(Partially resolved)* Multi-user instances (self-host multi & managed) are first-class. The profile/avatar and account-switching UX **does** need to support multiple isolated users in v1. How minimal can this be while staying clear?
5. What is the interaction model for historical log editing? (User logs wrong weight, wants to fix it 2 days later.)
6. Should the Non-Scale Victories log allow images? (Belt hole photo, mirror selfie, etc.)
7. How should the UI adapt per **training modality** (gym vs. walk/run vs. classes) so a non-gym user never sees gym-centric framing?

---

*Document prepared for internal design review. Updated to reflect the first architecture sync: AI-client-led onboarding with copy-paste fallback, the Connect-to-AI flow, the training-modality question, and first-class multi-user/managed support.*
