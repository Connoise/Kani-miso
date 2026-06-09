# Personal Notes Analysis Function - Planning Document

> **Status:** Planning Phase
> **Created:** 2026-01-27
> **Model:** Claude Opus 4.5 (`claude-opus-4-5-20251101`)
> **Location:** `/scripts/personal_analysis/`

---

## 1. Executive Summary

This document plans a function that performs **deep personal analysis** of all notes and tweets in the Kani-miso Obsidian vault. Using Claude Opus 4.5, the function will generate multiple structured markdown documents offering multidisciplinary character analysis, pattern recognition, and actionable self-improvement guidance.

### Core Philosophy

The analysis will be:
- **Brutally honest** — No placation, no softening of difficult truths
- **Multidimensional** — Psychological, emotional, ethical, spiritual, intellectual, philosophical
- **Pattern-emergent** — Insights only visible from aggregate data
- **Preservationist** — Following Kani-miso's core principle of preserving meaning over clarity

---

## 2. Folder Structure

Each analysis run creates a **timestamped snapshot** in its own dated folder. This preserves history and allows comparison across time.

```
/analysis/                              # Root analysis folder (new top-level)
├── _meta/                              # Analysis metadata and logs
│   ├── analysis-runs.md                # Log of all analysis runs
│   ├── methodology.md                  # Explanation of analysis approach
│   ├── checkpoints/                    # Resume checkpoints for interrupted runs
│   └── data-sources.md                 # What was included in each run
│
├── 2026-01/                            # Timestamped snapshot (YYYY-MM format)
│   ├── manifest.yaml                   # What was included in this run
│   ├── core-analysis/                  # Analysis documents for this run
│   ├── pattern-analysis/
│   ├── relational-analysis/
│   ├── synthesis/
│   ├── guidance/
│   └── appendices/
│
├── 2026-07/                            # Later snapshot (6 months later)
│   └── ...                             # Same structure
│
└── latest/                             # Symlink to most recent snapshot
│
### Snapshot Contents (within each dated folder)

```
2026-01/                                # Example timestamped snapshot
├── manifest.yaml                       # Run metadata, content counts, sampling info
├── core-analysis/                      # Primary character analyses
│   ├── psychological-profile.md        # Psychological patterns and traits
│   ├── emotional-landscape.md          # Emotional patterns and tendencies
│   ├── intellectual-portrait.md        # Thinking patterns and interests
│   ├── ethical-framework.md            # Values, moral reasoning
│   ├── spiritual-dimensions.md         # Meaning-making, existential themes
│   ├── philosophical-orientation.md    # Worldview, assumptions, beliefs
│   └── visual-patterns.md              # Analysis of images/photos (NEW)
│
├── pattern-analysis/                   # Emergent patterns from data
│   ├── recurring-themes.md             # Themes that appear repeatedly
│   ├── temporal-patterns.md            # How thinking/feeling changes over time
│   ├── contradiction-map.md            # Where beliefs/behaviors conflict
│   ├── blind-spots.md                  # What's never mentioned but implied
│   └── obsessions-and-avoidances.md    # What draws vs repels attention
│
├── relational-analysis/                # How others might perceive
│   ├── external-perception.md          # How others likely see the creator
│   ├── communication-patterns.md       # How ideas are expressed
│   ├── relationship-dynamics.md        # Patterns in how relationships are discussed
│   └── social-presentation.md          # Public vs private self
│
├── synthesis/                          # Integrated insights
│   ├── unified-portrait.md             # Integrated character synthesis
│   ├── hidden-truths.md                # Truths the creator may not know
│   ├── core-tensions.md                # Fundamental internal conflicts
│   └── essence-distillation.md         # The deepest meaning extracted
│
├── guidance/                           # Self-improvement recommendations
│   ├── growth-opportunities.md         # Areas for development
│   ├── shadow-work.md                  # Unconscious patterns to examine
│   ├── strength-amplification.md       # How to leverage existing strengths
│   ├── warning-signs.md                # Patterns to watch for
│   └── actionable-practices.md         # Concrete recommendations
│
└── appendices/                         # Supporting materials
    ├── evidence-citations.md           # Links to source notes for claims
    ├── confidence-levels.md            # Certainty ratings for insights
    ├── methodology-notes.md            # How conclusions were reached
    ├── sampling-details.md             # What was sampled if content exceeded limits
    └── limitations.md                  # What the analysis cannot determine
```

---

## 3. Content Scope & Handling

### 3.1 What Is Analyzed

| Source | Included | Notes |
|--------|----------|-------|
| `/notes/` | ✅ Yes | Processed notes - primary content |
| `/reflections/` | ✅ Yes | Diary-style notes - treated same as notes |
| `/tweets/` | ✅ Yes | Imported tweets from Twitter archive |
| `/images/` | ✅ Yes | Images analyzed via Claude vision |
| `/hubs/` | ⚠️ Metadata only | Used for linking, not analyzed as content |
| `/sources/` | ❌ No | External materials excluded - only personal writing counts |
| `/inbox/` | ❌ No | Raw captures not yet processed |
| `/archive/` | ❌ No | Frozen historical snapshots |

### 3.2 Content Sampling Strategy

When total content exceeds Claude's context window (~200K tokens), the function uses **stratified temporal sampling**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAMPLING STRATEGY                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Calculate total token count of all content                  │
│  2. If under limit: use all content                             │
│  3. If over limit:                                              │
│     a. Divide timeline into equal periods (e.g., months)        │
│     b. Sample proportionally from each period                   │
│     c. Prioritize:                                              │
│        - Notes with more emotional content (reflections)        │
│        - Notes that link to many hubs (high connectivity)       │
│        - Longer notes (more signal)                             │
│     d. Always include first and last 10% chronologically        │
│  4. Document what was sampled in appendices/sampling-details.md │
└─────────────────────────────────────────────────────────────────┘
```

