from __future__ import annotations

from typing import Any, Iterable

import requests

from .models import TrialRecord
from .normalization import parse_age_years


API_URL = "https://clinicaltrials.gov/api/v2/studies"
OPEN_STATUS_FILTER = (
    "RECRUITING|NOT_YET_RECRUITING|ENROLLING_BY_INVITATION|ACTIVE_NOT_RECRUITING"
)


class ClinicalTrialsClient:
    """Small client for the public ClinicalTrials.gov API v2."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def search(
        self, condition: str, page_size: int = 1000, open_only: bool = True
    ) -> list[TrialRecord]:
        params = {
            "query.cond": condition,
            "pageSize": min(page_size, 1000),
            "format": "json",
            "countTotal": "true",
        }
        if open_only:
            params["filter.overallStatus"] = OPEN_STATUS_FILTER
        studies: list[dict[str, Any]] = []
        while True:
            response = requests.get(API_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            studies.extend(payload.get("studies", []))
            next_page = payload.get("nextPageToken")
            if not next_page:
                break
            params["pageToken"] = next_page
        return [trial_from_study(study) for study in studies]

    def search_many(
        self, conditions: Iterable[str], page_size: int = 1000, open_only: bool = True
    ) -> list[TrialRecord]:
        by_id: dict[str, TrialRecord] = {}
        for condition in conditions:
            for trial in self.search(condition, page_size=page_size, open_only=open_only):
                by_id[trial.nct_id] = trial
        return sorted(by_id.values(), key=lambda trial: trial.nct_id)


def _module(study: dict[str, Any], name: str) -> dict[str, Any]:
    return study.get("protocolSection", {}).get(name, {}) or {}


def trial_from_study(study: dict[str, Any]) -> TrialRecord:
    identification = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    conditions = _module(study, "conditionsModule")
    design = _module(study, "designModule")
    eligibility = _module(study, "eligibilityModule")
    contacts = _module(study, "contactsLocationsModule")
    arms = _module(study, "armsInterventionsModule")
    description = _module(study, "descriptionModule")

    countries = sorted({
        location.get("country", "").strip()
        for location in contacts.get("locations", [])
        if location.get("country", "").strip()
    })
    intervention_names = sorted({
        intervention.get("name", "").strip()
        for intervention in arms.get("interventions", [])
        if intervention.get("name", "").strip()
    })
    nct_id = identification.get("nctId", "")
    return TrialRecord(
        nct_id=nct_id,
        title=identification.get("briefTitle", ""),
        overall_status=status.get("overallStatus", "UNKNOWN"),
        conditions=tuple(conditions.get("conditions", []) or []),
        sex=eligibility.get("sex", "ALL"),
        minimum_age_years=parse_age_years(eligibility.get("minimumAge")),
        maximum_age_years=parse_age_years(eligibility.get("maximumAge")),
        countries=tuple(countries),
        phases=tuple(design.get("phases", []) or []),
        interventions=tuple(intervention_names),
        eligibility_text=eligibility.get("eligibilityCriteria", "") or "",
        brief_summary=description.get("briefSummary", "") or "",
        last_update=(status.get("lastUpdatePostDateStruct", {}) or {}).get("date", ""),
        source_url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    )
