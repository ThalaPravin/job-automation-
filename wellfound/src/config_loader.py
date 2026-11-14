from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class SearchConfig(BaseModel):
    custom_search_url: str = "https://wellfound.com/jobs"
    roles: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    min_salary_usd: int = 0

class SafetyConfig(BaseModel):
    dry_run: bool = True
    max_applications_per_run: int = 10
    min_delay_seconds: int = 15
    max_delay_seconds: int = 35
    headless: bool = False

class BrowserConfig(BaseModel):
    user_data_dir: str = "browser_profile"
    use_cdp: bool = False
    cdp_url: str = "http://localhost:9222"

class BlacklistConfig(BaseModel):
    companies: List[str] = Field(default_factory=list)
    title_keywords_exclude: List[str] = Field(default_factory=list)

class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    blacklist: BlacklistConfig = Field(default_factory=BlacklistConfig)

class CandidateProfile(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    leetcode: str = ""
    current_company: str = ""
    education: str = ""
    years_of_experience: int = 1
    primary_skills: str = ""
    summary: str = ""

class PitchConfig(BaseModel):
    use_ai: bool = True
    template: str = ""

class UserProfile(BaseModel):
    candidate: CandidateProfile = Field(default_factory=CandidateProfile)
    pitch: PitchConfig = Field(default_factory=PitchConfig)
    screening_answers: Dict[str, Any] = Field(default_factory=dict)

def load_yaml(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_config() -> AppConfig:
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    if not config_path.exists():
        config_path = PROJECT_ROOT / "config" / "config.example.yaml"
    data = load_yaml(config_path)
    return AppConfig(**data)

def get_profile() -> UserProfile:
    profile_path = PROJECT_ROOT / "config" / "profile.yaml"
    if not profile_path.exists():
        profile_path = PROJECT_ROOT / "config" / "profile.example.yaml"
    data = load_yaml(profile_path)
    return UserProfile(**data)
