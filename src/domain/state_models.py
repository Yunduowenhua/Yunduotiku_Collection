from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class QuestionStatus(str, Enum):
    CORRECT = "correct"
    UNCERTAIN = "uncertain"
    FAILED = "failed"

class JobState(str, Enum):
    CREATED = "created"
    PARSING = "parsing"
    COMPLETED = "completed"
    PAUSED = "paused"

class QuestionState(BaseModel):
    q_id: str
    question_text: str = ""
    options: List[str] = Field(default_factory=list)
    answer_text: str = ""
    explanation_text: str = ""
    image_path: str = ""
    status: QuestionStatus = QuestionStatus.UNCERTAIN
    confirmed: bool = False
    manual_edited: bool = False
    is_crashed: bool = False
