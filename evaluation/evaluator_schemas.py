from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BinaryJudgeResult(BaseModel):
    score: Literal[0, 1] = Field(..., description="Binary score only.")
    label: Literal["PASS", "FAIL"]
    explanation: str
    judge_name: str | None = None
    criterion_name: str | None = None

    @field_validator("label")
    @classmethod
    def label_matches_score(cls, value: str, info):
        score = info.data.get("score")
        if score == 1 and value != "PASS":
            return "PASS"
        if score == 0 and value != "FAIL":
            return "FAIL"
        return value


def fail_result(
    criterion_name: str,
    explanation: str,
    judge_name: str = "EvaluationJudge",
) -> dict:
    return BinaryJudgeResult(
        score=0,
        label="FAIL",
        explanation=explanation,
        judge_name=judge_name,
        criterion_name=criterion_name,
    ).model_dump()

