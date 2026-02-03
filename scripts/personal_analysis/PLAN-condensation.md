# Analysis Condensation Function - Planning Document

> **Status:** Planning Phase
> **Created:** 2026-02-03
> **Location:** `/scripts/personal_analysis/`
> **Related:** `PLAN.md` (parent analysis function)

---

## 1. Executive Summary

This document plans a function that **condenses all analysis outputs** into a compact, shareable format suitable for:
- Giving to an LLM for continued analysis or conversation
- Sharing with a mental health professional (therapist, counselor, psychiatrist)
- Personal reference for comprehensive self-understanding

The function reads existing analysis markdown files (from `/analysis/YYYY-MM/`) and produces:
1. **Personal Background Document** - Factual biographical information (user-verified)
2. **2-8 Category Summaries** - Condensed insights covering distinct aspects of the person

### Design Philosophy

- **Preserve completeness** — Do not redact information that could be clinically relevant
- **Maximize density** — Every sentence should carry meaning
- **Maintain evidence links** — Keep citations to original notes where possible
- **Enable professional use** — Format for easy review by trained humans
- **Support verification** — User confirms factual information before finalizing

---

## 2. Output Structure

### 2.1 Condensed Documents (Target: 3-8 files)

Output location: `/notes/person-profile/` (within Obsidian vault)

```
/notes/person-profile/
├── 00-personal-background.md      # Factual biographical information
├── 01-psychological-summary.md    # Core psychological patterns
├── 02-emotional-profile.md        # Emotional landscape and regulation
├── 03-cognitive-intellectual.md   # Thinking patterns, interests, learning
├── 04-values-ethics-meaning.md    # Values, ethics, spiritual/existential
├── 05-relational-social.md        # Relationships, communication, social patterns
├── 06-challenges-growth.md        # Current struggles, growth areas, warnings
├── 07-key-themes-tensions.md      # Central threads, contradictions, essence
└── _meta/
    └── condensation-manifest.yaml # What was condensed, when, from what source
```

### 2.2 Personal Background Document Structure

```markdown
---
type: person-profile
category: background
created_at: <ISO datetime>
last_verified: <ISO datetime>
verification_status: verified | partial | unverified
source_analysis: /analysis/YYYY-MM/
---

# Personal Background

> This document contains factual biographical information verified by the subject.
> Last verified: <date>

## Basic Identity
- **Name:** [Full name or preferred identifier]
- **Date of Birth:** [YYYY-MM-DD]
- **Age:** [calculated or stated]
- **Gender Identity:** [as self-identified]
- **Pronouns:** [preferred pronouns]

## Physical Characteristics
- **Height:** [with units]
- **Weight:** [with units]
- **Notable Physical Traits:** [relevant characteristics]

## Location & Origins
- **Current Residence:** [city, region, country]
- **Hometown/Place of Origin:** [childhood location]
- **Significant Locations Lived:** [list with approximate dates]
- **Cultural/Ethnic Background:** [self-identified]

## Education
- **Highest Level Completed:** [degree type]
- **Fields of Study:** [majors, concentrations]
- **Institutions Attended:** [names, dates]
- **Notable Academic Interests:** [subjects of focus]

## Employment & Career
- **Current Occupation:** [job title, field]
- **Career History Summary:** [brief trajectory]
- **Professional Skills:** [key competencies]

## Family & Relationships
- **Relationship Status:** [current]
- **Children:** [number, ages if relevant]
- **Family Structure:** [parents, siblings - living status if relevant]
- **Significant Relationships:** [close friendships, mentors]

## Health Information
### Physical Health
- **Chronic Conditions:** [diagnosed conditions]
- **Medications:** [current prescriptions]
- **Allergies:** [known allergies]
- **Sleep Patterns:** [typical hours, quality]
- **Exercise Habits:** [frequency, type]
- **Diet Notes:** [restrictions, patterns]

### Mental Health
- **Diagnosed Conditions:** [official diagnoses]
- **Current Treatment:** [therapy, medication]
- **Treatment History:** [past interventions]
- **Substance Use:** [alcohol, tobacco, other - frequency]

## Interests & Preferences
### Interests
- [Interest 1]
- [Interest 2]
- ...

### Dislikes/Aversions
- [Dislike 1]
- [Dislike 2]
- ...

### Daily Routines
- **Wake Time:** [typical]
- **Sleep Time:** [typical]
- **Notable Routines:** [relevant patterns]

## Goals & Aspirations
### Short-term Goals (< 1 year)
- [Goal 1]
- [Goal 2]

### Long-term Goals (1-5 years)
- [Goal 1]
- [Goal 2]

### Life Vision
[Brief statement of overall direction/purpose]

## Major Life Events
- **[Year]:** [Event and brief impact]
- **[Year]:** [Event and brief impact]
- ...

## Additional Context
[Any other information relevant for health/growth planning]

---

## Verification Log
| Field | Verified | Date | Notes |
|-------|----------|------|-------|
| Date of Birth | ✓ | 2026-02-03 | |
| Current Residence | ✓ | 2026-02-03 | |
| ... | | | |
```

