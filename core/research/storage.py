from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime,timezone
from pathlib import Path
from typing import Any, Optional

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)

from core.research.memory_object import MemoryCandidate
from core.orchestrator.task_state import Goal, Task


class ResearchStorage:
    """
    Persistent SQLite storage for the SAHIBEX research system.

    Stores:
    - Research sources
    - Research documents
    - Research findings
    - Evidence
    - Knowledge candidates
    - Memory candidates

    Datetime/date values are serialized with explicit type markers
    so objects can be reconstructed without losing their original types.
    """

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        # Multiple SAHIBEX entry points can start close together on Android.
        # Wait for a concurrent SQLite writer instead of failing immediately
        # during schema/FTS initialization; SQLite still serializes writes.
        self._connection = sqlite3.connect(
            str(self.database_path),
            timeout=30.0,
        )

        self._connection.row_factory = sqlite3.Row

        try:
            self._initialize_schema()
        except BaseException:
            # Never leave a half-initialized connection alive after corrupt or
            # incompatible database state. Propagate the original failure so
            # callers fail closed instead of silently opening an empty store.
            self._connection.close()
            raise

    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_sources (
                source_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS research_documents (
                document_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_documents_source
            ON research_documents(source_id);

            CREATE INDEX IF NOT EXISTS idx_documents_hash
            ON research_documents(content_hash);

            CREATE TABLE IF NOT EXISTS research_findings (
                finding_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_findings_document
            ON research_findings(document_id);

            CREATE TABLE IF NOT EXISTS research_evidence (
                evidence_id TEXT PRIMARY KEY,
                finding_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_finding
            ON research_evidence(finding_id);

            CREATE INDEX IF NOT EXISTS idx_evidence_source
            ON research_evidence(source_id);

            CREATE TABLE IF NOT EXISTS knowledge_candidates (
                knowledge_id TEXT PRIMARY KEY,
                verified INTEGER NOT NULL,
                confidence REAL NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_knowledge_verified
            ON knowledge_candidates(verified);

            CREATE TABLE IF NOT EXISTS knowledge_merge_records (
                merge_id TEXT PRIMARY KEY,
                primary_knowledge_id TEXT NOT NULL,
                duplicate_knowledge_id TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                status TEXT NOT NULL,
                merged_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_merge_primary
            ON knowledge_merge_records(primary_knowledge_id);

            CREATE INDEX IF NOT EXISTS idx_merge_duplicate
            ON knowledge_merge_records(duplicate_knowledge_id);

            CREATE INDEX IF NOT EXISTS idx_merge_status
            ON knowledge_merge_records(status);

            CREATE TABLE IF NOT EXISTS knowledge_conflict_records (
                conflict_id TEXT PRIMARY KEY,
                first_knowledge_id TEXT NOT NULL,
                second_knowledge_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                resolution_status TEXT NOT NULL,
                selected_knowledge_id TEXT,
                created_at TEXT,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conflict_first
            ON knowledge_conflict_records(first_knowledge_id);

            CREATE INDEX IF NOT EXISTS idx_conflict_second
            ON knowledge_conflict_records(second_knowledge_id);

            CREATE INDEX IF NOT EXISTS idx_conflict_status
            ON knowledge_conflict_records(resolution_status);

            CREATE TABLE IF NOT EXISTS knowledge_verification_records (
                event_id TEXT PRIMARY KEY,
                knowledge_id TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_verification_knowledge
            ON knowledge_verification_records(knowledge_id);

            CREATE INDEX IF NOT EXISTS idx_verification_status
            ON knowledge_verification_records(status);

            CREATE INDEX IF NOT EXISTS idx_verification_time
            ON knowledge_verification_records(verified_at);

            CREATE TABLE IF NOT EXISTS learning_history_records (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                topic TEXT NOT NULL,
                success INTEGER NOT NULL,
                status TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                research_job_id TEXT NOT NULL,
                research_execution_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_learning_history_created
            ON learning_history_records(created_at);

            CREATE INDEX IF NOT EXISTS idx_learning_history_topic
            ON learning_history_records(topic);

            CREATE TABLE IF NOT EXISTS memory_verification_records (
                memory_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                verified_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_memory_verification_status
            ON memory_verification_records(status);

            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                source TEXT NOT NULL,
                importance REAL NOT NULL,
                confidence REAL NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_memories_type
            ON memories(memory_type);

            CREATE INDEX IF NOT EXISTS idx_memories_source
            ON memories(source);

            CREATE INDEX IF NOT EXISTS idx_memories_importance
            ON memories(importance);

            CREATE INDEX IF NOT EXISTS idx_memories_confidence
            ON memories(confidence);

                       CREATE TABLE IF NOT EXISTS planning_goals (
                goal_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS planning_tasks (
                task_id TEXT PRIMARY KEY,
                goal_id TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                parent_task_id TEXT,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_planning_tasks_goal
            ON planning_tasks(goal_id);

            CREATE INDEX IF NOT EXISTS idx_planning_tasks_status
            ON planning_tasks(status);

            CREATE INDEX IF NOT EXISTS idx_planning_tasks_priority
            ON planning_tasks(priority);

            CREATE INDEX IF NOT EXISTS idx_planning_tasks_parent
            ON planning_tasks(parent_task_id);
            """
        )

        self._connection.commit()
        self._initialize_search_indexes()

    def _initialize_search_indexes(self) -> None:
        """Create and synchronize FTS5 indexes for persistent retrieval."""
        self._connection.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_search
            USING fts5(memory_id UNINDEXED, searchable_text);

            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search
            USING fts5(knowledge_id UNINDEXED, searchable_text);

            CREATE TABLE IF NOT EXISTS fts_index_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                dirty INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO fts_index_state(id, dirty) VALUES (1, 1);

            CREATE TRIGGER IF NOT EXISTS memories_fts_dirty_insert
            AFTER INSERT ON memories BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;
            CREATE TRIGGER IF NOT EXISTS memories_fts_dirty_update
            AFTER UPDATE ON memories BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;
            CREATE TRIGGER IF NOT EXISTS memories_fts_dirty_delete
            AFTER DELETE ON memories BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;

            CREATE TRIGGER IF NOT EXISTS knowledge_fts_dirty_insert
            AFTER INSERT ON knowledge_candidates BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;
            CREATE TRIGGER IF NOT EXISTS knowledge_fts_dirty_update
            AFTER UPDATE ON knowledge_candidates BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;
            CREATE TRIGGER IF NOT EXISTS knowledge_fts_dirty_delete
            AFTER DELETE ON knowledge_candidates BEGIN
                UPDATE fts_index_state SET dirty = 1 WHERE id = 1;
            END;

            """
        )

        # Canonical-table triggers and transactional save methods maintain this
        # marker. Clean databases avoid a full scan on every startup; legacy or
        # interrupted canonical/FTS states are rebuilt before exposure.
        state = self._connection.execute(
            "SELECT dirty FROM fts_index_state WHERE id = 1"
        ).fetchone()
        if state is None or state["dirty"]:
            expected_memories = {}
            for row in self._connection.execute(
                "SELECT memory_id, data FROM memories"
            ).fetchall():
                payload = self._deserialize(row["data"])
                expected_memories[row["memory_id"]] = " ".join(
                    [
                        str(payload.get("content", "")),
                        str(payload.get("memory_type", "")),
                        str(payload.get("source", "")),
                        " ".join(str(tag) for tag in payload.get("tags", [])),
                        self._serialize(payload.get("metadata", {})),
                    ]
                )
            expected_knowledge = {}
            for row in self._connection.execute(
                "SELECT knowledge_id, data FROM knowledge_candidates"
            ).fetchall():
                payload = self._deserialize(row["data"])
                expected_knowledge[row["knowledge_id"]] = str(
                    payload.get("statement", "")
                )

            self._connection.execute("DELETE FROM memory_search")
            self._connection.executemany(
                "INSERT INTO memory_search(memory_id, searchable_text) VALUES (?, ?)",
                list(expected_memories.items()),
            )
            self._connection.execute("DELETE FROM knowledge_search")
            self._connection.executemany(
                "INSERT INTO knowledge_search(knowledge_id, searchable_text) VALUES (?, ?)",
                list(expected_knowledge.items()),
            )
            self._connection.execute(
                "UPDATE fts_index_state SET dirty = 0 WHERE id = 1"
            )

        self._connection.commit()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    @staticmethod
    def _encode(value: Any) -> Any:
        if isinstance(value, datetime):
            return {
                "__sahibex_type__": "datetime",
                "value": value.isoformat(),
            }

        if isinstance(value, date):
            return {
                "__sahibex_type__": "date",
                "value": value.isoformat(),
            }

        if is_dataclass(value):
            return ResearchStorage._encode(asdict(value))

        if isinstance(value, dict):
            return {
                str(key): ResearchStorage._encode(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                ResearchStorage._encode(item)
                for item in value
            ]

        return value

    @staticmethod
    def _decode(value: Any) -> Any:
        if isinstance(value, dict):
            marker = value.get("__sahibex_type__")

            if marker == "datetime":
                return datetime.fromisoformat(value["value"])

            if marker == "date":
                return date.fromisoformat(value["value"])

            return {
                key: ResearchStorage._decode(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                ResearchStorage._decode(item)
                for item in value
            ]

        return value

    @classmethod
    def _serialize(cls, value: Any) -> str:
        encoded = cls._encode(value)

        return json.dumps(
            encoded,
            ensure_ascii=False,
            sort_keys=True,
        )

    @classmethod
    def _deserialize(cls, data: str) -> dict:
        value = json.loads(data)

        if not isinstance(value, dict):
            raise ValueError(
                "Stored research object must be a JSON object"
            )

        return cls._decode(value)

    # ---------------------------------------------------------
    # Sources
    # ---------------------------------------------------------

    def save_source(self, source: ResearchSource) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO research_sources
            (source_id, data)
            VALUES (?, ?)
            """,
            (
                source.source_id,
                self._serialize(source),
            ),
        )

        self._connection.commit()

    def get_source(
        self,
        source_id: str,
    ) -> Optional[ResearchSource]:
        row = self._connection.execute(
            """
            SELECT data
            FROM research_sources
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchone()

        if row is None:
            return None

        return ResearchSource(
            **self._deserialize(row["data"])
        )

    def source_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_sources
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Documents
    # ---------------------------------------------------------

    def save_document(
        self,
        document: ResearchDocument,
    ) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO research_documents
            (document_id, source_id, content_hash, data)
            VALUES (?, ?, ?, ?)
            """,
            (
                document.document_id,
                document.source_id,
                document.content_hash,
                self._serialize(document),
            ),
        )

        self._connection.commit()

    def get_document(
        self,
        document_id: str,
    ) -> Optional[ResearchDocument]:
        row = self._connection.execute(
            """
            SELECT data
            FROM research_documents
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return ResearchDocument(
            **self._deserialize(row["data"])
        )

    def find_document_by_hash(
        self,
        content_hash: str,
    ) -> Optional[ResearchDocument]:
        row = self._connection.execute(
            """
            SELECT data
            FROM research_documents
            WHERE content_hash = ?
            LIMIT 1
            """,
            (content_hash,),
        ).fetchone()

        if row is None:
            return None

        return ResearchDocument(
            **self._deserialize(row["data"])
        )

    def document_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_documents
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Findings
    # ---------------------------------------------------------

    def save_finding(
        self,
        finding: ResearchFinding,
    ) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO research_findings
            (finding_id, document_id, data)
            VALUES (?, ?, ?)
            """,
            (
                finding.finding_id,
                finding.document_id,
                self._serialize(finding),
            ),
        )

        self._connection.commit()

    def get_finding(
        self,
        finding_id: str,
    ) -> Optional[ResearchFinding]:
        row = self._connection.execute(
            """
            SELECT data
            FROM research_findings
            WHERE finding_id = ?
            """,
            (finding_id,),
        ).fetchone()

        if row is None:
            return None

        return ResearchFinding(
            **self._deserialize(row["data"])
        )

    def finding_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_findings
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    def save_evidence(
        self,
        evidence: Evidence,
    ) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO research_evidence
            (evidence_id, finding_id, source_id, data)
            VALUES (?, ?, ?, ?)
            """,
            (
                evidence.evidence_id,
                evidence.finding_id,
                evidence.source_id,
                self._serialize(evidence),
            ),
        )

        self._connection.commit()

    def get_evidence(
        self,
        evidence_id: str,
    ) -> Optional[Evidence]:
        row = self._connection.execute(
            """
            SELECT data
            FROM research_evidence
            WHERE evidence_id = ?
            """,
            (evidence_id,),
        ).fetchone()

        if row is None:
            return None

        return Evidence(
            **self._deserialize(row["data"])
        )

    def evidence_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM research_evidence
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Knowledge
    # ---------------------------------------------------------

    def _save_search_indexed_record(
        self,
        *,
        canonical_sql: str,
        canonical_parameters: tuple,
        index_table: str,
        index_id_column: str,
        record_id: str,
        searchable_text: str,
    ) -> None:
        """Atomically persist a canonical row and its derived search row.

        The connection context manager commits only on success and rolls back
        the entire write transaction on any SQL error. Without this boundary,
        a canonical row could remain pending after an FTS failure and be
        committed accidentally by a later unrelated write.
        """
        allowed_indexes = {
            ("memory_search", "memory_id"),
            ("knowledge_search", "knowledge_id"),
        }
        if (index_table, index_id_column) not in allowed_indexes:
            raise ValueError("Unsupported search index table.")

        with self._connection:
            self._connection.execute(
                canonical_sql,
                canonical_parameters,
            )
            self._connection.execute(
                f"DELETE FROM {index_table} WHERE {index_id_column} = ?",
                (record_id,),
            )
            self._connection.execute(
                f"INSERT INTO {index_table}({index_id_column}, searchable_text) VALUES (?, ?)",
                (record_id, searchable_text),
            )
            self._connection.execute(
                "UPDATE fts_index_state SET dirty = 0 WHERE id = 1"
            )

    def save_knowledge(
        self,
        knowledge: KnowledgeCandidate,
    ) -> None:
        self._save_search_indexed_record(
            canonical_sql=(
                "INSERT OR REPLACE INTO knowledge_candidates "
                "(knowledge_id, verified, confidence, data) VALUES (?, ?, ?, ?)"
            ),
            canonical_parameters=(
                knowledge.knowledge_id,
                int(knowledge.verified),
                knowledge.confidence,
                self._serialize(knowledge),
            ),
            index_table="knowledge_search",
            index_id_column="knowledge_id",
            record_id=knowledge.knowledge_id,
            searchable_text=knowledge.statement,
        )

    def get_knowledge(
        self,
        knowledge_id: str,
    ) -> Optional[KnowledgeCandidate]:
        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_candidates
            WHERE knowledge_id = ?
            """,
            (knowledge_id,),
        ).fetchone()

        if row is None:
            return None

        return KnowledgeCandidate(
            **self._deserialize(row["data"])
        )

    def list_knowledge(
        self,
        *,
        verified_only: bool = False,
    ) -> list[KnowledgeCandidate]:
        """
        Return persisted knowledge candidates.

        When verified_only is True, only verified knowledge is returned.
        Results are ordered by confidence, highest first.
        """
        if verified_only:
            rows = self._connection.execute(
                """
                SELECT data
                FROM knowledge_candidates
                WHERE verified = 1
                ORDER BY confidence DESC
                """
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT data
                FROM knowledge_candidates
                ORDER BY confidence DESC
                """
            ).fetchall()

        return [
            KnowledgeCandidate(
                **self._deserialize(row["data"])
            )
            for row in rows
        ]

    def retrieve_knowledge(
        self,
        query: str,
        *,
        verified_only: bool = False,
        min_confidence: float = 0.0,
        limit: Optional[int] = None,
    ) -> list[KnowledgeCandidate]:
        """
        Retrieve persisted knowledge whose statements contain
        the requested query text.

        Retrieval is:
        - case-insensitive
        - whitespace-normalized
        - deterministic
        - optionally restricted to verified knowledge
        - optionally restricted by minimum confidence
        """
        if not isinstance(query, str):
            raise ValueError("query must be a string")

        normalized_query = " ".join(
            query.lower().strip().split()
        )

        if not normalized_query:
            raise ValueError("query cannot be empty")

        if not isinstance(verified_only, bool):
            raise ValueError(
                "verified_only must be a boolean"
            )

        if not isinstance(min_confidence, (int, float)):
            raise ValueError(
                "min_confidence must be numeric"
            )

        if not 0 <= min_confidence <= 1:
            raise ValueError(
                "min_confidence must be between 0 and 1"
            )

        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer")
            if limit <= 0:
                raise ValueError("limit must be positive")

        # Use the dedicated FTS5 index so retrieval does not scan or
        # deserialize the full persistent knowledge database.
        fts_terms = [
            token.replace('"', '""')
            for token in normalized_query.split()
            if token.strip()
        ]
        fts_query = " OR ".join(
            f'"{token}"'
            for token in fts_terms
        ) or f'"{normalized_query.replace(chr(34), chr(34) * 2)}"'

        # Apply the result limit after relevance filtering. Limiting the FTS
        # prefilter first can let high-confidence but irrelevant candidates
        # crowd out the actually relevant claim.
        limit_sql = ""
        limit_params: tuple[object, ...] = ()

        if verified_only:
            rows = self._connection.execute(
                f"""
                SELECT knowledge_candidates.data
                FROM knowledge_candidates
                JOIN knowledge_search
                  ON knowledge_search.knowledge_id =
                     knowledge_candidates.knowledge_id
                WHERE knowledge_candidates.verified = 1
                  AND knowledge_search MATCH ?
                ORDER BY knowledge_candidates.confidence DESC
                {limit_sql}
                """,
                (fts_query, *limit_params),
            ).fetchall()
        else:
            rows = self._connection.execute(
                f"""
                SELECT knowledge_candidates.data
                FROM knowledge_candidates
                JOIN knowledge_search
                  ON knowledge_search.knowledge_id =
                     knowledge_candidates.knowledge_id
                WHERE knowledge_search MATCH ?
                ORDER BY knowledge_candidates.confidence DESC
                {limit_sql}
                """,
                (fts_query, *limit_params),
            ).fetchall()

        # SQLite's FTS unicode tokenizer can fail to index/search some
        # Indic-script tokens consistently on device builds. For non-ASCII
        # queries, scan persisted candidates and apply the same strict
        # token-overlap relevance gate below rather than trusting FTS hits.
        if any(ord(character) > 127 for character in normalized_query):
            if verified_only:
                rows = self._connection.execute(
                    """
                    SELECT data FROM knowledge_candidates
                    WHERE verified = 1
                    ORDER BY confidence DESC
                    """
                ).fetchall()
            else:
                rows = self._connection.execute(
                    "SELECT data FROM knowledge_candidates ORDER BY confidence DESC"
                ).fetchall()

        matches: list[KnowledgeCandidate] = []
        punctuation = ".,!?;:()[]{}'\"।॥"
        query_tokens = {
            token.strip(punctuation)
            for token in normalized_query.split()
            if token.strip(punctuation)
        }
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "how", "in", "is", "it", "of", "on", "or", "the",
            "to", "was", "what", "when", "where", "which", "who", "why",
            "hai", "hain", "ka", "ki", "ke", "ko", "kya", "mein", "me",
            "se", "aur", "kaun", "kab", "kahan", "kyon", "hai", "tha",
            "thi", "the", "कौन", "कौनसा", "कौनसी", "क्या", "कहाँ",
            "कब", "क्यों", "कैसे", "बताओ", "बताइए", "कृपया",
        }
        significant_query_tokens = {
            token for token in query_tokens
            if len(token) >= 3 and token not in stop_words
        }

        for row in rows:
            knowledge = KnowledgeCandidate(
                **self._deserialize(row["data"])
            )

            if knowledge.confidence < min_confidence:
                continue

            normalized_statement = " ".join(
                knowledge.statement.casefold().strip().split()
            )
            statement_tokens = {
                token.strip(punctuation)
                for token in normalized_statement.split()
                if token.strip(punctuation)
            }

            # Exact phrase matches remain strongest. Natural-language queries
            # can also retrieve semantically relevant candidates by requiring
            # enough significant token overlap; a single shared generic word
            # cannot pull in unrelated knowledge. The FTS index is only a
            # candidate prefilter, never the final relevance decision.
            if normalized_query not in normalized_statement:
                if not significant_query_tokens:
                    continue
                overlap = significant_query_tokens & statement_tokens
                required_overlap = max(
                    1,
                    (len(significant_query_tokens) * 2 + 2) // 3,
                )
                if len(overlap) < required_overlap:
                    continue

            matches.append(knowledge)

        matches.sort(
            key=lambda knowledge: (
                -knowledge.confidence,
                knowledge.knowledge_id,
            )
        )
        if limit is not None:
            matches = matches[:limit]

        return matches

    def knowledge_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_candidates
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Knowledge Merge
    # ---------------------------------------------------------

    def save_knowledge_merge(
        self,
        *,
        merge_id: str,
        primary_knowledge_id: str,
        duplicate_knowledge_id: str,
        similarity_score: float,
        status: str,
        merged_at: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        if not isinstance(merge_id, str):
            raise TypeError("merge_id must be a string")

        if not merge_id.strip():
            raise ValueError("merge_id cannot be empty")

        if not isinstance(primary_knowledge_id, str):
            raise TypeError(
                "primary_knowledge_id must be a string"
            )

        if not primary_knowledge_id.strip():
            raise ValueError(
                "primary_knowledge_id cannot be empty"
            )

        if not isinstance(duplicate_knowledge_id, str):
            raise TypeError(
                "duplicate_knowledge_id must be a string"
            )

        if not duplicate_knowledge_id.strip():
            raise ValueError(
                "duplicate_knowledge_id cannot be empty"
            )

        if primary_knowledge_id == duplicate_knowledge_id:
            raise ValueError(
                "primary and duplicate knowledge IDs cannot be the same"
            )

        if not 0.0 <= similarity_score <= 1.0:
            raise ValueError(
                "similarity_score must be between 0 and 1"
            )

        if not isinstance(status, str):
            raise TypeError("status must be a string")

        if not status.strip():
            raise ValueError("status cannot be empty")

        if not isinstance(merged_at, datetime):
            raise TypeError("merged_at must be a datetime")

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_merge_records
            (
                merge_id,
                primary_knowledge_id,
                duplicate_knowledge_id,
                similarity_score,
                status,
                merged_at,
                metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                merge_id,
                primary_knowledge_id,
                duplicate_knowledge_id,
                similarity_score,
                status,
                merged_at.isoformat(),
                self._serialize(metadata),
            ),
        )

        self._connection.commit()

    def get_knowledge_merge(
        self,
        merge_id: str,
    ) -> Optional[dict[str, Any]]:
        if not isinstance(merge_id, str):
            raise TypeError("merge_id must be a string")

        if not merge_id.strip():
            raise ValueError("merge_id cannot be empty")

        row = self._connection.execute(
            """
            SELECT
                merge_id,
                primary_knowledge_id,
                duplicate_knowledge_id,
                similarity_score,
                status,
                merged_at,
                metadata
            FROM knowledge_merge_records
            WHERE merge_id = ?
            """,
            (merge_id,),
        ).fetchone()

        if row is None:
            return None

        merged_at = datetime.fromisoformat(
            row["merged_at"]
        )

        return {
            "merge_id": row["merge_id"],
            "primary_knowledge_id": row[
                "primary_knowledge_id"
            ],
            "duplicate_knowledge_id": row[
                "duplicate_knowledge_id"
            ],
            "similarity_score": row["similarity_score"],
            "status": row["status"],
            "merged_at": merged_at,
            "metadata": self._deserialize(
                row["metadata"]
            ),
        }

    def knowledge_merge_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_merge_records
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Knowledge Conflicts
    # ---------------------------------------------------------

    def save_knowledge_conflict(
        self,
        conflict,
    ) -> None:
        from core.research.knowledge_conflict import (
            KnowledgeConflictRecord,
        )

        if not isinstance(
            conflict,
            KnowledgeConflictRecord,
        ):
            raise TypeError(
                "conflict must be a KnowledgeConflictRecord"
            )

        created_at = (
            conflict.created_at.isoformat()
            if conflict.created_at is not None
            else None
        )

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_conflict_records
            (
                conflict_id,
                first_knowledge_id,
                second_knowledge_id,
                conflict_type,
                resolution_status,
                selected_knowledge_id,
                created_at,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict.conflict_id,
                conflict.first_knowledge_id,
                conflict.second_knowledge_id,
                conflict.conflict_type,
                conflict.resolution_status,
                conflict.selected_knowledge_id,
                created_at,
                self._serialize(conflict),
            ),
        )

        self._connection.commit()

    def get_knowledge_conflict(
        self,
        conflict_id: str,
    ):
        from core.research.knowledge_conflict import (
            KnowledgeConflictRecord,
        )

        if not isinstance(conflict_id, str):
            raise TypeError(
                "conflict_id must be a string"
            )

        if not conflict_id.strip():
            raise ValueError(
                "conflict_id cannot be empty"
            )

        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_conflict_records
            WHERE conflict_id = ?
            """,
            (conflict_id,),
        ).fetchone()

        if row is None:
            return None

        return KnowledgeConflictRecord(
            **self._deserialize(row["data"])
        )

    @staticmethod
    def _conflict_pair_id(
        first_knowledge_id: str,
        second_knowledge_id: str,
    ) -> str:
        if not isinstance(first_knowledge_id, str):
            raise TypeError(
                "first_knowledge_id must be a string"
            )

        if not isinstance(second_knowledge_id, str):
            raise TypeError(
                "second_knowledge_id must be a string"
            )

        first = first_knowledge_id.strip()
        second = second_knowledge_id.strip()

        if not first:
            raise ValueError(
                "first_knowledge_id cannot be empty"
            )

        if not second:
            raise ValueError(
                "second_knowledge_id cannot be empty"
            )

        if first == second:
            raise ValueError(
                "knowledge conflict cannot reference the same knowledge"
            )

        ordered = sorted((first, second))

        return (
            f"knowledge-conflict:"
            f"{ordered[0]}:"
            f"{ordered[1]}"
        )

    def save_conflict_assessment(
        self,
        assessment,
    ) -> None:
        """
        Persist a 6G-5 ConflictIntelligenceAssessment as a
        durable 6H-7 KnowledgeConflictRecord.

        The existing conflict storage path remains authoritative.
        """
        from datetime import datetime, timezone

        from core.research.knowledge_conflict import (
            KnowledgeConflictRecord,
        )

        required_fields = (
            "first_knowledge_id",
            "second_knowledge_id",
            "conflict_type",
            "conflict_reason",
            "resolution_status",
            "selected_knowledge_id",
            "evidence_score_delta",
            "source_reliability_delta",
            "knowledge_confidence_delta",
            "resolution_reason",
        )

        for field_name in required_fields:
            if not hasattr(assessment, field_name):
                raise TypeError(
                    "assessment must be a "
                    "ConflictIntelligenceAssessment-compatible object"
                )

        first_id = assessment.first_knowledge_id
        second_id = assessment.second_knowledge_id

        conflict_id = self._conflict_pair_id(
            first_id,
            second_id,
        )

        metadata = {
            "conflict_intelligence_version": getattr(
                assessment,
                "version",
                None,
            ),
        }

        record = KnowledgeConflictRecord(
            conflict_id=conflict_id,
            first_knowledge_id=first_id,
            second_knowledge_id=second_id,
            conflict_type=assessment.conflict_type,
            conflict_reason=assessment.conflict_reason,
            resolution_status=assessment.resolution_status,
            selected_knowledge_id=assessment.selected_knowledge_id,
            evidence_score_delta=assessment.evidence_score_delta,
            source_reliability_delta=assessment.source_reliability_delta,
            knowledge_confidence_delta=assessment.knowledge_confidence_delta,
            resolution_reason=assessment.resolution_reason,
            created_at=datetime.now(timezone.utc),
            metadata=metadata,
        )

        self.save_knowledge_conflict(record)

    def get_conflict_assessment(
        self,
        first_knowledge_id: str,
        second_knowledge_id: str,
    ):
        conflict_id = self._conflict_pair_id(
            first_knowledge_id,
            second_knowledge_id,
        )

        return self.get_knowledge_conflict(
            conflict_id
        )

    def conflict_assessment_count(self) -> int:
        return self.knowledge_conflict_count()

    def conflicts_for_knowledge(
        self,
        knowledge_id: str,
        resolution_status: Optional[str] = None,
    ):
        from core.research.knowledge_conflict import (
            KnowledgeConflictRecord,
            RESOLUTION_RESOLVED,
            RESOLUTION_UNRESOLVED,
        )

        if not isinstance(knowledge_id, str):
            raise TypeError(
                "knowledge_id must be a string"
            )

        knowledge_id = knowledge_id.strip()

        if not knowledge_id:
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        if resolution_status is not None:
            if not isinstance(resolution_status, str):
                raise TypeError(
                    "resolution_status must be a string"
                )

            resolution_status = resolution_status.strip()

            if resolution_status not in {
                RESOLUTION_RESOLVED,
                RESOLUTION_UNRESOLVED,
            }:
                raise ValueError(
                    "resolution_status must be "
                    "RESOLVED or UNRESOLVED"
                )

        if resolution_status is None:
            rows = self._connection.execute(
                """
                SELECT data
                FROM knowledge_conflict_records
                WHERE first_knowledge_id = ?
                   OR second_knowledge_id = ?
                ORDER BY created_at ASC, conflict_id ASC
                """,
                (
                    knowledge_id,
                    knowledge_id,
                ),
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT data
                FROM knowledge_conflict_records
                WHERE (
                    first_knowledge_id = ?
                    OR second_knowledge_id = ?
                )
                AND resolution_status = ?
                ORDER BY created_at ASC, conflict_id ASC
                """,
                (
                    knowledge_id,
                    knowledge_id,
                    resolution_status,
                ),
            ).fetchall()

        return [
            KnowledgeConflictRecord(
                **self._deserialize(row["data"])
            )
            for row in rows
        ]

    def knowledge_conflict_context(
        self,
        knowledge_id: str,
    ) -> dict:
        if not isinstance(knowledge_id, str):
            raise TypeError(
                "knowledge_id must be a string"
            )

        knowledge_id = knowledge_id.strip()

        if not knowledge_id:
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        conflicts = self.conflicts_for_knowledge(
            knowledge_id
        )

        resolved_conflict_count = sum(
            1
            for conflict in conflicts
            if conflict.resolution_status == "RESOLVED"
        )

        unresolved_conflict_count = sum(
            1
            for conflict in conflicts
            if conflict.resolution_status == "UNRESOLVED"
        )

        return {
            "knowledge_id": knowledge_id,
            "conflict_count": len(conflicts),
            "resolved_conflict_count": resolved_conflict_count,
            "unresolved_conflict_count": unresolved_conflict_count,
            "conflicts": conflicts,
        }

    def knowledge_verification_context(
        self,
        knowledge_id: str,
    ) -> dict:
        """
        Return conflict-aware verification context for one
        knowledge candidate.

        Verification status semantics:
        - NO_CONFLICT: no persisted conflicts exist
        - RESOLVED: conflicts exist and all are resolved
        - UNRESOLVED: at least one conflict remains unresolved
        """
        if not isinstance(knowledge_id, str):
            raise ValueError(
                "knowledge_id must be a string"
            )

        if not knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        context = self.knowledge_conflict_context(
            knowledge_id
        )

        conflicts = context["conflicts"]

        if not conflicts:
            conflict_status = "NO_CONFLICT"
            selected_knowledge_id = None

        elif context["unresolved_conflict_count"] > 0:
            conflict_status = "UNRESOLVED"
            selected_knowledge_id = None

        else:
            conflict_status = "RESOLVED"

            selected_ids = {
                conflict.selected_knowledge_id
                for conflict in conflicts
                if conflict.selected_knowledge_id is not None
            }

            if len(selected_ids) == 1:
                selected_knowledge_id = next(
                    iter(selected_ids)
                )
            else:
                selected_knowledge_id = None

        return {
            "knowledge_id": knowledge_id,
            "conflict_count": context["conflict_count"],
            "resolved_conflict_count": context[
                "resolved_conflict_count"
            ],
            "unresolved_conflict_count": context[
                "unresolved_conflict_count"
            ],
            "conflict_status": conflict_status,
            "selected_knowledge_id": selected_knowledge_id,
            "conflicts": conflicts,
        }

    # ---------------------------------------------------------
    # Knowledge Verification
    # ---------------------------------------------------------

    def record_knowledge_verification(
        self,
        *,
        knowledge_id: str,
        status: str,
        reason: str,
        verified_at: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Persist one knowledge verification event.

        This method records verification history only.
        It does not mutate the KnowledgeCandidate itself.
        """
        if not isinstance(knowledge_id, str):
            raise ValueError(
                "knowledge_id must be a string"
            )

        if not knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        if not isinstance(status, str):
            raise ValueError(
                "status must be a string"
            )

        allowed_statuses = {
            "VERIFIED",
            "UNVERIFIED",
            "CONFLICTED",
        }

        if status not in allowed_statuses:
            raise ValueError(
                "status must be VERIFIED, UNVERIFIED, or CONFLICTED"
            )

        if not isinstance(reason, str):
            raise ValueError(
                "reason must be a string"
            )

        if not reason.strip():
            raise ValueError(
                "reason cannot be empty"
            )

        if not isinstance(verified_at, datetime):
            raise ValueError(
                "verified_at must be a datetime"
            )

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise ValueError(
                "metadata must be a dictionary"
            )

        event_id = f"knowledge-verification:{uuid.uuid4().hex}"
        self._connection.execute(
            """
            INSERT INTO knowledge_verification_records (
                event_id,
                knowledge_id,
                status,
                reason,
                verified_at,
                metadata
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                knowledge_id,
                status,
                reason,
                verified_at.isoformat(),
                self._serialize(metadata),
            ),
        )

        self._connection.commit()

    def knowledge_verification_history(
        self,
        knowledge_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return verification history for one knowledge candidate.
        """
        if not isinstance(knowledge_id, str):
            raise ValueError(
                "knowledge_id must be a string"
            )

        if not knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        rows = self._connection.execute(
            """
            SELECT
                event_id,
                knowledge_id,
                status,
                reason,
                verified_at,
                metadata
            FROM knowledge_verification_records
            WHERE knowledge_id = ?
            ORDER BY verified_at ASC, event_id ASC
            """,
            (knowledge_id,),
        ).fetchall()

        history: list[dict[str, Any]] = []

        for row in rows:
            verified_at = datetime.fromisoformat(
                row[4]
            )

            history.append(
                {
                    "event_id": row[0],
                    "knowledge_id": row[1],
                    "status": row[2],
                    "reason": row[3],
                    "verified_at": verified_at,
                    "metadata": self._deserialize(row[5]),
                }
            )

        return history

    def knowledge_verification_lifecycle(
        self,
        knowledge_id: str,
    ) -> dict[str, Any]:
        """
        Return the current verification lifecycle state.

        The lifecycle state is derived from persisted verification
        history. No KnowledgeCandidate mutation is performed here.
        """
        if not isinstance(knowledge_id, str):
            raise ValueError(
                "knowledge_id must be a string"
            )

        if not knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        history = self.knowledge_verification_history(
            knowledge_id
        )

        if not history:
            verification_status = "UNVERIFIED"
            last_verification_status = None
            last_verified_at = None

        else:
            latest = history[-1]

            verification_status = latest["status"]
            last_verification_status = latest["status"]
            last_verified_at = latest["verified_at"]

        return {
            "knowledge_id": knowledge_id,
            "verification_status": verification_status,
            "verification_event_count": len(history),
            "last_verification_status": last_verification_status,
            "last_verified_at": last_verified_at,
            "history": history,
        }

    # ---------------------------------------------------------
    # Learning History
    # ---------------------------------------------------------

    def record_learning_history(
        self,
        *,
        topic: str,
        success: bool,
        status: str,
        verification_status: str,
        research_job_id: str = "",
        research_execution_id: str = "",
        learned_knowledge_ids: tuple[str, ...] | list[str] = (),
        verified_knowledge_ids: tuple[str, ...] | list[str] = (),
        error: str = "",
        answer: str = "",
        created_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Persist one learning attempt, including rejected/failed attempts."""
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic cannot be empty")
        if not isinstance(success, bool):
            raise ValueError("success must be a boolean")
        for field_name, value in (
            ("status", status),
            ("verification_status", verification_status),
            ("research_job_id", research_job_id),
            ("research_execution_id", research_execution_id),
            ("error", error),
            ("answer", answer),
        ):
            if not isinstance(value, str):
                raise ValueError(f"{field_name} must be a string")
        if not isinstance(learned_knowledge_ids, (tuple, list)):
            raise ValueError("learned_knowledge_ids must be a list or tuple")
        if not isinstance(verified_knowledge_ids, (tuple, list)):
            raise ValueError("verified_knowledge_ids must be a list or tuple")
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise ValueError("created_at must be a timezone-aware datetime")

        event_id = f"learning-history:{uuid.uuid4().hex}"
        record: dict[str, Any] = {
            "event_id": event_id,
            "topic": topic.strip(),
            "success": success,
            "status": status,
            "verification_status": verification_status,
            "research_job_id": research_job_id,
            "research_execution_id": research_execution_id,
            "learned_knowledge_ids": tuple(learned_knowledge_ids),
            "verified_knowledge_ids": tuple(verified_knowledge_ids),
            "error": error,
            "answer": answer,
            "created_at": created_at,
        }
        self._connection.execute(
            """
            INSERT INTO learning_history_records (
                event_id, topic, success, status, verification_status,
                research_job_id, research_execution_id, created_at, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                record["topic"],
                int(success),
                status,
                verification_status,
                research_job_id,
                research_execution_id,
                created_at.isoformat(),
                self._serialize(record),
            ),
        )
        self._connection.commit()
        return record

    def learning_history(
        self,
        *,
        topic: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return durable learning attempts in insertion order."""
        if topic is not None and (not isinstance(topic, str) or not topic.strip()):
            raise ValueError("topic must be a non-empty string when supplied")
        if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit < 1):
            raise ValueError("limit must be a positive integer")

        sql = "SELECT data FROM learning_history_records"
        parameters: list[Any] = []
        if topic is not None:
            sql += " WHERE topic = ?"
            parameters.append(topic.strip())
        sql += " ORDER BY sequence ASC"
        if limit is not None:
            sql += " LIMIT ?"
            parameters.append(limit)

        rows = self._connection.execute(sql, parameters).fetchall()
        history = [self._deserialize(row["data"]) for row in rows]
        for record in history:
            for field_name in (
                "learned_knowledge_ids",
                "verified_knowledge_ids",
            ):
                record[field_name] = tuple(record.get(field_name, ()))
        return history

    def learning_history_count(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM learning_history_records"
        ).fetchone()
        return int(row["count"])

    # ---------------------------------------------------------
    # Memory Verification
    # ---------------------------------------------------------

    def record_memory_verification(
        self,
        memory_id: str,
        status: str,
        evidence_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """
        Persist the verification state of a memory.

        This records verification metadata only.
        The MemoryCandidate itself is not modified.
        """

        if not isinstance(memory_id, str):
            raise ValueError(
                "memory_id must be a string"
            )

        memory_id = memory_id.strip()

        if not memory_id:
            raise ValueError(
                "memory_id cannot be empty"
            )

        if not isinstance(status, str):
            raise ValueError(
                "status must be a string"
            )

        status = status.strip()

        allowed_statuses = {
            "VERIFIED",
            "UNVERIFIED",
            "CONFLICTED",
        }

        if status not in allowed_statuses:
            raise ValueError(
                "status must be VERIFIED, UNVERIFIED, or CONFLICTED"
            )

        if not isinstance(evidence_id, str):
            raise ValueError(
                "evidence_id must be a string"
            )

        evidence_id = evidence_id.strip()

        if not evidence_id:
            raise ValueError(
                "evidence_id cannot be empty"
            )

        if not isinstance(reason, str):
            raise ValueError(
                "reason must be a string"
            )

        reason = reason.strip()

        if not reason:
            raise ValueError(
                "reason cannot be empty"
            )

        memory = self.get_memory(memory_id)

        if memory is None:
            raise KeyError(
                f"unknown memory: {memory_id}"
            )

        verified_at = datetime.now(timezone.utc)

        self._connection.execute(
            """
            INSERT OR REPLACE INTO memory_verification_records (
                memory_id,
                status,
                evidence_id,
                reason,
                verified_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                status,
                evidence_id,
                reason,
                verified_at.isoformat(),
            ),
        )

        self._connection.commit()

        return {
            "memory_id": memory_id,
            "status": status,
            "evidence_id": evidence_id,
            "reason": reason,
            "verified_at": verified_at,
        }

    def get_memory_verification(
        self,
        memory_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Return persisted verification state for one memory.
        """

        if not isinstance(memory_id, str):
            raise ValueError(
                "memory_id must be a string"
            )

        memory_id = memory_id.strip()

        if not memory_id:
            raise ValueError(
                "memory_id cannot be empty"
            )

        row = self._connection.execute(
            """
            SELECT
                memory_id,
                status,
                evidence_id,
                reason,
                verified_at
            FROM memory_verification_records
            WHERE memory_id = ?
            """,
            (memory_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "memory_id": row["memory_id"],
            "status": row["status"],
            "evidence_id": row["evidence_id"],
            "reason": row["reason"],
            "verified_at": datetime.fromisoformat(
                row["verified_at"]
            ),
        }

    def knowledge_conflict_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_conflict_records
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Memories
    # ---------------------------------------------------------

    def save_memory(
        self,
        memory: MemoryCandidate,
    ) -> None:
        """
        Persist one SAHIBEX memory.

        Existing memory with the same memory_id is replaced,
        matching the persistence semantics used by the research
        and knowledge storage components.
        """
        if not isinstance(memory, MemoryCandidate):
            raise TypeError(
                "memory must be a MemoryCandidate"
            )

        searchable_text = " ".join(
            [
                memory.content,
                memory.memory_type,
                memory.source,
                " ".join(memory.tags),
                self._serialize(memory.metadata),
            ]
        )
        self._save_search_indexed_record(
            canonical_sql=(
                "INSERT OR REPLACE INTO memories "
                "(memory_id, memory_type, source, importance, confidence, data) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ),
            canonical_parameters=(
                memory.memory_id,
                memory.memory_type,
                memory.source,
                memory.importance,
                memory.confidence,
                self._serialize(memory),
            ),
            index_table="memory_search",
            index_id_column="memory_id",
            record_id=memory.memory_id,
            searchable_text=searchable_text,
        )

    def get_memory(
        self,
        memory_id: str,
    ) -> Optional[MemoryCandidate]:
        """
        Retrieve one persisted memory by identity.
        """
        if not isinstance(memory_id, str):
            raise TypeError(
                "memory_id must be a string"
            )

        if not memory_id.strip():
            raise ValueError(
                "memory_id cannot be empty"
            )

        row = self._connection.execute(
            """
            SELECT data
            FROM memories
            WHERE memory_id = ?
            """,
            (memory_id,),
        ).fetchone()

        if row is None:
            return None

        return MemoryCandidate(
            **self._deserialize(row["data"])
        )
    def touch_memory(
        self,
        memory_id: str,
    ) -> MemoryCandidate:
        """
        Mark a memory as accessed.

        The original created_at timestamp remains unchanged.
        Both updated_at and last_accessed_at are refreshed.
        The updated memory is persisted and returned.
        """
        if not isinstance(memory_id, str):
            raise TypeError("memory_id must be a string")

        if not memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        memory = self.get_memory(memory_id)

        if memory is None:
            raise KeyError(
                f"unknown memory: {memory_id}"
            )

        now = datetime.now(timezone.utc)

        updated_memory = MemoryCandidate(
            memory_id=memory.memory_id,
            content=memory.content,
            memory_type=memory.memory_type,
            source=memory.source,
            importance=memory.importance,
            confidence=memory.confidence,
            tags=list(memory.tags),
            metadata=dict(memory.metadata),
            created_at=memory.created_at,
            updated_at=now,
            last_accessed_at=now,
        )

        self.save_memory(updated_memory)

        return updated_memory


    def list_memories(
        self,
    ) -> list[MemoryCandidate]:
        """
        Return all persisted memories in deterministic identity order.
        """
        rows = self._connection.execute(
            """
            SELECT data
            FROM memories
            ORDER BY memory_id ASC
            """
        ).fetchall()

        return [
            MemoryCandidate(
                **self._deserialize(row["data"])
            )
            for row in rows
        ]
    def retrieve_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        min_importance: Optional[float] = None,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        child_brain_id: Optional[str] = None,
        memory_namespace: Optional[str] = None,
    ) -> list[MemoryCandidate]:
        """
        Retrieve memories using case-insensitive relevance matching.

        Matching is performed against:
        - memory content
        - memory type
        - source
        - tags
        - serialized metadata

        Scope-bound memories require exact matching user/task/child/namespace
        context. Omitting a scope filter never exposes a record that carries
        that scope, which prevents accidental cross-context recall.

        Results are deterministic and ranked by:
        1. relevance score
        2. importance
        3. confidence
        4. memory_id
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty")

        if memory_type is not None:
            if not isinstance(memory_type, str):
                raise TypeError("memory_type must be a string")

            memory_type = memory_type.strip()

            if not memory_type:
                raise ValueError("memory_type cannot be empty")

        if min_confidence is not None:
            if not isinstance(min_confidence, (int, float)):
                raise TypeError("min_confidence must be numeric")

            if not 0.0 <= float(min_confidence) <= 1.0:
                raise ValueError(
                    "min_confidence must be between 0 and 1"
                )

        if min_importance is not None:
            if not isinstance(min_importance, (int, float)):
                raise TypeError("min_importance must be numeric")

            if not 0.0 <= float(min_importance) <= 1.0:
                raise ValueError(
                    "min_importance must be between 0 and 1"
                )

        if limit is not None:
            if not isinstance(limit, int) or isinstance(limit, bool):
                raise TypeError("limit must be an integer")
            if limit <= 0:
                raise ValueError("limit must be positive")

        requested_scope = {
            "user_id": user_id,
            "task_id": task_id,
            "child_brain_id": child_brain_id,
            "memory_namespace": memory_namespace,
        }
        for scope_name, scope_value in requested_scope.items():
            if scope_value is not None and (
                not isinstance(scope_value, str) or not scope_value.strip()
            ):
                raise ValueError(f"{scope_name} must be a non-empty string when supplied")

        query_lower = query.casefold()
        query_tokens = {
            token.strip(".,!?;:()[]{}'\"")
            for token in query_lower.split()
            if len(token.strip(".,!?;:()[]{}'\"")) >= 4
        }

        # Use the dedicated FTS5 index so retrieval does not scan or
        # deserialize every persistent memory on each request.
        fts_terms = [
            token.replace('"', '""')
            for token in (query_tokens or {query_lower})
            if token.strip()
        ]
        fts_query = " OR ".join(
            f'"{token}"'
            for token in fts_terms
        ) or f'"{query_lower.replace(chr(34), chr(34) * 2)}"'

        clauses = ["memory_search MATCH ?"]
        params = [fts_query]

        if memory_type is not None:
            clauses.append("memories.memory_type = ?")
            params.append(memory_type)

        if min_confidence is not None:
            clauses.append("memories.confidence >= ?")
            params.append(float(min_confidence))

        if min_importance is not None:
            clauses.append("memories.importance >= ?")
            params.append(float(min_importance))

        limit_sql = ""
        if limit is not None:
            limit_sql = " LIMIT ?"
            params.append(limit)

        rows = self._connection.execute(
            f"""
            SELECT
                memories.memory_id,
                memories.memory_type,
                memories.source,
                memories.importance,
                memories.confidence,
                memories.data
            FROM memories
            JOIN memory_search
              ON memory_search.memory_id = memories.memory_id
            WHERE {" AND ".join(clauses)}
            ORDER BY bm25(memory_search), memories.memory_id ASC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()

        results = []

        for row in rows:
            if memory_type is not None:
                if row["memory_type"] != memory_type:
                    continue

            if min_confidence is not None:
                if float(row["confidence"]) < float(min_confidence):
                    continue

            if min_importance is not None:
                if float(row["importance"]) < float(min_importance):
                    continue

            memory = MemoryCandidate(
                **self._deserialize(row["data"])
            )

            # Scope metadata may be stored flat for legacy callers or under a
            # dedicated "scope" object. Any malformed or unmatched stored
            # scope fails closed; unscoped legacy/global memories remain usable.
            metadata = memory.metadata if isinstance(memory.metadata, dict) else {}
            nested_scope = metadata.get("scope", {})
            if "scope" in metadata and not isinstance(nested_scope, dict):
                continue
            stored_scope = {
                "user_id": metadata.get("user_id", nested_scope.get("user_id")),
                "task_id": metadata.get("task_id", nested_scope.get("task_id")),
                "child_brain_id": metadata.get(
                    "child_brain_id",
                    metadata.get(
                        "child_id",
                        nested_scope.get("child_brain_id", nested_scope.get("child_id")),
                    ),
                ),
                "memory_namespace": metadata.get(
                    "memory_namespace", nested_scope.get("memory_namespace")
                ),
            }
            has_stored_scope = any(value is not None for value in stored_scope.values())
            has_incomplete_requested_scope = any(
                value is None for value in requested_scope.values()
            )
            scope_matches = not (
                has_stored_scope and has_incomplete_requested_scope
            )
            for scope_name, stored_value in stored_scope.items():
                if not scope_matches:
                    break
                requested_value = requested_scope[scope_name]
                # Scope matching is exact in both directions. A scoped request
                # must never inherit an unscoped/partially scoped legacy record,
                # and an unscoped request must never see a scoped record.
                if stored_value is None and requested_value is None:
                    continue
                if (
                    not isinstance(stored_value, str)
                    or not stored_value.strip()
                    or not isinstance(requested_value, str)
                    or not requested_value.strip()
                    or requested_value != stored_value
                ):
                    scope_matches = False
                    break
            if not scope_matches:
                continue

            searchable_parts = [
                memory.content,
                memory.memory_type,
                memory.source,
                *memory.tags,
                self._serialize(memory.metadata),
            ]

            searchable_text = " ".join(
                str(part) for part in searchable_parts
            ).casefold()

            token_matches = {
                token
                for token in query_tokens
                if token in searchable_text
            }

            # Exact phrase matching remains strongest. For natural
            # conversational questions, allow deterministic token-overlap
            # retrieval so "what is my project name?" can recall a memory
            # containing "my preferred project name is ...".
            if query_lower not in searchable_text and len(token_matches) < 2:
                # A single long keyword (for example, a project name) must
                # not make an otherwise unrelated multi-word query relevant.
                # Single-term queries still pass through the exact-match path.
                continue

            relevance = 0

            if query_lower in memory.content.casefold():
                relevance += 100

            if query_lower in memory.memory_type.casefold():
                relevance += 50

            if query_lower in memory.source.casefold():
                relevance += 40

            for tag in memory.tags:
                if query_lower in str(tag).casefold():
                    relevance += 30

            relevance += 8 * len(token_matches)

            if query_lower in self._serialize(
                memory.metadata
            ).casefold():
                relevance += 20

            results.append(
                (
                    relevance,
                    float(memory.importance),
                    float(memory.confidence),
                    memory.memory_id,
                    memory,
                )
            )

        results.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                -item[2],
                item[3],
            )
        )

        return [
            item[4]
            for item in results
        ]

    def find_duplicate_memories(
        self,
        memory: MemoryCandidate,
    ) -> list[MemoryCandidate]:
        """
        Find exact duplicate memories.

        Duplicate identity is based on the semantic memory payload:
        content, memory type, and source.

        The supplied memory itself is excluded from the result.
        No memory is modified or deleted.
        """
        if not isinstance(memory, MemoryCandidate):
            raise TypeError(
                "memory must be a MemoryCandidate"
            )

        rows = self._connection.execute(
            """
            SELECT data
            FROM memories
            WHERE memory_id != ?
            AND memory_type = ?
            AND source = ?
            ORDER BY memory_id ASC
            """,
            (
                memory.memory_id,
                memory.memory_type,
                memory.source,
            ),
        ).fetchall()

        duplicates = []

        for row in rows:
            candidate = MemoryCandidate(
                **self._deserialize(row["data"])
            )

            if candidate.content == memory.content:
                duplicates.append(candidate)

        return duplicates

    def plan_memory_consolidation(
        self,
        primary_memory_id: str,
        duplicate_memory_id: str,
    ) -> dict:
        """
        Create a non-destructive memory consolidation proposal.

        This method does not delete, merge, or modify memories.
        Actual consolidation requires a separate controlled action.
        """
        if not isinstance(primary_memory_id, str):
            raise TypeError(
                "primary_memory_id must be a string"
            )

        if not isinstance(duplicate_memory_id, str):
            raise TypeError(
                "duplicate_memory_id must be a string"
            )

        if not primary_memory_id.strip():
            raise ValueError(
                "primary_memory_id cannot be empty"
            )

        if not duplicate_memory_id.strip():
            raise ValueError(
                "duplicate_memory_id cannot be empty"
            )

        if primary_memory_id == duplicate_memory_id:
            raise ValueError(
                "primary and duplicate memory cannot be identical"
            )

        primary = self.get_memory(primary_memory_id)
        duplicate = self.get_memory(duplicate_memory_id)

        if primary is None:
            raise KeyError(
                f"unknown primary memory: {primary_memory_id}"
            )

        if duplicate is None:
            raise KeyError(
                f"unknown duplicate memory: {duplicate_memory_id}"
            )

        exact_duplicate = (
            primary.content == duplicate.content
            and primary.memory_type == duplicate.memory_type
            and primary.source == duplicate.source
        )

        return {
            "action": "PROPOSAL_ONLY",
            "safe_to_consolidate": exact_duplicate,
            "primary_memory_id": primary.memory_id,
            "duplicate_memory_id": duplicate.memory_id,
        }

    def detect_memory_conflict(
        self,
        memory_a: MemoryCandidate,
        memory_b: MemoryCandidate,
    ) -> dict:
        """
        Detect whether two memories contain a potential contradiction.

        Conflicting memories are preserved. No memory is deleted,
        overwritten, merged, or otherwise modified.
        """
        if not isinstance(memory_a, MemoryCandidate):
            raise TypeError(
                "memory_a must be a MemoryCandidate"
            )

        if not isinstance(memory_b, MemoryCandidate):
            raise TypeError(
                "memory_b must be a MemoryCandidate"
            )

        if memory_a.memory_id == memory_b.memory_id:
            return {
                "conflict": False,
                "status": "NOT_APPLICABLE",
                "memory_a_id": memory_a.memory_id,
                "memory_b_id": memory_b.memory_id,
                "action": "NO_ACTION",
            }

        same_subject = (
            memory_a.memory_type == memory_b.memory_type
            and set(memory_a.tags).intersection(
                set(memory_b.tags)
            )
        )

        different_content = (
            memory_a.content.strip()
            != memory_b.content.strip()
        )

        conflict_detected = bool(
            same_subject and different_content
        )

        if conflict_detected:
            return {
                "conflict": True,
                "status": "UNRESOLVED",
                "memory_a_id": memory_a.memory_id,
                "memory_b_id": memory_b.memory_id,
                "action": "REQUIRES_VERIFICATION",
            }

        return {
            "conflict": False,
            "status": "NO_CONFLICT",
            "memory_a_id": memory_a.memory_id,
            "memory_b_id": memory_b.memory_id,
            "action": "NO_ACTION",
        }

    def plan_memory_conflict_resolution(
        self,
        memory_a_id: str,
        memory_b_id: str,
        selected_memory_id: str,
        verification_source: str,
    ) -> dict:
        """
        Create a non-destructive proposal for resolving a memory conflict.

        No memory is deleted, overwritten, or modified.
        The selected memory is the proposed surviving claim,
        while the other memory is marked as the rejected claim
        within the proposal only.
        """
        if not isinstance(memory_a_id, str):
            raise TypeError(
                "memory_a_id must be a string"
            )

        if not isinstance(memory_b_id, str):
            raise TypeError(
                "memory_b_id must be a string"
            )

        if not isinstance(selected_memory_id, str):
            raise TypeError(
                "selected_memory_id must be a string"
            )

        if not isinstance(verification_source, str):
            raise TypeError(
                "verification_source must be a string"
            )

        if not memory_a_id.strip():
            raise ValueError(
                "memory_a_id cannot be empty"
            )

        if not memory_b_id.strip():
            raise ValueError(
                "memory_b_id cannot be empty"
            )

        if not selected_memory_id.strip():
            raise ValueError(
                "selected_memory_id cannot be empty"
            )

        if not verification_source.strip():
            raise ValueError(
                "verification_source cannot be empty"
            )

        if memory_a_id == memory_b_id:
            raise ValueError(
                "memory conflict requires two different memories"
            )

        if selected_memory_id not in {
            memory_a_id,
            memory_b_id,
        }:
            raise ValueError(
                "selected memory must belong to the conflict"
            )

        memory_a = self.get_memory(memory_a_id)
        memory_b = self.get_memory(memory_b_id)

        if memory_a is None:
            raise KeyError(
                f"unknown memory: {memory_a_id}"
            )

        if memory_b is None:
            raise KeyError(
                f"unknown memory: {memory_b_id}"
            )

        conflict = self.detect_memory_conflict(
            memory_a,
            memory_b,
        )

        if not conflict["conflict"]:
            raise ValueError(
                "memories do not contain a detected conflict"
            )

        rejected_memory_id = (
            memory_b_id
            if selected_memory_id == memory_a_id
            else memory_a_id
        )

        return {
            "action": "PROPOSAL_ONLY",
            "status": "PROPOSAL_ONLY",
            "memory_a_id": memory_a_id,
            "memory_b_id": memory_b_id,
            "selected_memory_id": selected_memory_id,
            "rejected_memory_id": rejected_memory_id,
            "verification_source": verification_source,
        }


    def memory_count(self) -> int:
        """
        Return the number of persisted memories.
        """
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM memories
            """
        ).fetchone()

        return int(row["count"])

        # ---------------------------------------------------------
    # Planning
    # ---------------------------------------------------------

    def save_goal(self, goal: Goal) -> None:
        """Persist one SAHIBEX planning goal."""
        if not isinstance(goal, Goal):
            raise TypeError("goal must be a Goal")

        self._connection.execute(
            """
            INSERT OR REPLACE INTO planning_goals
            (
                goal_id,
                data
            )
            VALUES (?, ?)
            """,
            (
                goal.goal_id,
                self._serialize(goal),
            ),
        )

        self._connection.commit()

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retrieve one persisted planning goal by identity."""
        if not isinstance(goal_id, str):
            raise TypeError("goal_id must be a string")

        if not goal_id.strip():
            raise ValueError("goal_id cannot be empty")

        row = self._connection.execute(
            """
            SELECT data
            FROM planning_goals
            WHERE goal_id = ?
            """,
            (goal_id,),
        ).fetchone()

        if row is None:
            return None

        data = self._deserialize(row["data"])

        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(Task(**task_data))

        data["tasks"] = tasks

        return Goal(**data)

    def list_goals(self) -> list[Goal]:
        """Return all persisted planning goals in deterministic order."""
        rows = self._connection.execute(
            """
            SELECT data
            FROM planning_goals
            ORDER BY goal_id ASC
            """
        ).fetchall()

        goals = []

        for row in rows:
            data = self._deserialize(row["data"])

            tasks = []
            for task_data in data.get("tasks", []):
                tasks.append(Task(**task_data))

            data["tasks"] = tasks

            goals.append(Goal(**data))

        return goals

    def goal_count(self) -> int:
        """Return the number of persisted planning goals."""
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM planning_goals
            """
        ).fetchone()

        return int(row["count"])

    def save_task(
        self,
        task: Task,
        goal_id: str,
    ) -> None:
        """Persist one SAHIBEX planning task."""
        if not isinstance(task, Task):
            raise TypeError("task must be a Task")

        if not isinstance(goal_id, str):
            raise TypeError("goal_id must be a string")

        if not goal_id.strip():
            raise ValueError("goal_id cannot be empty")

        self._connection.execute(
            """
            INSERT OR REPLACE INTO planning_tasks
            (
                task_id,
                goal_id,
                status,
                priority,
                parent_task_id,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task.task_id,
                goal_id,
                task.status.value,
                task.priority.value,
                task.parent_task_id,
                self._serialize(task),
            ),
        )

        self._connection.commit()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve one persisted planning task by identity."""
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")

        if not task_id.strip():
            raise ValueError("task_id cannot be empty")

        row = self._connection.execute(
            """
            SELECT data
            FROM planning_tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if row is None:
            return None

        return Task(
            **self._deserialize(row["data"])
        )

    def list_tasks(
        self,
        goal_id: str | None = None,
    ) -> list[Task]:
        """Return persisted planning tasks in deterministic order."""
        if goal_id is not None:
            if not isinstance(goal_id, str):
                raise TypeError("goal_id must be a string")

            if not goal_id.strip():
                raise ValueError("goal_id cannot be empty")

            rows = self._connection.execute(
                """
                SELECT data
                FROM planning_tasks
                WHERE goal_id = ?
                ORDER BY task_id ASC
                """,
                (goal_id,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT data
                FROM planning_tasks
                ORDER BY task_id ASC
                """
            ).fetchall()

        return [
            Task(
                **self._deserialize(row["data"])
            )
            for row in rows
        ]

    def task_count(
        self,
        goal_id: str | None = None,
    ) -> int:
        """Return the number of persisted planning tasks."""
        if goal_id is not None:
            if not isinstance(goal_id, str):
                raise TypeError("goal_id must be a string")

            if not goal_id.strip():
                raise ValueError("goal_id cannot be empty")

            row = self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM planning_tasks
                WHERE goal_id = ?
                """,
                (goal_id,),
            ).fetchone()
        else:
            row = self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM planning_tasks
                """
            ).fetchone()

        return int(row["count"])


    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def summary(self) -> dict:
        return {
            "database": str(self.database_path),
            "sources": self.source_count(),
            "documents": self.document_count(),
            "findings": self.finding_count(),
            "evidence": self.evidence_count(),
            "knowledge": self.knowledge_count(),
            "memories": self.memory_count(),
        }

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "ResearchStorage":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
