"""
Data models for analysis condensation.

These models represent personal background information and condensed summaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


@dataclass
class FieldDef:
    """Definition of a background field for verification."""

    key: str
    label: str
    optional: bool = True
    multiline: bool = False
    derived: bool = False  # If True, calculated from other fields
    example: Optional[str] = None


@dataclass
class CategoryDef:
    """Definition of a condensation category."""

    id: str
    name: str
    filename: str
    sources: List[str]  # Analysis dimensions to draw from
    description: str


# Field definitions for each section
BASIC_IDENTITY_FIELDS = [
    FieldDef("name", "Full Name", optional=True, example="John Smith"),
    FieldDef("date_of_birth", "Date of Birth (YYYY-MM-DD)", optional=False, example="1990-05-15"),
    FieldDef("age", "Age", derived=True),
    FieldDef("gender_identity", "Gender Identity", optional=True, example="male"),
    FieldDef("pronouns", "Pronouns", optional=True, example="he/him"),
]

PHYSICAL_FIELDS = [
    FieldDef("height", "Height", optional=True, example="5'10\" or 178cm"),
    FieldDef("weight", "Weight", optional=True, example="175 lbs or 79kg"),
    FieldDef("notable_traits", "Notable Physical Traits", optional=True),
]

LOCATION_FIELDS = [
    FieldDef("current_residence", "Current City/Region", optional=True, example="Seattle, WA"),
    FieldDef("hometown", "Hometown/Place of Origin", optional=True, example="Portland, OR"),
    FieldDef("places_lived", "Other Significant Places Lived", optional=True, multiline=True),
    FieldDef("cultural_background", "Cultural/Ethnic Background", optional=True),
]

EDUCATION_FIELDS = [
    FieldDef("highest_level", "Highest Education Level", optional=True, example="Bachelor's degree"),
    FieldDef("fields_of_study", "Fields of Study", optional=True, example="Computer Science, Psychology"),
    FieldDef("institutions", "Schools/Universities Attended", optional=True, multiline=True),
]

EMPLOYMENT_FIELDS = [
    FieldDef("current_occupation", "Current Job/Occupation", optional=True, example="Software Engineer"),
    FieldDef("career_summary", "Brief Career History", optional=True, multiline=True),
]

FAMILY_FIELDS = [
    FieldDef("relationship_status", "Relationship Status", optional=True, example="married"),
    FieldDef("children", "Children (ages if relevant)", optional=True, example="2 children (ages 5, 8)"),
    FieldDef("family_structure", "Family Background", optional=True, multiline=True),
]

HEALTH_PHYSICAL_FIELDS = [
    FieldDef("chronic_conditions", "Chronic Physical Conditions", optional=True),
    FieldDef("medications", "Current Medications", optional=True),
    FieldDef("allergies", "Known Allergies", optional=True),
    FieldDef("sleep_patterns", "Typical Sleep (hours, quality)", optional=True, example="7 hours, restless"),
    FieldDef("exercise", "Exercise Habits", optional=True, example="Running 3x/week"),
    FieldDef("diet", "Diet/Eating Notes", optional=True),
]

HEALTH_MENTAL_FIELDS = [
    FieldDef("diagnosed_conditions", "Mental Health Diagnoses", optional=True, example="anxiety, depression"),
    FieldDef("current_treatment", "Current Treatment (therapy, etc.)", optional=True, example="weekly therapy"),
    FieldDef("treatment_history", "Past Treatment", optional=True, multiline=True),
    FieldDef("substance_use", "Substance Use (alcohol, etc.)", optional=True, example="occasional alcohol"),
]

INTERESTS_FIELDS = [
    FieldDef("interests", "Interests/Hobbies (comma-separated)", optional=True, example="reading, hiking, cooking"),
    FieldDef("dislikes", "Dislikes/Aversions (comma-separated)", optional=True, example="crowds, small talk"),
]

GOALS_FIELDS = [
    FieldDef("short_term_goals", "Short-term Goals (< 1 year)", optional=True, multiline=True),
    FieldDef("long_term_goals", "Long-term Goals (1-5 years)", optional=True, multiline=True),
    FieldDef("life_vision", "Overall Life Vision", optional=True, multiline=True),
]

LIFE_EVENTS_FIELDS = [
    FieldDef("major_events", "Major Life Events (year: event)", optional=True, multiline=True,
             example="2015: Graduated college\n2018: First job\n2020: Moved to Seattle"),
]

# All field sections
ALL_FIELD_SECTIONS = {
    "basic_identity": ("Basic Identity", BASIC_IDENTITY_FIELDS),
    "physical": ("Physical Characteristics", PHYSICAL_FIELDS),
    "location": ("Location & Origins", LOCATION_FIELDS),
    "education": ("Education", EDUCATION_FIELDS),
    "employment": ("Employment & Career", EMPLOYMENT_FIELDS),
    "family": ("Family & Relationships", FAMILY_FIELDS),
    "health_physical": ("Health - Physical", HEALTH_PHYSICAL_FIELDS),
    "health_mental": ("Health - Mental", HEALTH_MENTAL_FIELDS),
    "interests": ("Interests & Preferences", INTERESTS_FIELDS),
    "goals": ("Goals & Aspirations", GOALS_FIELDS),
    "life_events": ("Major Life Events", LIFE_EVENTS_FIELDS),
}


# Category definitions for condensation
CATEGORY_DEFINITIONS = [
    CategoryDef(
        id="psychological",
        name="Psychological Summary",
        filename="01-psychological-summary",
        sources=["psychological", "hidden_truths", "blind_spots"],
        description="Core psychological patterns, personality, defense mechanisms, self-concept",
    ),
    CategoryDef(
        id="emotional",
        name="Emotional Profile",
        filename="02-emotional-profile",
        sources=["emotional", "temporal_patterns"],
        description="Emotional landscape, triggers, regulation patterns, mood tendencies",
    ),
    CategoryDef(
        id="cognitive",
        name="Cognitive & Intellectual Profile",
        filename="03-cognitive-intellectual",
        sources=["intellectual", "recurring_themes"],
        description="Thinking patterns, intellectual interests, learning style, creativity",
    ),
    CategoryDef(
        id="values",
        name="Values, Ethics & Meaning",
        filename="04-values-ethics-meaning",
        sources=["ethical", "spiritual", "philosophical"],
        description="Value system, moral reasoning, meaning-making, existential orientation",
    ),
    CategoryDef(
        id="relational",
        name="Relational & Social Patterns",
        filename="05-relational-social",
        sources=["relationship_dynamics", "communication_patterns", "social_presentation", "external_perception"],
        description="Relationship patterns, communication style, social presentation, how others perceive",
    ),
    CategoryDef(
        id="challenges",
        name="Challenges & Growth Areas",
        filename="06-challenges-growth",
        sources=["growth_opportunities", "shadow_work", "warning_signs", "actionable_practices"],
        description="Current struggles, development opportunities, patterns to monitor, recommendations",
    ),
    CategoryDef(
        id="themes",
        name="Key Themes & Tensions",
        filename="07-key-themes-tensions",
        sources=["unified_portrait", "core_tensions", "essence_distillation", "contradiction_map", "obsessions_avoidances"],
        description="Central life themes, fundamental tensions, contradictions, essence distillation",
    ),
]


@dataclass
class PersonalBackground:
    """Personal background information for a person profile."""

    # Each section is a dict of field_key -> value
    basic_identity: Dict[str, Any] = field(default_factory=dict)
    physical: Dict[str, Any] = field(default_factory=dict)
    location: Dict[str, Any] = field(default_factory=dict)
    education: Dict[str, Any] = field(default_factory=dict)
    employment: Dict[str, Any] = field(default_factory=dict)
    family: Dict[str, Any] = field(default_factory=dict)
    health_physical: Dict[str, Any] = field(default_factory=dict)
    health_mental: Dict[str, Any] = field(default_factory=dict)
    interests: Dict[str, Any] = field(default_factory=dict)
    goals: Dict[str, Any] = field(default_factory=dict)
    life_events: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_verified: Optional[datetime] = None
    verification_status: str = "unverified"  # "verified", "partial", "unverified"
    source_analysis: Optional[Path] = None

    # Tracking what was extracted vs provided
    extracted_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)

    def get_section(self, section_key: str) -> Dict[str, Any]:
        """Get a section by key."""
        return getattr(self, section_key, {})

    def set_section(self, section_key: str, values: Dict[str, Any]) -> None:
        """Set a section by key."""
        setattr(self, section_key, values)

    def count_filled_fields(self) -> tuple[int, int]:
        """Return (filled, total) field counts."""
        filled = 0
        total = 0
        for section_key, (_, fields) in ALL_FIELD_SECTIONS.items():
            section_data = self.get_section(section_key)
            for f in fields:
                if not f.derived:
                    total += 1
                    value = section_data.get(f.key)
                    if value and value != "Not provided":
                        filled += 1
        return filled, total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "basic_identity": self.basic_identity,
            "physical": self.physical,
            "location": self.location,
            "education": self.education,
            "employment": self.employment,
            "family": self.family,
            "health_physical": self.health_physical,
            "health_mental": self.health_mental,
            "interests": self.interests,
            "goals": self.goals,
            "life_events": self.life_events,
            "metadata": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "last_verified": self.last_verified.isoformat() if self.last_verified else None,
                "verification_status": self.verification_status,
                "source_analysis": str(self.source_analysis) if self.source_analysis else None,
            }
        }


@dataclass
class CategorySummary:
    """Condensed summary for a single category."""

    category_id: str
    category_name: str
    filename: str
    content: str  # The generated markdown content

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    source_documents: List[str] = field(default_factory=list)
    source_analysis: Optional[Path] = None
    confidence: str = "medium"  # Aggregated from sources
    word_count: int = 0

    # Hub links found/added
    hub_links: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate derived fields."""
        if self.content:
            self.word_count = len(self.content.split())


@dataclass
class CondensationResult:
    """Result from a complete condensation run."""

    output_folder: Path
    background: PersonalBackground
    summaries: List[CategorySummary]

    # Metadata
    run_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    source_analysis: Optional[Path] = None

    # Statistics
    total_word_count: int = 0
    total_files: int = 0

    def __post_init__(self):
        """Calculate statistics."""
        self.total_files = 1 + len(self.summaries)  # background + summaries
        self.total_word_count = sum(s.word_count for s in self.summaries)
