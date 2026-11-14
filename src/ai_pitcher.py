import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class PitchGenerator:
    def __init__(self, profile_data, use_ai: bool = True):
        self.profile = profile_data.candidate
        self.pitch_config = profile_data.pitch
        self.use_ai = use_ai and self.pitch_config.use_ai
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None

        if self.use_ai and self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize Gemini client: {e}. Falling back to template.")

    def generate(self, company_name: str, role_title: str, job_description: str = "") -> str:
        """Generates a tailored pitch note (Wellfound recommends < 1000 characters)."""
        if self.client:
            try:
                prompt = f"""
You are an expert career advisor writing a concise, authentic job application pitch note on Wellfound (AngelList).
Candidate Details:
- Name: {self.profile.full_name}
- Years of Experience: {self.profile.years_of_experience}
- Core Skills: {self.profile.primary_skills}
- Background: {self.profile.summary}
- GitHub / Portfolio: {self.profile.github} | {self.profile.portfolio}

Target Position:
- Company: {company_name}
- Role: {role_title}
- Job Snippet / Description: {job_description[:800]}

Guidelines:
1. Write a direct, engaging pitch directly from the candidate to the founder/recruiter.
2. Max length: 700 characters (under 130 words).
3. Do not use generic filler words like 'I am writing to express my eager interest'.
4. Mention 1-2 relevant technical skills and why the candidate is a strong match.
5. End with a polite call to action and the candidate's name.
6. Return ONLY the note text, without any markdown quotes or meta commentary.
"""
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                pitch = response.text.strip()
                if pitch:
                    return pitch[:950]
            except Exception as e:
                print(f"[Info] AI generation fallback triggered: {e}")

        # Fallback to template interpolation
        template = self.pitch_config.template or (
            "Hi {company_name} team,\n\n"
            "I'm {candidate_name}, a {role_title} specializing in {skills}.\n\n"
            "{summary}\n\n"
            "I thrive in high-ownership teams where I can build reliable, low-latency systems and deliver impact from day one.\n\n"
            "- Portfolio: {portfolio}\n"
            "- GitHub: {github}\n"
            "- LinkedIn: {linkedin}\n\n"
            "Best,\n{candidate_name}"
        )

        replacements = {
            "company_name": company_name or "there",
            "role_title": role_title or "Backend Engineer",
            "candidate_name": self.profile.full_name or "Candidate",
            "years_of_experience": self.profile.years_of_experience or 2,
            "skills": self.profile.primary_skills or "Go, Python, Microservices, gRPC, Kafka, Kubernetes",
            "summary": self.profile.summary or "Experienced in designing and deploying scalable backend services and high-throughput microservices.",
            "github": self.profile.github or "https://github.com",
            "portfolio": self.profile.portfolio or "https://example.com",
            "linkedin": self.profile.linkedin or "https://linkedin.com",
            "leetcode": self.profile.leetcode or "https://leetcode.com",
        }

        # Safe replacement without throwing KeyError on missing placeholders
        result = template
        for k, v in replacements.items():
            result = result.replace(f"{{{k}}}", str(v))

        return result.strip()[:980]