---

## 3. Category Summary Documents

Each category summary follows this structure:

```markdown
---
type: person-profile
category: <category-name>
created_at: <ISO datetime>
source_analysis: /analysis/YYYY-MM/
confidence: high | medium | low
word_count: <number>
---

# [Category Title]

> Condensed from analysis dated [date]. Confidence: [level].

## Summary
[2-3 paragraph high-level overview]

## Key Patterns
- **[Pattern 1]:** [Description with evidence reference]
- **[Pattern 2]:** [Description with evidence reference]
- ...

## Notable Insights
> [!insight] [Insight title]
> [Detailed insight with citation: [[source-note]]]

## Concerns/Flags
> [!warning] [Concern title]
> [Description of pattern to monitor]

## Contradictions & Tensions
- [Tension 1]: [Description]
- [Tension 2]: [Description]

## Questions for Further Exploration
- [Question 1]
- [Question 2]

## Evidence Base
This summary draws from:
- [[psychological-profile]]
- [[emotional-landscape]]
- [other relevant analysis documents]
```

### 3.1 Category Definitions

| # | Category | Source Documents | Focus |
|---|----------|------------------|-------|
| 01 | Psychological Summary | psychological-profile, hidden-truths, blind-spots | Personality, defense mechanisms, self-concept |
| 02 | Emotional Profile | emotional-landscape, temporal-patterns | Emotional range, triggers, regulation |
| 03 | Cognitive-Intellectual | intellectual-portrait, recurring-themes | Thinking style, interests, learning |
| 04 | Values-Ethics-Meaning | ethical-framework, spiritual-dimensions, philosophical-orientation | Values, morality, meaning-making |
| 05 | Relational-Social | relationship-dynamics, communication-patterns, social-presentation, external-perception | Relationships, communication, social self |
| 06 | Challenges-Growth | growth-opportunities, shadow-work, warning-signs | Current struggles, development areas |
| 07 | Key Themes-Tensions | unified-portrait, core-tensions, essence-distillation, contradiction-map, obsessions-avoidances | Central patterns, fundamental conflicts |

---

## 4. Technical Implementation

### 4.1 Function Architecture

```
personal_analysis/
├── condensers/                    # NEW: Condensation module
│   ├── __init__.py
│   ├── background_condenser.py   # Personal background generation
│   ├── category_condenser.py     # Category summary generation
│   ├── analysis_reader.py        # Read existing analysis files
│   └── user_verifier.py          # Interactive verification
├── generators/
│   └── profile_generator.py      # NEW: Write profile markdown
└── condenser.py                  # NEW: Main orchestrator
```

### 4.2 Core Classes