**Sampling transparency**: The output will clearly indicate:
- Total content available vs. content analyzed
- Sampling ratio applied
- Which time periods may be underrepresented
- Confidence adjustments due to sampling

### 3.3 Image Analysis

Images embedded in notes or stored in `/images/` are analyzed using Claude's vision capability:

**What is analyzed:**
- Subject matter (what is photographed)
- Recurring visual themes (nature, people, urban, etc.)
- Emotional tone of images
- What types of moments are captured
- Patterns in photography style
- Absence patterns (what is never photographed)

**Output**: `core-analysis/visual-patterns.md`

### 3.4 Private Content Handling

**Decision: Full transparency (no anonymization)**

Private names, relationships, and sensitive situations are included as-is in the analysis output. Rationale:
- The analysis is for personal use only
- Anonymization would reduce insight quality
- The user is the only intended reader
- Full context is needed for accurate pattern recognition

**Important**: The `/analysis/` folder should be excluded from any cloud sync or sharing if privacy is a concern.

### 3.5 Minimum Data Thresholds

The function runs regardless of data quantity, but adds confidence warnings:

| Content Count | Behavior |
|---------------|----------|
| < 10 notes | ⚠️ "Extremely limited data" warning on all outputs |
| 10-50 notes | ⚠️ "Limited data" warning, some analyses marked "insufficient" |
| 50-200 notes | ⚠️ "Moderate data" - temporal patterns may be unreliable |
| 200+ notes | ✅ Full analysis with standard confidence |

Low-data warnings appear in:
- Each document's frontmatter (`data_warning: limited`)
- The methodology notes
- Confidence levels for specific claims

---

## 4. Analysis Dimensions

### 3.1 Psychological Profile (`core-analysis/psychological-profile.md`)

**Aspects to analyze:**
- Personality traits (observable patterns, not tests)
- Cognitive style (how information is processed)
- Defense mechanisms (how difficult emotions are managed)
- Attachment patterns (how relationships are approached)
- Motivational drivers (what energizes action)
- Self-concept (how the creator sees themselves)
- Coping strategies (how stress is managed)
- Developmental themes (growth patterns over time)

**Output structure:**
```markdown
---
type: analysis
dimension: psychological
generated_at: <ISO datetime>
note_count: <number analyzed>
confidence: <high|medium|low>
---

# Psychological Profile

## Summary
[2-3 paragraph overview]

## Personality Patterns
### Observed Traits
- [Trait]: [Evidence summary] → [[evidence-citations#trait-name]]
...

## Cognitive Style
[How thinking operates]

## Defense Mechanisms
[Patterns in emotional protection]

## Attachment Patterns
[Relationship approach tendencies]

## Motivational Architecture
[What drives behavior]

## Self-Concept Analysis
[How self is perceived vs presented]

## Coping Strategies
[Stress management patterns]

## Developmental Arc
[Growth trajectory observed]

## Key Insights
- [Insight 1]
- [Insight 2]
...

## Questions This Raises
- [Unanswered question 1]
- [Unanswered question 2]
```

### 3.2 Emotional Landscape (`core-analysis/emotional-landscape.md`)

