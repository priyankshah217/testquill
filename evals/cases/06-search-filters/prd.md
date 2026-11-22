# Search Filters Revamp

## Context

The current filter panel lets users pick contradictory combinations (e.g.
"Free items" with a price range of 100–200) and returns empty results. This
revamp makes filters aware of each other.

## Filters in scope

- **Category** (single select, tree)
- **Price range** (min, max — integers)
- **Free items only** (toggle)
- **Condition** (multi-select: Brand new, Like new, Lightly used, Well used, Heavily used)
- **Deal method** (multi-select: Meetup, Delivery)
- **Distance** (radius: 1 km, 5 km, 10 km, 25 km)
- **Sort** (Best match, Newest, Price low→high, Price high→low, Nearest)

## Interaction rules

1. **Free ↔ Price.** Turning **Free items only** on clears Price
   range. Entering any value in Price range turns **Free items only** off.
2. **Price min ↔ max.** If min > max, swap the two values when the user leaves
   the field. Empty min means 0; empty max means no upper limit.
3. **Deal method ↔ Distance.** Distance is only enabled when **Meetup** is
   selected. If Meetup is deselected, Distance is reset to "Any" and disabled.
4. **Distance / Sort ↔ Location permission.** Distance and the **Nearest** sort
   require location permission. If permission is denied, both are disabled and
   show the helper text *"Turn on location to use this"*. If the user grants
   permission, both become enabled without reopening the panel.
5. **Nearest ↔ Deal method.** Choosing **Nearest** sort automatically selects
   **Meetup** if it isn't already selected. Deselecting Meetup while Nearest is
   active switches sort back to **Best match**.
6. **Free ↔ Price sorts.** When **Free items only** is on, the "Price low→high"
   and "Price high→low" sorts are hidden. If one was active, sort falls back to
   **Best match**.
7. **Category ↔ Condition.** For categories flagged `no_condition` (e.g.
   Services, Property), the Condition filter is hidden and any selected
   conditions are cleared. Switching back to a normal category does **not**
   restore the previous condition selection.

## Panel behaviour

- The **Show N results** button updates live as filters change.
- **Reset** returns every filter to its default: no category, no price, Free
  off, no condition, no deal method, Distance "Any", Sort "Best match".
- Applied filters appear as removable chips above results. Removing a chip
  applies the same interaction rules as changing it in the panel (e.g. removing
  the Meetup chip resets Distance and, if active, the Nearest sort).