```python
# condenser.py - Main orchestrator

class AnalysisCondenser:
    """
    Condenses full analysis output into shareable profile documents.
    """

    def __init__(self, notes_root: Path, analysis_folder: Path):
        self.notes_root = notes_root
        self.analysis_folder = analysis_folder
        self.output_folder = notes_root / "notes" / "person-profile"
        self.client = anthropic.Anthropic()

    def run(self, interactive: bool = True) -> CondensationResult:
        """
        Execute the full condensation pipeline.

        Args:
            interactive: If True, prompt user to verify background info
        """
        # 1. Read all analysis documents
        analyses = self._read_all_analyses()

        # 2. Generate personal background (may require extraction from analyses)
        background = self._generate_background(analyses)

        # 3. If interactive, verify background with user
        if interactive:
            background = self._verify_background_with_user(background)

        # 4. Generate category summaries
        summaries = self._generate_category_summaries(analyses)

        # 5. Write all outputs
        self._write_outputs(background, summaries)

        return CondensationResult(...)
```

### 4.3 Analysis Reader

```python
# condensers/analysis_reader.py

@dataclass
class AnalysisDocument:
    """Represents a single analysis document."""
    path: Path
    dimension: str
    content: str
    frontmatter: Dict[str, Any]
    confidence: str
    generated_at: datetime

class AnalysisReader:
    """Reads and parses existing analysis documents."""

    def __init__(self, analysis_folder: Path):
        self.analysis_folder = analysis_folder

    def read_all(self) -> Dict[str, AnalysisDocument]:
        """Read all analysis documents from the folder."""
        documents = {}

        for subfolder in ["core-analysis", "pattern-analysis",
                         "relational-analysis", "synthesis", "guidance"]:
            folder = self.analysis_folder / subfolder
            if folder.exists():
                for md_file in folder.glob("*.md"):
                    doc = self._parse_document(md_file)
                    if doc:
                        documents[doc.dimension] = doc

        return documents

    def read_manifest(self) -> Dict[str, Any]:
        """Read the analysis manifest for metadata."""
        manifest_path = self.analysis_folder / "manifest.yaml"
        if manifest_path.exists():
            return yaml.safe_load(manifest_path.read_text())
        return {}
```

### 4.4 Background Condenser

```python
# condensers/background_condenser.py

class BackgroundCondenser:
    """
    Generates personal background document.

    Extracts factual information from analyses and/or prompts user.
    """

    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def generate(self, analyses: Dict[str, AnalysisDocument]) -> PersonalBackground:
        """
        Generate personal background from analysis content.

        Some fields may be extractable from notes content.
        Others will need to be filled by user.
        """
        # Attempt to extract what can be inferred
        extracted = self._extract_from_analyses(analyses)

        # Create background with extracted + empty fields
        return PersonalBackground(
            basic_identity=extracted.get("basic_identity", {}),
            physical=extracted.get("physical", {}),
            location=extracted.get("location", {}),
            education=extracted.get("education", {}),
            employment=extracted.get("employment", {}),
            family=extracted.get("family", {}),
            health_physical=extracted.get("health_physical", {}),
            health_mental=extracted.get("health_mental", {}),
            interests=extracted.get("interests", []),
            dislikes=extracted.get("dislikes", []),
            goals=extracted.get("goals", {}),
            life_events=extracted.get("life_events", []),
            # Track what was extracted vs needs input
            _extracted_fields=list(extracted.keys()),
            _missing_fields=self._identify_missing(extracted),
        )

    def _extract_from_analyses(self, analyses: Dict) -> Dict:
        """Use Claude to extract factual information from analyses."""
        # Combine relevant analysis content
        content = self._prepare_extraction_content(analyses)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",  # Sonnet sufficient for extraction
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": BACKGROUND_EXTRACTION_PROMPT.format(content=content)
            }]
        )

        return self._parse_extraction_response(response)
```

### 4.5 User Verification Interface

