---
name: erp-workspace-panels
description: Build and extend production-grade ERP screens with persistent workspace panels instead of disposable modal dialogs. Use this skill whenever the user asks for invoice, accounting, finance, construction, CRM, or other dense business screens to stay open while navigating menus, dock to a side or bottom area, move/resize/maximize/minimize, preserve unsaved drafts, or let users customize table and form dimensions. Apply it even when the user only describes a visual problem such as a panel covering the header, menu, or line-item table.
compatibility: Vue 3 + TypeScript + Tailwind CSS applications, especially layouts with fixed sidebars and top navigation.
---

# ERP Workspace Panels

Design dense ERP screens as persistent workspaces, not short-lived centered modals. The user may need to inspect account cards, invoices, ledgers, projects, or other menus while an unfinished document remains available. Preserve that mental model in both interaction and implementation.

## Core interaction contract

When adding or repairing a document editor:

1. Open it as a docked workspace panel, normally at the bottom-right of the application content area.
2. Do not close it when the user clicks another menu, the page background, or the application shell.
3. Do not close it on Escape unless the user explicitly chose the ordinary disposable-modal behavior.
4. Provide visible controls for:
   - minimize/“Alta al”
   - restore/“Geri aç”
   - maximize within the application content area
   - return to normal size
   - explicit close
5. Keep the workspace available while the user visits other routes. Show a compact return affordance such as “Fatura taslağına dön”.
6. Restore the unsaved draft when the user returns to the module. Clear it only after successful save or explicit close.

The panel must be useful at every viewport size. Never let a maximized panel cover the fixed top bar or the fixed sidebar. Derive its bounds from the shell variables (for example sidebar width and header height), not from `100vw`/`100vh` alone.

## Position and movement

- Default placement for a new dense document: pin the panel to the content area's top-left corner (after the fixed header and sidebar) and fill the available content area with a small safe inset. This makes all invoice line-item controls visible immediately. Use right-bottom docking only when the product explicitly requests a compact floating start state.
- If the user has previously resized or moved the workspace, restore that custom geometry instead of resetting it. Clamp restored geometry to the current content area when the viewport is smaller.
- Make the title bar draggable when the user requests movable panels. Clamp the panel to the viewport so it cannot be lost off-screen.
- For dense persistent panels, use a ghost drag/resize interaction to keep the form usable while geometry is changing:
  - On pointerdown, measure the panel once, cache its rectangle, create an imperative `position: fixed` ghost outline, and visually reduce the real panel opacity.
  - The ghost must use `pointer-events: none`, a visible dashed outline, a restrained translucent background, and `will-change: transform`.
  - During pointermove, keep the latest event and schedule one `requestAnimationFrame`; never update Vue geometry state or read layout metrics for every raw pointer event.
  - Drag movement should update only the ghost with `transform: translate3d(...)`. Resize movement may update only the ghost's cached `left`, `top`, `width`, and `height`.
  - Do not call `getBoundingClientRect`, `offsetWidth`, `offsetHeight`, `getComputedStyle`, or `localStorage.setItem` from pointermove/rAF movement handlers.
  - On pointerup, cancel the pending frame, apply the final cached geometry to the panel state once, remove the ghost, restore opacity/user selection, persist geometry once, and apply only a short (about 150ms) ease-out transition.
- Do not use a ghost placeholder as a reason to unmount, replace, or lose the form; draft state and controlled `buyuk`/`kucuk` behavior must remain intact.
- Persist the last position if the panel is expected to survive route changes or reloads.
- Persist the last user-selected width and height under a versioned workspace key. Do not treat a stale geometry value as the default for a newly opened workspace.
- On mobile, use the full available content width and account for the mobile navigation state.
- When the sidebar collapses, recompute or express panel bounds using the collapsed sidebar width.
- Avoid putting the panel under a higher-z-index header or sidebar. Use one explicit layering policy for the shell, panel, and floating return control.

## Sizing and line-item tables

Dense invoice/accounting forms should not use a many-column responsive grid that silently compresses inputs.

- Put line items in an intentional horizontal scroll region with a minimum usable width.
- Use a consistent header/data grid with responsive `minmax(0, <weight>fr)` columns by default; preserve user-selected column proportions when resizing.
- Make the description column wider than numeric columns.
- Keep row totals aligned below the row or in a clearly dedicated column.
- Add a “Sütunları ayarla” control when the user needs to adapt the screen to their workflow.
- Let users change each meaningful column width within sensible min/max bounds.
- Persist column widths locally and reload them safely; malformed stored values must fall back to defaults.
- Keep add-row, remove-row, tax-profile, validation, and total behaviors intact while changing layout.

## Compact modal form standard

All forms rendered inside the shared workspace modal should use the same dense, aligned visual language:

