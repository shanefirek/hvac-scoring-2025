from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import os

app = FastAPI(title="Appletree HVAC Lead Scoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRANCHISES = [
    "ARS",
    "Rescue Rooter",
    "One Hour",
    "Benjamin Franklin",
    "Roto-Rooter",
    "Mr. Rooter",
    "Aire Serv",
    "Goettl"
]

SERVICE_SOFTWARE = ["ServiceTitan", "Jobber", "Housecall Pro"]

class LeadInput(BaseModel):
    company: str
    reviews_count: Optional[int] = 0
    service_software: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    domain: Optional[str] = ""

class ScoreBreakdown(BaseModel):
    service_software: int
    franchise_or_reviews: int
    linkedin: int
    domain: int

class LeadScore(BaseModel):
    is_franchise: str
    score: int
    tier: str
    messaging_strategy: str
    breakdown: ScoreBreakdown

def detect_franchise(company_name: str) -> bool:
    company_upper = company_name.upper()
    return any(franchise.upper() in company_upper for franchise in FRANCHISES)

def calculate_review_score(review_count: int) -> int:
    if review_count >= 500:
        return 10
    elif review_count >= 100:
        return 7
    elif review_count >= 25:
        return 4
    elif review_count >= 10:
        return 2
    return 0

def has_service_software(software: str) -> bool:
    if not software:
        return False
    return any(sw.lower() in software.lower() for sw in SERVICE_SOFTWARE)

def determine_messaging_strategy(tier: str, has_software: bool, is_franchise: bool) -> str:
    if tier == "A":
        if is_franchise:
            return "Franchise: Multi-unit operations + franchise fee complexity"
        elif has_software:
            return "Software + Scale: Tech-forward operator with systems"
        else:
            return "Scale: High-volume operation with complex tax needs"
    elif tier == "B":
        if has_software:
            return "Tech Signal: Has systems, needs better accounting integration"
        else:
            return "Growth Signal: Established business, room for tax optimization"
    else:
        return "Pain Focus: Direct CPA pain points and tax surprises"

@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "Appletree HVAC Lead Scoring API",
        "version": "1.0.0"
    }

@app.post("/score-lead", response_model=LeadScore)
def score_lead(lead: LeadInput):
    try:
        score = 0
        breakdown = {
            "service_software": 0,
            "franchise_or_reviews": 0,
            "linkedin": 0,
            "domain": 0
        }

        has_software = has_service_software(lead.service_software)
        if has_software:
            score += 15
            breakdown["service_software"] = 15

        is_franchise = detect_franchise(lead.company)
        if is_franchise:
            score += 10
            breakdown["franchise_or_reviews"] = 10
        else:
            review_score = calculate_review_score(lead.reviews_count)
            score += review_score
            breakdown["franchise_or_reviews"] = review_score

        if lead.linkedin_url and len(lead.linkedin_url) > 0:
            score += 3
            breakdown["linkedin"] = 3

        if lead.domain and len(lead.domain) > 0:
            score += 2
            breakdown["domain"] = 2

        if score >= 20:
            tier = "A"
        elif score >= 10:
            tier = "B"
        else:
            tier = "C"

        messaging = determine_messaging_strategy(tier, has_software, is_franchise)

        return LeadScore(
            is_franchise="YES" if is_franchise else "NO",
            score=score,
            tier=tier,
            messaging_strategy=messaging,
            breakdown=ScoreBreakdown(**breakdown)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring lead: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
