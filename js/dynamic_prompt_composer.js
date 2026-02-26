import { app } from "../../scripts/app.js";

const NODE_NAME = "DynamicPromptComposer";
const MAX_SECTIONS = 10;

// ─── widget visibility ───────────────────────────────────────────────────────

function hideWidget(w) {
    if (w._hidden) return;
    w._origComputeSize = w.computeSize;
    w.computeSize = () => [0, -4];
    // Multiline text inputs are real DOM elements; computeSize alone won't hide them.
    if (w.element) {
        w._origDisplay = w.element.style.display;
        w.element.style.display = "none";
    }
    w._hidden = true;
}

function showWidget(w) {
    if (!w._hidden) return;
    w.computeSize = w._origComputeSize;
    delete w._origComputeSize;
    if (w.element) {
        w.element.style.display = w._origDisplay ?? "";
        delete w._origDisplay;
    }
    w._hidden = false;
}

function getSectionWidgets(node, i) {
    return [
        node.widgets?.find((w) => w.name === `section_${i}`),
        node.widgets?.find((w) => w.name === `section_${i}_mode`),
        node.widgets?.find((w) => w.name === `section_${i}_start_index`),
    ];
}

function applyVisibility(node, count) {
    for (let i = 0; i < MAX_SECTIONS; i++) {
        const [textW, modeW, fixedIdxW] = getSectionWidgets(node, i);
        if (!textW || !modeW) continue;
        const active = i < count;
        (active ? showWidget : hideWidget)(textW);
        (active ? showWidget : hideWidget)(modeW);
        if (fixedIdxW) {
            (active ? showWidget : hideWidget)(fixedIdxW);
        }
    }
    node.size[1] = node.computeSize()[1];
    app.graph?.setDirtyCanvas(true);
}

// ─── buttons ─────────────────────────────────────────────────────────────────

function refreshButtons(node) {
    node.widgets = (node.widgets ?? []).filter((w) => !w._dpcButton);

    const addBtn = node.addWidget(
        "button",
        "＋ Add Section",
        null,
        () => {
            const count = node.properties._sectionCount ?? 1;
            if (count >= MAX_SECTIONS) return;
            node.properties._sectionCount = count + 1;
            applyVisibility(node, count + 1);
        },
        { serialize: false }
    );
    addBtn._dpcButton = true;

    const removeBtn = node.addWidget(
        "button",
        "－ Remove Section",
        null,
        () => {
            const count = node.properties._sectionCount ?? 1;
            if (count <= 1) return;
            // Clear the removed section so Python ignores it on future runs
            const [textW] = getSectionWidgets(node, count - 1);
            if (textW) {
                textW.value = "";
                if (textW.element) textW.element.value = "";
            }
            node.properties._sectionCount = count - 1;
            applyVisibility(node, count - 1);
        },
        { serialize: false }
    );
    removeBtn._dpcButton = true;
}

// ─── extension ───────────────────────────────────────────────────────────────

app.registerExtension({
    name: "DynamicPromptComposer.Extension",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        // Fresh node dropped from the menu.
        // setTimeout defers visibility setup until after ComfyUI finishes
        // registering all widget objects, so section_9 is present when we
        // try to hide it.
        const origOnCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origOnCreated?.apply(this, arguments);
            this.properties ??= {};
            this.properties._sectionCount ??= 3;
            // Assume fresh until onConfigure proves otherwise (see below).
            this._dpcIsNew = true;
            const self = this;
            setTimeout(() => {
                applyVisibility(self, self.properties._sectionCount);
                refreshButtons(self);
                // Only double the width for truly new nodes. For nodes loaded
                // from a saved workflow, onConfigure fires synchronously before
                // this setTimeout and clears the flag, so we skip the doubling.
                if (self._dpcIsNew) {
                    self.size[0] *= 2;
                    app.graph?.setDirtyCanvas(true);
                }
            }, 0);
        };

        // Node loaded from a saved workflow
        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (config) {
            // Let LiteGraph restore widget values and node.properties first.
            // Clear the new-node flag so the setTimeout above skips width doubling.
            origOnConfigure?.apply(this, arguments);
            this._dpcIsNew = false;
            const count = this.properties?._sectionCount ?? 1;
            applyVisibility(this, count);
            refreshButtons(this);
        };
    },
});
