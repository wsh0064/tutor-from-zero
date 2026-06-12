# Visual And Formula Style

## Formula Contract

- Write inline mathematics only as `\(...\)`.
- Write display mathematics only as a standalone `\[...\]` block.
- Keep one complete display expression between the delimiters. Use aligned environments
  inside the block for multi-step derivations.
- Write each formula once. Do not repeat it in plain text, a code fence, an image, or a
  second delimiter style.
- Explain the meaning, conditions, and next reasoning step in prose outside the formula.
- Do not screenshot ordinary typeset formulas. Use an image only for source handwriting,
  unusual source layout, or a question whose visual arrangement is itself relevant.

Example:

```text
当 \(x \ne 1\) 时，可以先约去公共因子：

\[
\begin{aligned}
f(x) &= \frac{x^2-1}{x-1} \\
     &= x+1
\end{aligned}
\]

因此当 \(x \to 1\) 时，函数值趋近于 \(2\)。
```

## Visual Selection

Give every core concept at least one useful visual unless the concept genuinely gains
nothing from visualization. Do not add decorative images merely to satisfy a count.

Use this fixed priority:

1. Reuse a high-quality visual from the course materials.
2. Redraw or adapt a source visual, including changing values for a variation.
3. Generate a new SVG or PNG teaching diagram.
4. Teach with text only and state why a visual would not help.

Label visuals as `资料原图`, `基于资料改编`, or `AI/程序生成`. Never call an adapted or
generated question a past paper question.

## Multimodal Interpretation

- Read `.tutor/visual_catalog.json` before selecting or generating a visual question.
- When direct image inspection is available, inspect the image itself. Use OCR for text
  recovery and search, not as a substitute for visual understanding.
- Require direct visual inspection for coordinates, arrows, topology, spatial
  relationships, geometry, charts, and multi-panel layout.
- Fill `multimodal_description`, `related_concepts`, `usability`, and
  `multimodal_review_status` after inspection when maintaining the catalog.

## Knowledge Navigation

Provide visible rendered diagrams, not raw Mermaid source. At minimum, show:

- chapter or prerequisite dependencies;
- the learner's current position;
- relationships among easily confused concepts.

Prefer Mermaid when the host renders it. For portable artifacts, export the diagram to
SVG or PNG and reference that file from Markdown.

## Visual Questions

Before creating a question, search the visual catalog. Prefer a source visual when it
matches the learning objective. When adapting it, preserve the tested concept, change
only the necessary values or labels, and mark it as adapted. Include alt text and a
source/provenance caption.