```python
# condensers/user_verifier.py

class UserVerifier:
    """
    Interactive verification of background information.

    Presents extracted/missing information and allows user to confirm/edit.
    """

    def verify(self, background: PersonalBackground) -> PersonalBackground:
        """
        Interactive verification loop.

        Returns updated background with verification status.
        """
        print("\n" + "="*60)
        print("PERSONAL BACKGROUND VERIFICATION")
        print("="*60)
        print("\nPlease verify or provide the following information.")
        print("Press Enter to accept extracted values, or type to correct.\n")

        verified = {}

        # Basic Identity
        verified["basic_identity"] = self._verify_section(
            "Basic Identity",
            background.basic_identity,
            BASIC_IDENTITY_FIELDS
        )

        # Physical Characteristics
        verified["physical"] = self._verify_section(
            "Physical Characteristics",
            background.physical,
            PHYSICAL_FIELDS
        )

        # Continue for all sections...

        # Mark as verified
        background.update(verified)
        background.verification_status = "verified"
        background.last_verified = datetime.now()

        return background

    def _verify_section(
        self,
        section_name: str,
        current: Dict,
        field_definitions: List[FieldDef]
    ) -> Dict:
        """Verify a single section interactively."""
        print(f"\n--- {section_name} ---\n")

        verified = {}
        for field in field_definitions:
            current_value = current.get(field.key, "")
            extracted_marker = " (extracted)" if current_value else " (missing)"

            prompt = f"{field.label}{extracted_marker}"
            if current_value:
                prompt += f" [{current_value}]"
            prompt += ": "

            user_input = input(prompt).strip()

            if user_input:
                verified[field.key] = user_input
            elif current_value:
                verified[field.key] = current_value
            else:
                verified[field.key] = None  # Still missing

        return verified
```

### 4.6 Category Condenser

```python
# condensers/category_condenser.py

class CategoryCondenser:
    """
    Generates condensed category summaries from full analyses.
    """

    CATEGORIES = [
        CategoryDef(
            id="psychological",
            name="Psychological Summary",
            sources=["psychological", "hidden_truths", "blind_spots"],
            prompt=PSYCHOLOGICAL_CONDENSATION_PROMPT,
        ),
        CategoryDef(
            id="emotional",
            name="Emotional Profile",
            sources=["emotional", "temporal_patterns"],
            prompt=EMOTIONAL_CONDENSATION_PROMPT,
        ),
        # ... other categories
    ]

    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def condense_all(
        self,
        analyses: Dict[str, AnalysisDocument]
    ) -> List[CategorySummary]:
        """Generate all category summaries."""
        summaries = []

        for category in self.CATEGORIES:
            # Gather source documents for this category
            source_content = self._gather_sources(analyses, category.sources)

            if not source_content:
                continue  # Skip if no source data

            # Generate condensed summary
            summary = self._condense_category(category, source_content)
            summaries.append(summary)

        return summaries

    def _condense_category(
        self,
        category: CategoryDef,
        source_content: str
    ) -> CategorySummary:
        """Use Claude to condense a single category."""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",  # Sonnet for condensation
            max_tokens=6000,
            messages=[{
                "role": "user",
                "content": category.prompt.format(content=source_content)
            }]
        )

        return CategorySummary(
            category_id=category.id,
            category_name=category.name,
            content=response.content[0].text,
            source_documents=category.sources,
            generated_at=datetime.now(),
        )
```

---

## 5. Prompts

### 5.1 Background Extraction Prompt

