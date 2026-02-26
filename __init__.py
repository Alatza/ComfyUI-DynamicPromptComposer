from .nodes import DynamicPromptComposer

NODE_CLASS_MAPPINGS = {
    "DynamicPromptComposer": DynamicPromptComposer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicPromptComposer": "Dynamic Prompt Composer",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
