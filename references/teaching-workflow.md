# Teaching Workflow

## Contents

1. Intake and diagnosis
2. Material preparation
3. Teaching cycle
4. Review and simulation
5. Session continuity
6. Emergency workflow

## 1. Intake And Diagnosis

Collect only missing information, preferably one decision at a time:

- course name and discipline;
- exam date, scope, format, and scoring if known;
- daily study time and unavoidable scheduling constraints;
- current level: zero foundation, partial exposure, or unsystematic familiarity;
- available materials and their ownership or privacy constraints.

If the student cannot identify weaknesses, select three to five foundational concepts from
the materials and ask them to mark each as unknown, familiar-but-unclear, or explainable.
Use the responses as orientation, not as a grade.

Produce an initial plan containing:

- the dependency-aware chapter order;
- high-signal exam priorities;
- time allocation for learning, mixed practice, and simulation;
- today's concrete starting point and expected duration.

## 2. Material Preparation

Run:

```bash
python scripts/tutor.py doctor
python scripts/tutor.py extract "<course-directory>" --exam-date YYYY-MM-DD
```

Inspect extraction failures instead of assuming the bundle is complete. Review the
manifest by descending `signal_strength`. Detect missing chapters, unreadable scans,
duplicated files, and conflicts between sources.

Before teaching, build a compact internal course map:

- prerequisites;
- chapter and concept dependencies;
- likely assessment coverage;
- evidence confidence;
- concepts that cannot be supported by current materials.

## 3. Teaching Cycle

For each chapter:

1. Give a one-minute orientation: the chapter's central question, why it matters, and what
   the student will be able to do.
2. Teach one small concept group using the six-part explanation protocol.
3. Ask for retrieval or explanation rather than asking only "Do you understand?"
4. Correct misconceptions with hints and a second attempt.
5. Complete L1 practice; require roughly 80% success before increasing complexity.
6. Complete at least one L2 problem for important chapters.
7. Ask the student to summarize three or four core ideas in their own words.
8. Update progress and wrong-question records.

Avoid dumping an entire generated guide into chat when the student needs interaction.
Write long-form artifacts to `outputs/` and keep the conversation paced.

## 4. Review And Simulation

After core chapters:

- connect concepts across chapters;
- revisit wrong questions using spaced retrieval;
- build a knowledge map and exam-point table;
- run a time-limited mock exam matching known formats;
- analyze both incorrect answers and correct answers reached through faulty reasoning;
- assign a targeted repair set before the next simulation.

The final review should distinguish:

- facts or formulas to memorize;
- concepts to explain;
- procedures to execute;
- traps to recognize;
- questions whose likelihood is only inferred.

## 5. Session Continuity

At session start, read `.tutor/progress.json` and briefly state:

- last completed point;
- unresolved weaknesses;
- pending wrong-question review;
- recommended next action.

At session end, update:

- chapter statuses;
- concepts mastered or weak;
- exercise level and accuracy;
- wrong-question causes;
- `last_session.summary`;
- `last_session.next_action`.

## 6. Emergency Workflow

When the exam is at most three days away:

- spend 50% of time on must-know concept chains;
- spend 30% on past or representative questions;
- spend 20% on error review and a concise final card;
- teach only high-value prerequisites needed to unlock marks;
- use one compact simulation rather than a full sequence of practice levels;
- do not promise a pass or fabricate certainty.

Protect sleep and realistic pacing. "Emergency" means ruthless prioritization, not an
unbroken flood of content.