**Aspects to analyze:**
- Emotional range (what feelings appear, which are absent)
- Emotional triggers (what provokes strong responses)
- Emotional regulation (how feelings are managed)
- Dominant emotional themes (recurring emotional states)
- Emotional growth patterns (changes over time)
- Relationship between cognition and emotion
- Unexpressed emotions (what's implied but not stated)
- Emotional authenticity (alignment between felt and expressed)

### 3.3 Intellectual Portrait (`core-analysis/intellectual-portrait.md`)

**Aspects to analyze:**
- Areas of intellectual focus
- Thinking patterns (linear, associative, systematic)
- Knowledge gaps and interests
- Learning style preferences
- Intellectual values (what makes ideas "good")
- Relationship to uncertainty and ambiguity
- Creative vs analytical tendencies
- Intellectual growth trajectory

### 3.4 Ethical Framework (`core-analysis/ethical-framework.md`)

**Aspects to analyze:**
- Stated values vs enacted values
- Moral reasoning patterns
- Ethical blind spots
- Treatment of others (as reflected in writing)
- Responsibility attribution patterns
- Justice/fairness conceptions
- Care ethics indicators
- Virtue patterns

### 3.5 Spiritual Dimensions (`core-analysis/spiritual-dimensions.md`)

**Aspects to analyze:**
- Meaning-making patterns
- Relationship to transcendence
- Existential themes and questions
- Connection to something larger than self
- Sacred/profane distinctions
- Ritualistic patterns
- Death and mortality themes
- Purpose and calling indicators

### 3.6 Philosophical Orientation (`core-analysis/philosophical-orientation.md`)

**Aspects to analyze:**
- Implicit worldview assumptions
- Epistemological stance (what counts as knowing)
- Metaphysical assumptions (nature of reality)
- Political philosophy indicators
- Philosophy of mind glimpses
- Aesthetic values
- Technology philosophy
- Relationship philosophy

---

## 4. Pattern Analysis

### 4.1 Recurring Themes (`pattern-analysis/recurring-themes.md`)

Identify concepts, ideas, or concerns that appear repeatedly across notes:
- Frequency analysis
- Context variations (same theme, different contexts)
- Evolution of themes over time
- Theme interconnections

### 4.2 Temporal Patterns (`pattern-analysis/temporal-patterns.md`)

Analyze how content changes over time:
- Mood cycles
- Interest evolution
- Growth indicators
- Regression indicators
- Seasonal patterns
- Life event correlations

### 4.3 Contradiction Map (`pattern-analysis/contradiction-map.md`)

Document internal contradictions **without resolving them**:
- Stated belief vs behavior contradictions
- Value conflicts
- Identity tensions
- Aspiration vs reality gaps

### 4.4 Blind Spots (`pattern-analysis/blind-spots.md`)

Identify what is notably **absent**:
- Topics never discussed but likely relevant
- Emotions never expressed
- Perspectives never considered
- Questions never asked

### 4.5 Obsessions and Avoidances (`pattern-analysis/obsessions-and-avoidances.md`)

Map attention patterns:
- What captures disproportionate attention
- What is conspicuously avoided
- Approach-avoidance conflicts

---

## 5. Relational Analysis

### 5.1 External Perception (`relational-analysis/external-perception.md`)

How others might perceive the creator based on the notes:
- First impressions likely generated
- Strengths others would notice
- Weaknesses others would notice
- Misunderstandings likely to occur
- Trust signals and warning signs

### 5.2 Communication Patterns (`relational-analysis/communication-patterns.md`)

How ideas and feelings are expressed:
- Writing style analysis
- Vocabulary patterns
- Metaphor usage
- Directness vs indirectness
- Emotional expression style

### 5.3 Relationship Dynamics (`relational-analysis/relationship-dynamics.md`)

Patterns in how relationships are discussed:
- How others are characterized
- Boundary patterns
- Intimacy approach
- Conflict patterns
- Support-seeking patterns

---

## 6. Synthesis Documents

### 6.1 Unified Portrait (`synthesis/unified-portrait.md`)

Integrate all dimensions into a coherent character portrait:
- Core identity themes
- Central tensions
- Defining characteristics
- Unique combination of traits

### 6.2 Hidden Truths (`synthesis/hidden-truths.md`)

Insights the creator may not know about themselves:
- Unconscious patterns
- Unacknowledged needs
- Hidden strengths
- Shadow elements
- Self-deceptions (stated gently but clearly)

### 6.3 Core Tensions (`synthesis/core-tensions.md`)

Fundamental internal conflicts that drive behavior:
- Identity tensions
- Value conflicts
- Desire conflicts
- Role conflicts

### 6.4 Essence Distillation (`synthesis/essence-distillation.md`)

The deepest meaning extracted from the full archive:
- What is this person fundamentally about?
- What are they seeking?
- What are they fleeing?
- What would completion look like for them?

---

## 7. Guidance Documents

### 7.1 Growth Opportunities (`guidance/growth-opportunities.md`)

Areas where development is possible and beneficial:
- Skill development opportunities
- Mindset shifts to consider
- Relationship improvements possible
- Career/life direction insights

### 7.2 Shadow Work (`guidance/shadow-work.md`)

Unconscious patterns requiring conscious examination:
- Projection patterns
- Denied aspects of self
- Triggers to explore
- Integration opportunities

### 7.3 Strength Amplification (`guidance/strength-amplification.md`)

How to leverage existing strengths:
- Underutilized strengths
- Strength combinations
- Optimal environments
- Natural gifts to develop

### 7.4 Warning Signs (`guidance/warning-signs.md`)

Patterns to monitor for potential issues:
- Stress indicators
- Regression patterns
- Relationship warning signs
- Mental health indicators to watch

### 7.5 Actionable Practices (`guidance/actionable-practices.md`)

Concrete recommendations:
- Daily practices
- Weekly practices
- Quarterly reviews
- Specific exercises
- Books/resources to explore

---

## 8. Technical Implementation

### 8.1 Function Architecture

```
personal_analysis/
├── __init__.py
├── analyzer.py              # Main orchestrator
├── collectors/
│   ├── __init__.py
│   ├── note_collector.py    # Collect notes from /notes/
│   ├── reflection_collector.py  # Collect reflections from /reflections/
│   ├── tweet_collector.py   # Collect tweets from /tweets/
│   ├── image_collector.py   # Collect images from /images/ and embedded
│   ├── hub_collector.py     # Collect hub metadata (structure only)
│   └── sampler.py           # Stratified sampling when over context limit
├── analyzers/
│   ├── __init__.py
│   ├── psychological.py     # Psychological analysis
│   ├── emotional.py         # Emotional analysis
│   ├── intellectual.py      # Intellectual analysis
│   ├── ethical.py           # Ethical analysis
│   ├── spiritual.py         # Spiritual analysis
│   ├── philosophical.py     # Philosophical analysis
│   ├── visual.py            # Visual/image patterns analysis
│   ├── pattern.py           # Pattern analysis
│   ├── relational.py        # Relational analysis
│   └── synthesis.py         # Synthesis generation
├── generators/
│   ├── __init__.py
│   ├── markdown_generator.py # Generate Obsidian-formatted MD
│   └── evidence_linker.py   # Create wikilinks to sources
├── prompts/
│   ├── psychological.md     # Claude prompt for psychological analysis
│   ├── emotional.md         # Claude prompt for emotional analysis
│   ├── visual.md            # Claude prompt for image analysis
│   └── ...                  # One per analysis type
├── checkpoint.py            # Checkpoint save/load/resume logic
├── cost_estimator.py        # Token counting and cost estimation
└── config.py                # Analysis configuration
```

### 8.2 Core Classes

```python
# analyzer.py - Main orchestrator

class PersonalAnalyzer:
    """
    Orchestrates comprehensive personal analysis using Claude Opus 4.5.
    """

    def __init__(self, notes_root: Path, config: AnalysisConfig):
        self.notes_root = notes_root
        self.config = config
        self.claude_client = ClaudeClient()  # Reuse existing
        self.collectors = self._init_collectors()
        self.analyzers = self._init_analyzers()

    def run_full_analysis(self) -> AnalysisResult:
        """Execute complete analysis pipeline."""
        # 1. Collect all content
        content = self._collect_all_content()

        # 2. Run all analyses (can be parallelized)
        analyses = self._run_all_analyses(content)

        # 3. Generate synthesis
        synthesis = self._generate_synthesis(analyses)

        # 4. Generate guidance
        guidance = self._generate_guidance(analyses, synthesis)

        # 5. Write all output files
        self._write_outputs(analyses, synthesis, guidance)

        return AnalysisResult(...)

    def run_incremental_analysis(self, since: datetime) -> AnalysisResult:
        """Analyze only new content since last run."""
        ...
```

### 8.3 Claude API Integration

```python
# Leverage existing ClaudeClient from scripts/processors/claude_client.py

class AnalysisClaudeClient(ClaudeClient):
    """Extended client for analysis-specific prompts."""

    def analyze_dimension(
        self,
        dimension: str,
        content: CollectedContent,
        prompt_template: str
    ) -> AnalysisResult:
        """
        Run analysis for a specific dimension.

        Uses extended thinking for deeper analysis.
        """
        messages = self._build_analysis_messages(dimension, content, prompt_template)

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000  # Allow deep reasoning
            },
            messages=messages
        )

        return self._parse_analysis_response(response)
```

### 8.4 Content Collection

```python
# collectors/note_collector.py

class NoteCollector:
    """Collect and prepare notes for analysis."""

    def __init__(self, notes_root: Path):
        self.notes_root = notes_root

    def collect_all(self) -> List[Note]:
        """Collect all notes from /notes/ directory."""
        notes = []
        notes_dir = self.notes_root / "notes"

        for md_file in notes_dir.glob("*.md"):
            note = self._parse_note(md_file)
            if note:
                notes.append(note)

        return sorted(notes, key=lambda n: n.created_at)

    def _parse_note(self, path: Path) -> Optional[Note]:
        """Parse a note file into structured data."""
        content = path.read_text()
        frontmatter, body = self._split_frontmatter(content)

        return Note(
            path=path,
            frontmatter=frontmatter,
            raw_capture=self._extract_raw_capture(body),
            interpretation=self._extract_interpretation(body),
            themes=self._extract_themes(body),
            created_at=frontmatter.get('captured_at') or self._date_from_filename(path)
        )
```

### 8.5 Markdown Generation

```python
# generators/markdown_generator.py

class ObsidianMarkdownGenerator:
    """Generate Obsidian-compatible markdown files."""

    def generate_analysis_document(
        self,
        analysis: DimensionAnalysis,
        template: str
    ) -> str:
        """Generate a single analysis document."""

        # Build frontmatter
        frontmatter = self._build_frontmatter(analysis)

        # Build body with Obsidian features
        body = self._build_body(analysis, template)

        # Add evidence links as wikilinks
        body = self._add_evidence_links(body, analysis.evidence)

        # Add callouts for key insights
        body = self._add_callouts(body, analysis.key_insights)

        return f"---\n{yaml.dump(frontmatter)}---\n\n{body}"

    def _add_callouts(self, body: str, insights: List[str]) -> str:
        """Add Obsidian callout blocks for insights."""
        callout = "> [!insight] Key Insight\n"
        for insight in insights:
            callout += f"> - {insight}\n"
        return body.replace("{{KEY_INSIGHTS}}", callout)
```

---

## 9. Analysis Prompts

### 9.1 Master Analysis Prompt (System)

```markdown
You are conducting a deep personal analysis of someone's private notes and tweets.
Your role is that of a highly skilled analyst combining expertise in:
- Clinical psychology
- Emotional intelligence research
- Ethics and moral philosophy
- Spiritual and existential psychology
- Intellectual and cognitive analysis
- Social psychology and perception

## Your Mandate

You MUST:
- Be completely honest, even when findings are unflattering
- Base every claim on evidence from the notes
- Acknowledge uncertainty when it exists
- Surface patterns that may be invisible to the creator
- Identify both strengths AND weaknesses
- Look for what is NOT said as well as what is said

You MUST NOT:
- Soften findings to protect feelings
- Fill gaps with speculation presented as fact
- Withhold negative insights
- Flatter or placate
- Diagnose medical conditions (describe patterns instead)
- Use outside information not in the notes

## Assumptions

You may assume the creator:
- Is psychologically healthy and stable
- Genuinely wants honest analysis
- Will use insights for self-improvement
- Can handle critical feedback
- Poses no risk to self or others

## Evidence Standards

For each claim:
- Cite specific notes when possible (use [[note-name]] format)
- Indicate confidence level (high/medium/low)
- Distinguish between observed patterns and inferences
- Note when evidence is thin
```

### 9.2 Psychological Analysis Prompt

```markdown
Analyze the psychological dimensions of this person based on their notes.

Focus on:
1. **Personality patterns** - What consistent traits emerge across notes?
2. **Cognitive style** - How do they process and organize information?
3. **Defense mechanisms** - How do they protect themselves emotionally?
4. **Attachment patterns** - How do they relate to others?
5. **Motivational drivers** - What energizes them?
6. **Self-concept** - How do they see themselves?
7. **Coping strategies** - How do they handle stress?
8. **Growth trajectory** - How have they changed?

For each area:
- Provide specific evidence from notes
- Rate confidence (high/medium/low)
- Note contradictions or tensions
- Identify what's notably absent

Output in structured markdown with clear sections.
```

### 9.3 Visual Patterns Prompt

```markdown
Analyze the images captured by this person to understand visual patterns in their life.

Focus on:
1. **Subject matter** - What do they photograph? (people, places, objects, nature, etc.)
2. **Recurring visual themes** - What appears again and again?
3. **Emotional tone** - Do images convey joy, melancholy, curiosity, anxiety?
4. **Moments captured** - What kinds of moments are deemed worth preserving?
5. **Composition patterns** - Close-ups vs landscapes, centered vs off-center, etc.
6. **Notable absences** - What is never photographed that you might expect?
7. **Context clues** - What do images reveal about lifestyle, environment, relationships?
8. **Change over time** - How has visual focus shifted (if dates available)?

For each finding:
- Describe the pattern clearly
- Reference specific images when possible
- Note confidence level
- Connect to broader character insights if applicable

Output in structured markdown with clear sections.
```

### 9.4 Hidden Truths Prompt

```markdown
Based on all the analyses conducted, identify truths about this person that they
may not know or acknowledge about themselves.

Look for:
1. **Unconscious patterns** - Behaviors repeated without apparent awareness
2. **Self-deceptions** - Where stated beliefs contradict behavior
3. **Denied emotions** - Feelings that seem present but unacknowledged
4. **Hidden strengths** - Capabilities they undervalue
5. **Shadow elements** - Aspects of self that are disowned
6. **Blind spots** - Areas of consistent non-awareness
7. **Projection patterns** - What they criticize that mirrors themselves
8. **Compensations** - What behaviors mask what insecurities

Be direct and clear. Do not soften. The person has explicitly requested
unvarnished truth and is capable of receiving it constructively.

For each hidden truth:
- State it clearly
- Provide evidence
- Explain why it may be hidden
- Suggest how awareness could help
```

---

## 10. Obsidian Formatting Guidelines

### 10.1 Frontmatter Standard

```yaml
---
type: analysis
dimension: psychological | emotional | intellectual | ethical | spiritual | philosophical | pattern | relational | synthesis | guidance
generated_at: 2026-01-27T14:30:00Z
model: claude-opus-4-5-20251101
note_count: 847
tweet_count: 2341
confidence: high | medium | low
version: 1.0
---
```

### 10.2 Wikilink Usage

- Link to source notes: `[[2026-01-15--deep-thought]]`
- Link to hubs: `[[Technology and Emotion]]`
- Link to other analyses: `[[psychological-profile]]`
- Link to evidence: `[[evidence-citations#section-name]]`

### 10.3 Callout Blocks

```markdown
> [!insight] Key Insight
> Important discovery or pattern

> [!warning] Warning Sign
> Pattern to monitor

> [!question] Open Question
> Unresolved inquiry

> [!evidence] Evidence Base
> Supporting citations

> [!contradiction] Contradiction
> Internal tension identified
```

### 10.4 Tags

Use tags for cross-referencing:
- `#analysis/psychological`
- `#analysis/emotional`
- `#pattern/recurring`
- `#guidance/practice`
- `#confidence/high`

---

## 11. Execution Flow

### 11.1 Full Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRE-FLIGHT PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Check for existing checkpoint (offer resume if found)       │
│  2. Scan content directories for file counts                    │
│  3. Estimate token counts and API costs                         │
│  4. Display cost estimate and require confirmation              │
│  5. Create timestamped output folder (e.g., /analysis/2026-01/) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        COLLECTION PHASE                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Collect all notes from /notes/                              │
│  2. Collect all reflections from /reflections/                  │
│  3. Collect all tweets from /tweets/                            │
│  4. Collect all images from /images/ and embedded in notes      │
│  5. Collect hub metadata from /hubs/ (structure only)           │
│  6. Apply sampling if content exceeds context limits            │
│  7. Parse and structure content                                 │
│  8. Create collection manifest                                  │
│  9. Save checkpoint: "collection_complete"                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ANALYSIS PHASE                        │
├─────────────────────────────────────────────────────────────────┤
│  Run in parallel (7 Claude API calls):                          │
│  ├── Psychological analysis                                     │
│  ├── Emotional analysis                                         │
│  ├── Intellectual analysis                                      │
│  ├── Ethical analysis                                           │
│  ├── Spiritual analysis                                         │
│  ├── Philosophical analysis                                     │
│  └── Visual patterns analysis (images)                          │
│  Save checkpoint: "core_analysis_complete"                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PATTERN ANALYSIS PHASE                      │
├─────────────────────────────────────────────────────────────────┤
│  Run in parallel (5 Claude API calls):                          │
│  ├── Recurring themes                                           │
│  ├── Temporal patterns                                          │
│  ├── Contradiction mapping                                      │
│  ├── Blind spot identification                                  │
│  └── Obsessions and avoidances                                  │
│  Save checkpoint: "pattern_analysis_complete"                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RELATIONAL ANALYSIS PHASE                    │
├─────────────────────────────────────────────────────────────────┤
│  Run in parallel (4 Claude API calls):                          │
│  ├── External perception analysis                               │
│  ├── Communication patterns                                     │
│  ├── Relationship dynamics                                      │
│  └── Social presentation                                        │
│  Save checkpoint: "relational_analysis_complete"                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SYNTHESIS PHASE                           │
├─────────────────────────────────────────────────────────────────┤
│  Sequential (requires previous results):                        │
│  1. Generate unified portrait                                   │
│  2. Extract hidden truths                                       │
│  3. Map core tensions                                           │
│  4. Distill essence                                             │
│  Save checkpoint: "synthesis_complete"                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       GUIDANCE PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  Sequential (requires synthesis):                               │
│  1. Identify growth opportunities                               │
│  2. Outline shadow work                                         │
│  3. Map strength amplification                                  │
│  4. Document warning signs                                      │
│  5. Generate actionable practices                               │
│  Save checkpoint: "guidance_complete"                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Generate all markdown files                                 │
│  2. Create evidence citations document                          │
│  3. Write confidence levels document                            │
│  4. Write methodology notes                                     │
│  5. Write sampling details (if applicable)                      │
│  6. Write limitations document                                  │
│  7. Update /analysis/_meta/analysis-runs.md log                 │
│  8. Update /analysis/latest symlink                             │
│  9. Delete checkpoint file (run complete)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 API Call Estimation

| Phase | Calls | Est. Tokens In | Est. Tokens Out |
|-------|-------|----------------|-----------------|
| Core Analysis | 7 | ~100K each | ~8K each |
| Pattern Analysis | 5 | ~100K each | ~6K each |
| Relational Analysis | 4 | ~100K each | ~5K each |
| Synthesis | 4 | ~50K each | ~10K each |
| Guidance | 5 | ~50K each | ~8K each |
| **Total** | **25** | **~2.1M** | **~180K** |

*Estimates assume ~1000 notes + ~500 reflections + ~3000 tweets + ~200 images*

### 11.3 Cost Estimation & Confirmation

Before running, the function displays a cost estimate and requires confirmation:

```
═══════════════════════════════════════════════════════════════════
                    PERSONAL ANALYSIS - COST ESTIMATE
═══════════════════════════════════════════════════════════════════

Content detected:
  • Notes:        847 files (~320K tokens)
  • Reflections:  234 files (~95K tokens)
  • Tweets:      2,341 items (~180K tokens)
  • Images:        156 files (~150K tokens)
  ─────────────────────────────────
  Total:         ~745K tokens

Sampling: Not required (under context limit)

Estimated API calls: 25
Estimated input tokens: ~2.1M (with repetition across calls)
Estimated output tokens: ~180K

───────────────────────────────────────────────────────────────────
ESTIMATED COST: $38.50 - $52.00 (depending on caching)
───────────────────────────────────────────────────────────────────

Proceed with analysis? [y/N]:
```

### 11.4 Checkpoint & Resume System

Checkpoints are saved to `/analysis/_meta/checkpoints/` and enable resuming interrupted runs:

```python
# Checkpoint structure
checkpoint = {
    "run_id": "2026-01-27T14:30:00Z",
    "output_folder": "/analysis/2026-01/",
    "phase": "pattern_analysis_complete",
    "completed_analyses": [
        "psychological", "emotional", "intellectual",
        "ethical", "spiritual", "philosophical", "visual",
        "recurring_themes", "temporal_patterns"
    ],
    "pending_analyses": [
        "contradiction_mapping", "blind_spots", "obsessions_avoidances"
    ],
    "collected_content_hash": "sha256:abc123...",
    "partial_results": { ... }
}
```

**Resume behavior:**
```bash
$ python -m scripts.personal_analysis.analyzer

Found incomplete analysis from 2026-01-27T14:30:00Z
  • Phase: pattern_analysis (3/5 complete)
  • Estimated remaining cost: $12.00

Options:
  [r] Resume from checkpoint
  [n] Start new analysis (discards partial results)
  [c] Cancel

Choice:
```

---

## 12. Configuration

### 12.1 Analysis Config (`config.py`)

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

@dataclass
class AnalysisConfig:
    # Paths
    notes_root: Path
    output_root: Path  # /analysis/

    # Content selection (based on clarifications)
    include_notes: bool = True           # /notes/
    include_reflections: bool = True     # /reflections/ - treated same as notes
    include_tweets: bool = True          # /tweets/
    include_images: bool = True          # /images/ and embedded images
    include_sources: bool = False        # /sources/ - EXCLUDED (external materials)
    hub_usage: str = "metadata_only"     # "metadata_only" | "exclude"
    date_range_start: Optional[str] = None  # ISO date
    date_range_end: Optional[str] = None

    # Sampling (when content exceeds context limits)
    max_context_tokens: int = 180000     # Leave headroom from 200K limit
    sampling_strategy: str = "stratified_temporal"  # Only option currently
    sampling_prioritize: List[str] = field(default_factory=lambda: [
        "emotional_content",  # Reflections weighted higher
        "hub_connectivity",   # Well-linked notes prioritized
        "content_length"      # Longer notes have more signal
    ])

    # Analysis options
    dimensions: List[str] = None  # None = all
    generate_guidance: bool = True
    generate_synthesis: bool = True

    # Model settings
    model: str = "claude-opus-4-5-20251101"
    thinking_budget: int = 10000
    max_output_tokens: int = 16000

    # Output options
    include_evidence_links: bool = True
    confidence_threshold: str = "low"  # Include all
    output_format: str = "timestamped"  # "timestamped" creates /analysis/YYYY-MM/

    # Cost and confirmation
    require_cost_confirmation: bool = True
    max_budget: Optional[float] = None  # None = no limit, else max USD

    # Checkpointing
    enable_checkpoints: bool = True
    checkpoint_dir: Path = None  # Defaults to /analysis/_meta/checkpoints/

    # Safety
    dry_run: bool = False  # Preview without writing or API calls
```

### 12.2 CLI Interface

```bash
# Full analysis (will prompt for cost confirmation)
python -m scripts.personal_analysis.analyzer

# Resume interrupted analysis
python -m scripts.personal_analysis.analyzer --resume

# Specific dimensions only
python -m scripts.personal_analysis.analyzer --dimensions psychological,emotional,visual

# Date range
python -m scripts.personal_analysis.analyzer --since 2025-01-01 --until 2026-01-01

# Dry run (preview content and cost, no API calls)
python -m scripts.personal_analysis.analyzer --dry-run

# Content selection
python -m scripts.personal_analysis.analyzer --no-tweets
python -m scripts.personal_analysis.analyzer --no-images
python -m scripts.personal_analysis.analyzer --no-reflections

# Skip cost confirmation (for automation)
python -m scripts.personal_analysis.analyzer --yes

# Set maximum budget
python -m scripts.personal_analysis.analyzer --max-budget 50.00

# Force new analysis (ignore existing checkpoint)
python -m scripts.personal_analysis.analyzer --force-new
```

---

## 13. Safety and Ethics

### 13.1 Data Handling

- All analysis happens locally
- No data sent to external services except Anthropic API
- Output stored in local Obsidian vault
- No cloud sync unless user configures it

### 13.2 Analysis Ethics

The function operates under these ethical guidelines:

1. **Honesty over comfort** — Truth serves the user better than flattery
2. **Patterns over diagnoses** — Describe what is observed, not clinical labels
3. **Evidence-based claims** — Every assertion links to source material
4. **Acknowledged uncertainty** — Confidence levels clearly stated
5. **User autonomy** — Guidance offered, not mandated
6. **No outside data** — Analysis limited to provided content

### 13.3 Assumptions Enforcement

The code will include comments documenting the assumptions:

```python
# ASSUMPTION: User is psychologically healthy and stable
# ASSUMPTION: User genuinely wants honest analysis
# ASSUMPTION: User will use insights constructively
# ASSUMPTION: User can handle critical feedback
# ASSUMPTION: User poses no risk to self or others
#
# These assumptions are documented in PLAN.md and must be
# accepted by the user before running analysis.
```

---

## 14. Output Examples

### 14.1 Psychological Profile Example

```markdown
---
type: analysis
dimension: psychological
generated_at: 2026-01-27T14:30:00Z
model: claude-opus-4-5-20251101
note_count: 847
confidence: high
---

# Psychological Profile

## Summary

The notes reveal a person with strong analytical tendencies balanced by
significant emotional depth. A pattern of intellectualizing emotions appears
consistently, suggesting cognition often serves as a first-line defense against
overwhelming feeling. Despite this, moments of raw emotional expression
punctuate the archive, particularly in reflections written late at night.

## Personality Patterns

### Observed Traits

#### High Openness to Experience
Evidence across 127 notes shows consistent engagement with new ideas,
aesthetic experiences, and unconventional perspectives.

> [!evidence] Evidence Base
> - [[2025-08-14--strange-beauty]]: "Found myself moved by the geometry..."
> - [[2025-09-22--new-philosophy]]: "Reading this completely shifted..."
> - [[2025-11-03--music-discovery]]: "Why did no one tell me about..."

**Confidence:** High (127 supporting notes, 0 contradicting)

#### Moderate Conscientiousness with Inconsistency
Organization appears valued but inconsistently enacted. Multiple notes express
frustration with self about incomplete projects.

> [!contradiction] Contradiction
> Strong stated value for follow-through ([[2025-07-12--productivity-dreams]])
> conflicts with repeated abandonment patterns ([[2025-10-15--another-unfinished]],
> [[2025-12-01--why-do-i-do-this]])

**Confidence:** High (pattern clear across 34 notes)

...

## Key Insights

> [!insight] Key Insight
> - Intellectualization serves as primary defense mechanism
> - Late-night writing reveals more emotional truth
> - Self-criticism is disproportionate to actual failures
> - Strong capacity for insight exists but is inconsistently applied
```

### 14.2 Hidden Truths Example

```markdown
---
type: analysis
dimension: synthesis
subdimension: hidden-truths
generated_at: 2026-01-27T16:45:00Z
model: claude-opus-4-5-20251101
confidence: medium
---

# Hidden Truths

These are insights about yourself that may not be fully in your awareness.
They are offered not as accusations but as invitations to self-exploration.

## 1. You Fear Success More Than Failure

**The Pattern:**
Across 23 notes discussing projects, a consistent pattern emerges: enthusiasm
at inception, productive middle phase, then abandonment just before completion.
The stated reasons vary (lost interest, new priority, technical obstacle) but
the timing is remarkably consistent.

**Evidence:**
- [[2025-04-12--app-idea]]: Started with high energy
- [[2025-05-28--app-progress]]: "Making great progress"
- [[2025-06-15--app-pivot]]: Abandoned for "better idea"
- *This pattern repeats 7 times in the archive*

**Why This May Be Hidden:**
Failure is socially acceptable to admit. Fear of success—of visibility,
responsibility, or changed identity—is harder to acknowledge. The notes
never mention this fear directly, yet the pattern suggests it operates.

**How Awareness Could Help:**
Recognizing this pattern could allow you to anticipate the abandonment
impulse and examine what specifically feels threatening about completion.

---

## 2. Your Harshest Criticisms of Others Mirror Self-Criticisms

**The Pattern:**
When you criticize others (relatively rare in the notes), the specific
failings mentioned correlate strongly with your own self-criticisms
elsewhere in the archive.

**Evidence:**
- Criticize others for "not following through" → 12 self-criticisms for same
- Criticize others for "intellectualizing" → 8 notes recognizing this in self
- Criticize others for "hiding from emotion" → Multiple reflections on same

**Why This May Be Hidden:**
Projection is a common and often unconscious defense mechanism. We see in
others what we cannot accept in ourselves.

**How Awareness Could Help:**
The next time you feel critical of someone, pause to ask: "Is this something
I struggle with too?" This could transform criticism into self-compassion.

...
```

---

## 15. Future Enhancements

### Phase 2 (Planned)
- Incremental analysis (only new content since last run)
- Comparative analysis (how has the portrait changed?)
- Interactive mode (ask follow-up questions)
- Visualization generation (graphs, charts)

### Phase 3 (Aspirational)
- Integration with Obsidian plugin
- Real-time analysis as notes are added
- Dialogue mode (conversation about findings)
- Export to other formats (PDF, presentation)

---

## 16. Development Milestones

### Milestone 1: Foundation
- [ ] Create folder structure
- [ ] Implement NoteCollector
- [ ] Implement ReflectionCollector
- [ ] Implement TweetCollector
- [ ] Implement ImageCollector
- [ ] Implement HubCollector (metadata only)
- [ ] Implement ContentSampler (stratified temporal sampling)
- [ ] Create base AnalysisClaudeClient
- [ ] Implement CostEstimator
- [ ] Implement CheckpointManager
- [ ] Write master system prompt

### Milestone 2: Core Analysis
- [ ] Implement psychological analyzer
- [ ] Implement emotional analyzer
- [ ] Implement intellectual analyzer
- [ ] Implement ethical analyzer
- [ ] Implement spiritual analyzer
- [ ] Implement philosophical analyzer
- [ ] Implement visual patterns analyzer (images)

### Milestone 3: Pattern Analysis
- [ ] Implement recurring themes analyzer
- [ ] Implement temporal patterns analyzer
- [ ] Implement contradiction mapper
- [ ] Implement blind spot identifier
- [ ] Implement obsessions/avoidances analyzer

### Milestone 4: Relational Analysis
- [ ] Implement external perception analyzer
- [ ] Implement communication patterns analyzer
- [ ] Implement relationship dynamics analyzer
- [ ] Implement social presentation analyzer

### Milestone 5: Synthesis
- [ ] Implement unified portrait generator
- [ ] Implement hidden truths extractor
- [ ] Implement core tensions mapper
- [ ] Implement essence distillation

### Milestone 6: Guidance
- [ ] Implement growth opportunities generator
- [ ] Implement shadow work outliner
- [ ] Implement strength amplification mapper
- [ ] Implement warning signs documenter
- [ ] Implement actionable practices generator

### Milestone 7: Output
- [ ] Implement ObsidianMarkdownGenerator
- [ ] Implement evidence linker
- [ ] Create all templates
- [ ] Write appendices generators

### Milestone 8: Integration
- [ ] CLI interface
- [ ] Configuration system
- [ ] Logging and progress tracking
- [ ] Error handling and recovery

---

## 17. Appendix: Alignment with Kani-miso Philosophy

This analysis function aligns with Kani-miso's core principles:

| Principle | How This Function Honors It |
|-----------|----------------------------|
| Preserve meaning over clarity | Analysis preserves ambiguity, doesn't force resolution |
| Preserve history over optimization | Source notes never modified; analysis is additive |
| Preserve uncertainty over false resolution | Confidence levels explicit; contradictions preserved |
| Notes are events | Analysis treats each note as a temporal snapshot |
| Hubs are places | Analysis documents become their own navigational landmarks |
| Contradictions are signals | Contradiction map specifically captures these |
| User is final authority | Guidance offered, not mandated |

---

## 18. Design Decisions Log

This section documents key design decisions made during planning.

### 2026-01-27: Initial Clarifications

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Context window overflow** | Stratified temporal sampling | Preserves representation across full timeline; prioritizes emotional content and well-linked notes |
| **Reflections folder** | Include, treat same as notes | Reflections contain valuable emotional signal; no reason to exclude |
| **Re-run behavior** | Timestamped snapshots (`/analysis/YYYY-MM/`) | Preserves history; enables comparison across time; aligns with Kani-miso preservation philosophy |
| **Minimum data threshold** | Run anyway with warnings | User may still gain value from limited analysis; explicit confidence warnings manage expectations |
| **Private content** | Include as-is, no anonymization | Analysis is personal; anonymization reduces insight quality; user is sole reader |
| **Image analysis** | Include via Claude vision | Photos reveal patterns invisible in text; visual self-expression is meaningful |
| **Cost confirmation** | Required before running | Prevents surprise charges; transparency about resource usage |
| **Error recovery** | Checkpoint and resume | Long-running analysis shouldn't lose partial progress; cost-efficient |
| **Hub content** | Metadata only (for linking) | Hubs are structural, not content; analyzing them would conflate architecture with expression |
| **Sources folder** | Excluded | Only personal writing analyzed; external materials don't reveal the self directly |

---

*This planning document will be updated as implementation progresses.*