```markdown
Extract factual biographical information from the following personal analysis documents.

Return ONLY information that is explicitly stated or strongly implied in the content.
Do NOT infer or guess information that isn't present.

For each field, indicate:
- The extracted value
- The confidence (high/medium/low)
- The source reference if available

If a field cannot be determined from the content, mark it as "unknown".

Content to analyze:
{content}

Extract the following fields:

## Basic Identity
- Name:
- Date of Birth:
- Age:
- Gender Identity:
- Pronouns:

## Physical Characteristics
- Height:
- Weight:

## Location
- Current Residence:
- Hometown:
- Places Lived:

## Education
- Education Level:
- Fields of Study:
- Institutions:

## Employment
- Current Occupation:
- Career Summary:

## Family
- Relationship Status:
- Children:
- Family Structure:

## Health
- Physical Conditions:
- Mental Health Diagnoses:
- Current Treatment:
- Medications:

## Interests
- Interests (list):
- Dislikes (list):

## Goals
- Short-term Goals:
- Long-term Goals:

## Life Events
- Major Life Events (list with dates if known):

Return as structured YAML.
```

### 5.2 Category Condensation Prompt (Psychological)

```markdown
You are condensing a detailed psychological analysis into a concise summary suitable for:
- A mental health professional reviewing a new client
- An LLM that needs context about a person
- Personal reference

Your summary should:
1. Preserve all clinically significant information
2. Use professional, precise language
3. Maintain evidence citations where possible (use [[note-name]] format)
4. Flag concerning patterns clearly
5. Note confidence levels for key claims
6. Keep contradictions and tensions visible (do not resolve them)

Target length: 800-1200 words

Source content:
{content}

Generate a condensed psychological summary following this structure:

# Psychological Summary

## Overview
[2-3 paragraphs capturing the essential psychological portrait]

## Key Patterns
[Bullet points of the most significant patterns]

## Defense Mechanisms
[How this person protects themselves emotionally]

## Self-Concept
[How they see themselves vs. how they present]

## Notable Insights
[The most important discoveries about this person]

## Clinical Considerations
[Patterns a mental health professional should be aware of]

## Confidence Notes
[What we're certain about vs. uncertain]

## Evidence Base
[Key source documents cited]
```

---

## 6. User Interaction Flow

### 6.1 CLI Interface

```bash
# Run condensation with interactive verification
python -m scripts.personal_analysis.condenser

# Run with specific analysis folder
python -m scripts.personal_analysis.condenser --analysis /analysis/2026-01/

# Run non-interactively (skip verification)
python -m scripts.personal_analysis.condenser --non-interactive

# Preview what will be generated
python -m scripts.personal_analysis.condenser --dry-run

# Regenerate only specific categories
python -m scripts.personal_analysis.condenser --categories psychological,emotional

# Update background only (re-verify)
python -m scripts.personal_analysis.condenser --background-only
```

### 6.2 Interactive Session Example

```
═══════════════════════════════════════════════════════════════════
                    ANALYSIS CONDENSATION
═══════════════════════════════════════════════════════════════════

Source: /analysis/2026-01/
Output: /notes/person-profile/

This will generate:
  • Personal Background (with verification)
  • 7 category summaries

Proceed? [Y/n]: y

────────────────────────────────────────────────────────────────────
                    BACKGROUND VERIFICATION
────────────────────────────────────────────────────────────────────

The system extracted some information from your notes.
Please verify or provide missing information.
Press Enter to accept extracted values, or type to correct.

--- Basic Identity ---

Date of Birth (extracted) [1990-05-15]:
Age (calculated) [35]:
Gender Identity (missing): male
Pronouns (missing): he/him

--- Physical Characteristics ---

Height (missing): 5'10"
Weight (missing): 175 lbs

--- Location ---

Current Residence (extracted) [Seattle, WA]:
Hometown (extracted) [Portland, OR]:

--- Health - Mental ---

Diagnosed Conditions (missing): anxiety, depression
Current Treatment (missing): therapy (weekly), sertraline 50mg

[... continues for all sections ...]

────────────────────────────────────────────────────────────────────
                    GENERATING SUMMARIES
────────────────────────────────────────────────────────────────────

  ✓ Psychological Summary (1,024 words)
  ✓ Emotional Profile (892 words)
  ✓ Cognitive-Intellectual (756 words)
  ✓ Values-Ethics-Meaning (834 words)
  ✓ Relational-Social (978 words)
  ✓ Challenges-Growth (712 words)
  ✓ Key Themes-Tensions (1,102 words)

────────────────────────────────────────────────────────────────────
                    COMPLETE
────────────────────────────────────────────────────────────────────

Output written to: /notes/person-profile/

Files generated:
  • 00-personal-background.md (verified)
  • 01-psychological-summary.md
  • 02-emotional-profile.md
  • 03-cognitive-intellectual.md
  • 04-values-ethics-meaning.md
  • 05-relational-social.md
  • 06-challenges-growth.md
  • 07-key-themes-tensions.md
  • _meta/condensation-manifest.yaml

Total: ~6,300 words across 8 documents
```