- Keep the form centered within a sensible maximum width (normally `58rem` or the panel's usable width).
- Prefer compact field heights around `2.15rem`, reduced horizontal/vertical input padding, and a label-to-control gap around `.25rem`.
- Use tight grid spacing (about `.6rem` vertically and `.75rem` horizontally) instead of large default gaps.
- Keep labels and required markers in one stable line; wrap required markers in a dedicated label-heading element when the label is a flex column.
- Use a minimum usable height for textareas, but do not allow a textarea to force every other field into a new row.
- Preserve responsive behavior: two-column grids on wide panels, one-column fields on narrow/mobile panels.
- Keep action buttons compact and aligned at the form footer.
- Apply this standard through the shared `KayitModal` content shell so finance, accounting, construction, real-estate, administration, and CRM forms remain consistent without duplicating CSS in every view.
- For dense inner sections such as invoice line-item grids, opt into the shell's wide-content mode (`genisIcerik` / `genis-icerik`) so the form can use the full available panel width instead of the compact `58rem` cap. This mode is for wide tables and similar work areas, not ordinary two-column CRUD forms.

## Optional tabbed form structure

When a form has enough fields to become vertically unwieldy, group related fields into an accessible tab strip rather than extending the panel indefinitely:

- Use short Turkish tab labels and a clear active state.
- Keep the tab strip horizontally scrollable on narrow screens.
- Preserve one form state while switching tabs; tab changes must not unmount or reset fields.
- Keep persistent cross-tab content such as notes, attachments, validation feedback, and primary actions outside the tab panels when users need them visible regardless of the active tab.
- Tabs are an opt-in form layout pattern; simple CRUD dialogs should remain simple and must not receive arbitrary tabs.

## Wide work areas

- New dense document panels should open at the content area's top-left and fill the available area by default, subject to restored user geometry.
- A wide work area must use the available panel width before falling back to horizontal scrolling for controls that cannot safely compress.
- Do not impose a large fixed `min-width` on the line-item grid during normal desktop/tablet use; let the grid shrink with its modal. Keep horizontal scrolling available as a narrow-screen fallback and never clip numeric or action columns just to remove scrolling.
- Other modules with comparable schedule, budget, inventory, or transaction grids may use the same wide-content opt-in without changing the shared panel behavior.

## Draft persistence

Use a namespaced storage key per workspace type, for example:

```ts
const STORAGE_KEY = 'erp_<workspace>_draft'
```

Persist the minimum state needed to restore the form:

- form values
- edited record id, if any
- optional panel position and column widths

Write after meaningful reactive changes, not on every unrelated global event. Parse storage defensively and remove invalid JSON. Dispatch a small window event when the draft changes so the application shell can update its return affordance.

## Component strategy

Prefer a reusable panel-capable modal/shell component with opt-in props:

- `kalici` or equivalent: persistent workspace behavior
- `tasinabilir`: draggable title bar
- `buyuk` / `kucuk`: maximize and minimized states
- `disTiklamaKapat`: preserve ordinary modal compatibility

Do not change the behavior of every existing modal by default. Existing CRUD dialogs should remain compatible; opt into workspace behavior only for dense document editors or explicitly requested screens.

## Layout integration

Coordinate the panel with the application shell:

```css
.app-shell {
  --erp-sidebar-width: 280px;
  --erp-header-height: 4rem;
}

.workspace-panel-maximized {
  top: var(--erp-header-height);
  left: var(--erp-sidebar-width);
  right: 1.5rem;
  bottom: 1.5rem;
}
```

Update the variables when the sidebar collapses and when the layout switches to mobile. Keep the return-to-draft control above normal page content but below critical system dialogs.

## Accessibility and visual quality

- Use real buttons with Turkish labels and `aria-label`/`title` values.
- Keep focusable controls out of the drag gesture with `stopPropagation`.
- Give the panel a clear title, active workspace indicator, and close confirmation only when closing would discard meaningful work.
- Ensure scroll containers have visible affordances and do not create nested horizontal scroll accidentally.
- Use restrained enterprise styling: clear hierarchy, compact but readable spacing, strong focus states, and a visually distinct active panel.
- Preserve the project's existing typography, colors, permissions, API contracts, and localization conventions.

## Drag/resize performance contract

Treat raw pointer events as input, not render instructions. A compliant implementation:

- has at most one pending animation frame for a drag or resize gesture;
- coalesces intermediate pointer events so the latest event wins;
- performs layout reads only during gesture setup (and any explicit final measurement), never inside the pointermove path;
- keeps storage writes out of pointermove and writes once on pointerup;
- uses live ghost geometry during the gesture and applies the real geometry only after release;
- cleans up the ghost, animation frame, listeners, inline opacity/user-select styles, and transition state on pointerup, unmount, or cancellation.

When reviewing a panel, explicitly check for layout thrashing, missing rAF throttling, synchronous storage writes, and accidental `left/top` updates on the real form during movement.

## Implementation checklist

Before finishing:

- Verify the panel opens at the intended side/bottom position.
- Verify clicking another route does not destroy the draft.
- Verify returning to the module restores the draft and panel controls.
- Verify minimize/restore and maximize/normal controls are visible and functional.
- Verify maximization starts below the header and to the right of the sidebar.
- Verify dragging clamps inside the available viewport.
- Verify drag/resize uses a ghost outline, latest-event-wins rAF throttling, and does not update the real form on every pointermove.
- Verify pointerup applies geometry once, persists once, restores opacity/user-select, and does not leave a ghost or pending animation frame after unmount.
- Verify line-item columns fit their controls without clipping.
- Verify column width changes persist after reload.
- Run the project's type-check/build and the smallest relevant UI tests.
