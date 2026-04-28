# Architecture Notes

This project has been reshaped around a few clearer layers so future features
can grow without pushing more logic into a single screen file.

## Current layout

- `lib/main.dart`
  - Thin entry point only.
- `lib/app/`
  - App shell and theme.
- `lib/data/`
  - Repositories and asset loading.
- `lib/models/`
  - Domain models, future rule types, and search/tag metadata.
- `lib/features/home/`
  - Main screen and its current UI flow.
- `lib/damage/`
  - Damage formula helpers.

## Why this helps

The app was previously organized as one large UI file that also owned:

- app bootstrap
- JSON loading
- data parsing
- domain models
- search logic

That structure works for a prototype, but it makes future features expensive.
The new boundaries let us grow in smaller steps.

## Expansion path

The new model layer includes placeholders for:

- `PairTag`
- `PassiveCondition`
- `PassiveEffect`
- `PassiveRule`
- `TeamConfig`

These are intentionally generic so we can model future features like:

- theme skill matching for sync pairs
- search by move effects
- passives that only activate under certain conditions
- teamwide passive resolution
- field and team configuration

## Recommended next refactors

1. Split `home_screen.dart` into smaller widgets:
   - roster picker
   - grid builder
   - overview panel
   - damage calculator panel
2. Normalize more text data into structured tags and effects during import.
3. Add a dedicated team builder feature with its own state object.
4. Move passive activation logic into a standalone rules engine.