---

## 7. Personal Background Field Definitions

### 7.1 Core Fields (Essential for Professional Use)

| Category | Field | Type | Importance | Notes |
|----------|-------|------|------------|-------|
| **Identity** | Date of Birth | date | High | Essential for age-related considerations |
| | Age | number | High | Derived from DOB |
| | Gender Identity | string | High | Affects healthcare approaches |
| **Physical** | Height | measurement | Medium | Body image, medical context |
| | Weight | measurement | Medium | Medical context, eating patterns |
| **Location** | Current Residence | location | Medium | Geographic mental health resources |
| | Hometown | location | Medium | Developmental context |
| **Health-Mental** | Diagnosed Conditions | list | Critical | Affects all treatment planning |
| | Current Treatment | list | Critical | Coordination of care |
| | Medications | list | Critical | Drug interactions, compliance |
| **Health-Physical** | Chronic Conditions | list | High | Mind-body connections |
| | Sleep Patterns | description | High | Sleep affects everything |

### 7.2 Extended Fields (Valuable for Comprehensive Understanding)

| Category | Field | Type | Importance | Notes |
|----------|-------|------|------------|-------|
| **Education** | Highest Level | string | Medium | Cognitive context |
| | Fields of Study | list | Low | Intellectual interests |
| **Employment** | Current Occupation | string | Medium | Stress sources, identity |
| | Career History | text | Low | Life trajectory |
| **Family** | Relationship Status | string | High | Support systems, stressors |
| | Children | list | Medium | Responsibilities, motivations |
| | Family Structure | text | Medium | Attachment patterns |
| **Lifestyle** | Exercise Habits | description | Medium | Coping, physical health |
| | Diet/Eating | description | Medium | Eating patterns, nutrition |
| | Substance Use | description | High | Substances affect mental health |
| **Goals** | Short-term | list | Medium | Motivation, direction |
| | Long-term | list | Medium | Life vision |
| **History** | Major Life Events | list | High | Trauma, formative experiences |

### 7.3 Additional Suggested Categories

Based on clinical relevance for health, growth, and future planning:

| Category | Description | Why Important |
|----------|-------------|---------------|
| **Trauma History** | Past traumatic experiences (with consent) | Informs treatment approach |
| **Support Network** | Close relationships, community involvement | Protective factors |
| **Financial Situation** | General stability/stress level | Major stressor for many |
| **Living Situation** | Who lives with, housing stability | Environment affects mental health |
| **Legal History** | Any relevant legal matters | Context for stress/restrictions |
| **Cultural Practices** | Religious, spiritual, cultural activities | Meaning-making, community |
| **Hobbies & Recreation** | How leisure time is spent | Coping, interests, social |
| **Technology Use** | Social media, screen time patterns | Modern mental health factor |
| **Sensory Sensitivities** | Light, sound, touch sensitivities | Neurodivergence indicators |
| **Communication Style** | Preferred ways of communicating | Therapeutic rapport |

---

## 8. Design Decisions (Resolved)

