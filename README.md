# ComfyUI-DynamicPromptComposer

A ComfyUI custom node for building varied prompts across batch image or video generations. Split your prompt into independent **sections**, fill each with multiple options, and let each section pick one per run — via random, seeded-random, increment, or fixed mode. All chosen pieces are joined into a clean single-line output string ready to wire into any text encoder.

---

## Installation

### Manual

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Alatza/ComfyUI-DynamicPromptComposer
```

Restart ComfyUI. The node will appear under the **prompt** category.

### ComfyUI Manager

Search for **Dynamic Prompt Composer** in the Manager and install from there.

---

## Usage

Add the **Dynamic Prompt Composer** node to your workflow and connect its `prompt` output to a text encoder or any `STRING` input.

### Sections

Each section represents one independent part of your prompt (subject, style, lighting, mood, etc.). Use the **Add Section** / **Remove Section** buttons to manage sections — up to 10 can be active at once.

Within a section, list your options separated by **newlines** or **pipes (`|`)**:

```
a sunny day
a rainy night | a foggy morning
```

### Modes

Each section has its own mode:

| Mode | Behavior |
|------|----------|
| `random` | Picks one element at true random. Non-reproducible every run — the `seed` input is ignored. |
| `random (seed)` | Picks one element at random using `seed` as the RNG seed. Same seed always produces the same pick. |
| `increment` | Cycles through elements in order across runs. Resets at the start of each new batch. |
| `fixed` | Always picks the element at the **start index**. |

> **`random` vs `random (seed)`** — Use `random` when you want a different result every single run with no way to reproduce it. Use `random (seed)` when you want to explore combinations by changing the seed, but need to be able to go back to a specific result — same seed always yields the same prompt.

### Seed

Used by `random` mode to seed the RNG. Changing the seed changes which elements are picked. Has no effect on `increment` or `fixed` sections.

### Start Index

Shared by `fixed` mode (which element to pin) and `increment` mode (which element to begin from at the start of each batch). Defaults to `0`.

---

## Compatibility

- ComfyUI (latest)
- Python 3.10+

---

## License

MIT
