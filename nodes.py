import random
import re

try:
    from server import PromptServer as _PromptServer
    _HAS_SERVER = True
except ImportError:
    _HAS_SERVER = False

SEPARATOR = " "
MAX_SECTIONS = 10

# Keyed by (node_unique_id, section_index); cleared when a new batch starts.
_INCREMENT_COUNTERS: dict = {}
_queue_was_empty: bool = True


def _setup_queue_hook() -> None:
    """Patch PromptServer.send_sync to reset increment counters between batches.

    Logic:
      - When a "status" event shows queue_remaining == 0, mark the queue as empty.
      - On the next "execution_start" after the queue was empty, clear all increment
        counters so the new batch starts from element[0].
      - On "execution_interrupted" (user stops a batch mid-run), clear counters
        immediately so the next batch always starts from element[0].
    """
    if not _HAS_SERVER:
        return
    try:
        server = _PromptServer.instance
        orig_send = server.send_sync

        def _patched_send(event, data, sid=None):
            global _queue_was_empty
            if event == "status":
                try:
                    if data["status"]["exec_info"]["queue_remaining"] == 0:
                        _queue_was_empty = True
                except (KeyError, TypeError):
                    pass
            elif event == "execution_start" and _queue_was_empty:
                _INCREMENT_COUNTERS.clear()
                _queue_was_empty = False
            elif event == "execution_interrupted":
                _INCREMENT_COUNTERS.clear()
            return orig_send(event, data, sid)

        server.send_sync = _patched_send
    except Exception:
        pass


_setup_queue_hook()


class DynamicPromptComposer:
    CATEGORY = "prompt"
    FUNCTION = "compose"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(MAX_SECTIONS):
            optional[f"section_{i}"] = ("STRING", {"multiline": True, "default": ""})
            optional[f"section_{i}_mode"] = (["random", "random (unseeded)", "increment", "fixed"], {})
            optional[f"section_{i}_start_index"] = ("INT", {"default": 0, "min": 0, "max": 99})
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
            "optional": optional,
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    @classmethod
    def IS_CHANGED(cls, seed, **kwargs):
        modes = [v for k, v in kwargs.items() if k.endswith("_mode")]
        if any(m in ("random", "random (unseeded)", "increment") for m in modes):
            return float("NaN")
        return seed

    def compose(self, seed, unique_id=None, **kwargs):
        rng = random.Random(seed)
        parts = []
        node_key = unique_id or "default"

        for i in range(MAX_SECTIONS):
            raw = kwargs.get(f"section_{i}", "")
            mode = kwargs.get(f"section_{i}_mode", "random")
            elements = [e.strip() for e in re.split(r"[\r\n]+|\|", raw) if e.strip()]

            if not elements:
                continue

            if mode == "random":
                chosen = rng.choice(elements)
            elif mode == "random (unseeded)":
                chosen = random.choice(elements)
            elif mode == "increment":
                start_index = kwargs.get(f"section_{i}_start_index", 0)
                key = (node_key, i)
                count = _INCREMENT_COUNTERS.get(key, start_index)
                chosen = elements[count % len(elements)]
                _INCREMENT_COUNTERS[key] = count + 1
            else:  # fixed
                start_index = kwargs.get(f"section_{i}_start_index", 0)
                clamped = min(start_index, len(elements) - 1)
                if start_index > clamped:
                    print(f"[DynamicPromptComposer] section_{i}: start_index {start_index} out of range, clamped to {clamped}")
                chosen = elements[clamped]

            parts.append(chosen)
            print(f"[DynamicPromptComposer] section_{i} ({mode}): '{chosen}'")

        result = re.sub(r"[\r\n]+", " ", SEPARATOR.join(parts)).strip()
        print(f"[DynamicPromptComposer] prompt: '{result}'")
        return (result,)