The following decisions have been made:

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Sensitive Information** | Preserve everything | Clinical accuracy requires full context |
| **Evidence Linking** | Include wikilinks | Traceability within Obsidian vault |
| **Multiple Analyses** | Use most recent only | Simplicity; historical versions preserved separately |
| **Missing Information** | Show "Not provided" | Transparency about data gaps |
| **Update Workflow** | Full re-verification each time | Ensures accuracy, user maintains control |
| **Output Length** | No limit | Completeness over brevity |
| **Export Formats** | Markdown only | Sufficient for intended use cases |
| **File Naming** | Timestamped versions | Preserves history of profile evolution |

### 8.1 Remaining Implementation Questions

These questions may arise during development:

1. **Partial Analyses**: What if the source analysis is incomplete (some dimensions failed)?
   - Decision: Generate what's possible with clear warnings

2. **Confidence Aggregation**: How to handle varying confidence across source documents?
   - Decision: Report the range and note lowest confidence prominently

---

## 9. Integration with Second-Brian

### 9.1 Alignment with Core Principles

| Principle | How This Function Honors It |
|-----------|----------------------------|
| Preserve meaning over clarity | Summaries preserve nuance, don't oversimplify |
| Preserve history over optimization | Original analyses untouched; condensed is additive |
| Preserve uncertainty | Confidence levels maintained in output |
| Notes are events | Background captures temporal facts (events, dates) |
| Hubs are places | Profile documents are navigational landmarks |
| Contradictions are signals | Tensions preserved in category summaries |
| User is final authority | Interactive verification gives user control |

### 9.2 Output Location Rationale

Placing output in `/notes/person-profile/` rather than `/analysis/`:
- Visible in Obsidian note graph
- Can be linked to from other notes
- Treated as living documents (can be updated)
- Separate from raw analysis output
- More appropriate for sharing/export

### 9.3 Relationship to Existing Analysis

```
/analysis/2026-01/               # Full analysis (source)
    ├── core-analysis/
    ├── pattern-analysis/
    ├── ...
    └── manifest.yaml

/notes/person-profile/           # Condensed profile (output)
    ├── 00-personal-background.md
    ├── 01-psychological-summary.md
    ├── ...
    └── _meta/
        └── condensation-manifest.yaml  # Links to source
```

---

## 10. Development Milestones

### Milestone 1: Foundation
- [ ] Create `condensers/` module structure
- [ ] Implement `AnalysisReader` (read existing analysis files)
- [ ] Implement `ProfileGenerator` (write output markdown)
- [ ] Create `CondensationConfig` dataclass
- [ ] Create data models (`PersonalBackground`, `CategorySummary`)

### Milestone 2: Background Generation
- [ ] Implement `BackgroundCondenser`
- [ ] Create background extraction prompt
- [ ] Implement `UserVerifier` CLI interface
- [ ] Test extraction accuracy on sample data

### Milestone 3: Category Condensation
- [ ] Implement `CategoryCondenser`
- [ ] Write condensation prompts for all 7 categories
- [ ] Implement source document gathering
- [ ] Test output quality

### Milestone 4: Orchestration
- [ ] Implement main `AnalysisCondenser` class
- [ ] Add CLI interface (`argparse`)
- [ ] Implement manifest generation
- [ ] Add dry-run mode

### Milestone 5: Polish
- [ ] Error handling and edge cases
- [ ] Progress indicators
- [ ] Logging
- [ ] Documentation

---

## 11. Cost Estimation

### 11.1 API Calls

| Phase | Model | Est. Input | Est. Output | Cost |
|-------|-------|------------|-------------|------|
| Background Extraction | Sonnet | ~50K | ~2K | ~$0.18 |
| Psychological Condensation | Sonnet | ~20K | ~2K | ~$0.09 |
| Emotional Condensation | Sonnet | ~15K | ~2K | ~$0.08 |
| Cognitive Condensation | Sonnet | ~15K | ~2K | ~$0.08 |
| Values Condensation | Sonnet | ~20K | ~2K | ~$0.09 |
| Relational Condensation | Sonnet | ~20K | ~2K | ~$0.09 |
| Challenges Condensation | Sonnet | ~25K | ~2K | ~$0.11 |
| Themes Condensation | Sonnet | ~25K | ~2K | ~$0.11 |
| **Total** | | **~190K** | **~16K** | **~$0.83** |

