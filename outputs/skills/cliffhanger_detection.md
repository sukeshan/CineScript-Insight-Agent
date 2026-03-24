# Cliffhanger Detection Skill

## Purpose
Identify potential cliffhangers, suspense points, and hook moments in the script using entities and scene context.

## Instructions

1. **Primary analysis**: Load and analyze `outputs/entity_map.md` first. Look for entities with:
   - High intensity (≥ 0.7)
   - Negative valence (≤ -0.5)
   - Entity types: `cliffhanger`, `tension_build`, `revelation`, `false_death`
   - High position percentage (≥ 75%) — late-placed beats are stronger cliffhanger candidates.

2. **Scene context**: If you need more detail about a specific moment, use `load_file` to read only the relevant `outputs/scenes/scene_XXX_*.md` file. **Never load the full original script.**

3. **Character ties**: Cross-reference with `outputs/character_analysis.md` to identify which characters drive the tension.

## Output Format

When presenting cliffhanger analysis, use this exact structure:

### 🎯 Cliffhanger Summary
> One-sentence highlight of the strongest cliffhanger.

### 📍 Detected Moments
1. **[Scene X]** — Description (Intensity: X/10)
2. **[Scene Y]** — Description (Intensity: X/10)

### 🔗 Entity Ties
- **Character A** — Role in creating tension
- **Object/Event B** — How it amplifies suspense

### 💪 Strength Rating
**X/10** — Brief justification

### 💡 Recommendation
Actionable suggestion to enhance the cliffhanger effect.

### 🃏 Visual Preview
```
Short markdown card snippet ready for UI display.
```

## Activation Keywords
This skill activates when the user asks about: cliffhanger, suspense, hook, episode ending, tension, plot twist, reveal, shocking moment.
