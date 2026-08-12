import sqlite3
from typing import Optional
from src.domain.state_models import QuestionState

class QuestionRepository:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    q_id TEXT PRIMARY KEY,
                    job_id TEXT,
                    page_num INTEGER,
                    question_no TEXT,
                    question_text TEXT,
                    options TEXT,
                    answer_text TEXT,
                    explanation_text TEXT,
                    image_path TEXT,
                    status TEXT,
                    confirmed INTEGER,
                    manual_edited INTEGER,
                    is_crashed INTEGER
                )
            """)

    def get_by_id(self, q_id: str) -> Optional[QuestionState]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE q_id = ?", (q_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return QuestionState(
            q_id=row["q_id"],
            question_text=row["question_text"],
            options=row["options"].split("||") if row["options"] else [],
            answer_text=row["answer_text"],
            explanation_text=row["explanation_text"],
            image_path=row["image_path"],
            status=row["status"],
            confirmed=bool(row["confirmed"]),
            manual_edited=bool(row["manual_edited"]),
            is_crashed=bool(row["is_crashed"])
        )

    def upsert(self, state: QuestionState, job_id: str, page_num: int, question_no: str):
        existing = self.get_by_id(state.q_id)
        if existing and existing.manual_edited:
            return

        options_str = "||".join(state.options) if state.options else ""
        with self.conn:
            self.conn.execute("""
                INSERT INTO questions (
                    q_id, job_id, page_num, question_no, question_text, 
                    options, answer_text, explanation_text, image_path, 
                    status, confirmed, manual_edited, is_crashed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(q_id) DO UPDATE SET
                    question_text=excluded.question_text,
                    options=excluded.options,
                    answer_text=excluded.answer_text,
                    explanation_text=excluded.explanation_text,
                    image_path=excluded.image_path,
                    status=excluded.status,
                    confirmed=excluded.confirmed,
                    manual_edited=excluded.manual_edited,
                    is_crashed=excluded.is_crashed
            """, (
                state.q_id, job_id, page_num, question_no, state.question_text,
                options_str, state.answer_text, state.explanation_text, state.image_path,
                state.status.value, int(state.confirmed), int(state.manual_edited), int(state.is_crashed)
            ))