Note: Using Sonnet instead of Opus significantly reduces costs. Condensation is less complex than original analysis.

---

## 12. Appendix: Field Definitions for Verification

```python
# Field definitions for user verification

BASIC_IDENTITY_FIELDS = [
    FieldDef("name", "Full Name", optional=True),
    FieldDef("date_of_birth", "Date of Birth (YYYY-MM-DD)", optional=False),
    FieldDef("age", "Age", derived=True),
    FieldDef("gender_identity", "Gender Identity", optional=True),
    FieldDef("pronouns", "Pronouns", optional=True),
]

PHYSICAL_FIELDS = [
    FieldDef("height", "Height", optional=True),
    FieldDef("weight", "Weight", optional=True),
    FieldDef("notable_traits", "Notable Physical Traits", optional=True),
]

LOCATION_FIELDS = [
    FieldDef("current_residence", "Current City/Region", optional=False),
    FieldDef("hometown", "Hometown/Place of Origin", optional=True),
    FieldDef("places_lived", "Other Significant Places Lived", optional=True),
    FieldDef("cultural_background", "Cultural/Ethnic Background", optional=True),
]

EDUCATION_FIELDS = [
    FieldDef("highest_level", "Highest Education Level", optional=True),
    FieldDef("fields_of_study", "Fields of Study", optional=True),
    FieldDef("institutions", "Schools/Universities Attended", optional=True),
]

EMPLOYMENT_FIELDS = [
    FieldDef("current_occupation", "Current Job/Occupation", optional=True),
    FieldDef("career_summary", "Brief Career History", optional=True),
]

FAMILY_FIELDS = [
    FieldDef("relationship_status", "Relationship Status", optional=True),
    FieldDef("children", "Children (ages if relevant)", optional=True),
    FieldDef("family_structure", "Family Background", optional=True),
]

HEALTH_PHYSICAL_FIELDS = [
    FieldDef("chronic_conditions", "Chronic Physical Conditions", optional=True),
    FieldDef("medications", "Current Medications", optional=True),
    FieldDef("allergies", "Known Allergies", optional=True),
    FieldDef("sleep_patterns", "Typical Sleep (hours, quality)", optional=True),
    FieldDef("exercise", "Exercise Habits", optional=True),
    FieldDef("diet", "Diet/Eating Notes", optional=True),
]

HEALTH_MENTAL_FIELDS = [
    FieldDef("diagnosed_conditions", "Mental Health Diagnoses", optional=True),
    FieldDef("current_treatment", "Current Treatment (therapy, etc.)", optional=True),
    FieldDef("treatment_history", "Past Treatment", optional=True),
    FieldDef("substance_use", "Substance Use (alcohol, etc.)", optional=True),
]

INTERESTS_FIELDS = [
    FieldDef("interests", "Interests/Hobbies (comma-separated)", optional=True),
    FieldDef("dislikes", "Dislikes/Aversions (comma-separated)", optional=True),
]

GOALS_FIELDS = [
    FieldDef("short_term_goals", "Short-term Goals (< 1 year)", optional=True),
    FieldDef("long_term_goals", "Long-term Goals (1-5 years)", optional=True),
    FieldDef("life_vision", "Overall Life Vision", optional=True),
]

LIFE_EVENTS_FIELDS = [
    FieldDef("major_events", "Major Life Events (year: event)", optional=True, multiline=True),
]
```

---

*This planning document is ready for review. Implementation should proceed after clarifying questions in Section 8.*
