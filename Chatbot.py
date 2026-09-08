#!/usr/bin/env python3
"""
Professional Business Support Chatbox
Phase 4 - Business & Production Edition

Python: 3.11+

Phase 4 capabilities:
- Everything from Phase 3
- Business configuration management
- Persistent support tickets
- Ticket lifecycle management
- SLA tracking
- Priority-based ticket handling
- Audit logging
- Agent workflow
- Customer status management
- Conversation analytics
- Session activity tracking
- Knowledge-base administration
- Health/status monitoring
- Improved security controls
- Input validation
- Safer database handling
- Graceful error recovery
- CSV exports
- Production-oriented architecture

Standard library only.
No external packages required.
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# ================================================================
# APPLICATION CONFIGURATION
# ================================================================

class AppConfig:
    """Central application configuration."""

    APP_NAME = "Professional Business Support Chatbox"
    VERSION = "4.0"
    DATABASE_FILE = os.getenv(
        "BUSINESS_CHATBOT_DB",
        "business_chatbot.db",
    )

    MAX_MESSAGE_LENGTH = 2000
    MAX_SESSION_MESSAGES = 1000

    BUSINESS_NAME = os.getenv(
        "BUSINESS_NAME",
        "Professional Support Desk",
    )

    DEFAULT_AGENT = os.getenv(
        "DEFAULT_AGENT",
        "Unassigned",
    )

    SLA_HOURS = {
        "high": 4,
        "medium": 12,
        "normal": 24,
    }


# ================================================================
# DATABASE
# ================================================================

class BusinessDatabase:
    """Persistent SQLite storage layer."""

    def __init__(
        self,
        database_file: str = AppConfig.DATABASE_FILE,
    ) -> None:

        self.database_file = Path(database_file)

        self.connection = sqlite3.connect(
            self.database_file
        )

        self.connection.row_factory = sqlite3.Row

        self.create_tables()
        self.seed_knowledge()
        self.seed_configuration()

    # ============================================================
    # DATABASE SETUP
    # ============================================================

    def create_tables(self) -> None:
        """Create all required database tables."""

        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    intent TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    customer_name TEXT,
                    product TEXT,
                    priority TEXT,
                    issue TEXT,
                    reference TEXT,
                    status TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_number TEXT UNIQUE NOT NULL,
                    session_id TEXT NOT NULL,
                    customer_name TEXT,
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    assigned_agent TEXT NOT NULL DEFAULT 'Unassigned',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    sla_due_at TEXT NOT NULL,
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS configuration (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def seed_knowledge(self) -> None:
        """Seed default knowledge entries."""

        count = self.connection.execute(
            "SELECT COUNT(*) FROM knowledge"
        ).fetchone()[0]

        if count > 0:
            return

        default_knowledge = [
            (
                "security",
                "security password otp pin cvv credentials token",
                (
                    "For your security, never share passwords, PINs, "
                    "OTPs, CVVs, access tokens, or full payment-card "
                    "numbers with support personnel."
                ),
            ),
            (
                "support_process",
                "support help assistance process customer service",
                (
                    "Our support process is designed to understand "
                    "the request, collect relevant non-sensitive "
                    "information, identify the appropriate support "
                    "area, and determine the appropriate next step."
                ),
            ),
            (
                "refund",
                "refund money return payment refund request",
                (
                    "A refund request should normally include the "
                    "relevant order or invoice reference, approximate "
                    "transaction date, reason for the request, and "
                    "desired resolution. Do not provide payment "
                    "credentials."
                ),
            ),
            (
                "business_hours",
                "hours opening working business support",
                (
                    "Official business hours have not yet been "
                    "configured in the local knowledge base."
                ),
            ),
            (
                "privacy",
                "privacy personal information data protection",
                (
                    "Please provide only the information necessary "
                    "to resolve your request. Do not send passwords, "
                    "authentication codes, payment credentials, or "
                    "other highly sensitive information."
                ),
            ),
        ]

        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO knowledge
                (topic, keywords, answer)
                VALUES (?, ?, ?)
                """,
                default_knowledge,
            )

    def seed_configuration(self) -> None:
        """Create default business configuration."""

        defaults = {
            "business_name": AppConfig.BUSINESS_NAME,
            "support_status": "operational",
            "support_email": "Not configured",
            "support_hours": "Not configured",
            "default_agent": AppConfig.DEFAULT_AGENT,
        }

        with self.connection:

            for key, value in defaults.items():

                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO configuration
                    (key, value, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        key,
                        value,
                        self.now(),
                    ),
                )

    @staticmethod
    def now() -> str:
        return datetime.now().isoformat(
            timespec="seconds"
        )

    # ============================================================
    # CONFIGURATION
    # ============================================================

    def get_config(
        self,
        key: str,
    ) -> Optional[str]:

        row = self.connection.execute(
            """
            SELECT value
            FROM configuration
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

        return row["value"] if row else None

    def set_config(
        self,
        key: str,
        value: str,
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO configuration
                (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key)
                DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (
                    key,
                    value,
                    self.now(),
                ),
            )

    def get_all_config(self) -> dict[str, str]:

        rows = self.connection.execute(
            """
            SELECT key, value
            FROM configuration
            ORDER BY key
            """
        ).fetchall()

        return {
            row["key"]: row["value"]
            for row in rows
        }

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    def create_session(
        self,
        session_id: str,
    ) -> None:

        timestamp = self.now()

        with self.connection:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO sessions
                (
                    session_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, 'active', ?, ?)
                """,
                (
                    session_id,
                    timestamp,
                    timestamp,
                ),
            )

    def update_session(
        self,
        session_id: str,
        customer_name: Optional[str] = None,
        status: str = "active",
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                UPDATE sessions
                SET customer_name = ?,
                    status = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (
                    customer_name,
                    status,
                    self.now(),
                    session_id,
                ),
            )

    # ============================================================
    # MESSAGE STORAGE
    # ============================================================

    def save_message(
        self,
        session_id: str,
        role: str,
        text: str,
        intent: Optional[str],
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO messages
                (
                    session_id,
                    role,
                    text,
                    intent,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    text,
                    intent,
                    self.now(),
                ),
            )

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[sqlite3.Row]:

        rows = self.connection.execute(
            """
            SELECT
                role,
                text,
                intent,
                created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                session_id,
                limit,
            ),
        ).fetchall()

        return list(reversed(rows))

    # ============================================================
    # CUSTOMER STORAGE
    # ============================================================

    def save_customer(
        self,
        session_id: str,
        customer: dict[str, Optional[str]],
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO customers
                (
                    session_id,
                    customer_name,
                    product,
                    priority,
                    issue,
                    reference,
                    status,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(session_id)
                DO UPDATE SET
                    customer_name =
                        COALESCE(
                            excluded.customer_name,
                            customers.customer_name
                        ),
                    product =
                        COALESCE(
                            excluded.product,
                            customers.product
                        ),
                    priority =
                        COALESCE(
                            excluded.priority,
                            customers.priority
                        ),
                    issue =
                        COALESCE(
                            excluded.issue,
                            customers.issue
                        ),
                    reference =
                        COALESCE(
                            excluded.reference,
                            customers.reference
                        ),
                    status =
                        COALESCE(
                            excluded.status,
                            customers.status
                        ),
                    updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    customer.get("customer_name"),
                    customer.get("product"),
                    customer.get("priority"),
                    customer.get("issue"),
                    customer.get("reference"),
                    customer.get("status"),
                    self.now(),
                ),
            )

    # ============================================================
    # KNOWLEDGE BASE
    # ============================================================

    def search_knowledge(
        self,
        text: str,
    ) -> Optional[str]:

        rows = self.connection.execute(
            """
            SELECT keywords, answer
            FROM knowledge
            WHERE active = 1
            """
        ).fetchall()

        words = set(
            re.findall(
                r"[a-z0-9]+",
                text.lower(),
            )
        )

        best_answer = None
        best_score = 0

        for row in rows:

            keywords = set(
                row["keywords"].lower().split()
            )

            score = len(
                words.intersection(keywords)
            )

            if score > best_score:

                best_score = score
                best_answer = row["answer"]

        if best_score >= 2:
            return best_answer

        return None

    def add_knowledge(
        self,
        topic: str,
        keywords: str,
        answer: str,
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO knowledge
                (topic, keywords, answer)
                VALUES (?, ?, ?)
                """,
                (
                    topic,
                    keywords,
                    answer,
                ),
            )

    def get_knowledge(self) -> list[sqlite3.Row]:

        return list(
            self.connection.execute(
                """
                SELECT
                    id,
                    topic,
                    keywords,
                    answer
                FROM knowledge
                WHERE active = 1
                ORDER BY id
                """
            )
        )

    # ============================================================
    # ESCALATIONS
    # ============================================================

    def create_escalation(
        self,
        session_id: str,
        reason: str,
        priority: str,
    ) -> int:

        with self.connection:

            cursor = self.connection.execute(
                """
                INSERT INTO escalations
                (
                    session_id,
                    reason,
                    priority,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, 'open', ?)
                """,
                (
                    session_id,
                    reason,
                    priority,
                    self.now(),
                ),
            )

        return int(cursor.lastrowid)

    def get_open_escalations(
        self,
    ) -> list[sqlite3.Row]:

        return list(
            self.connection.execute(
                """
                SELECT
                    id,
                    session_id,
                    reason,
                    priority,
                    status,
                    created_at
                FROM escalations
                WHERE status = 'open'
                ORDER BY
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        ELSE 3
                    END,
                    id DESC
                """
            )
        )

    # ============================================================
    # TICKETS
    # ============================================================

    def create_ticket(
        self,
        session_id: str,
        customer_name: Optional[str],
        subject: str,
        description: str,
        priority: str,
    ) -> tuple[str, str]:

        ticket_number = (
            "TKT-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + secrets.token_hex(3).upper()
        )

        sla_hours = AppConfig.SLA_HOURS.get(
            priority,
            24,
        )

        created = datetime.now()

        due = created + timedelta(
            hours=sla_hours
        )

        with self.connection:

            self.connection.execute(
                """
                INSERT INTO tickets
                (
                    ticket_number,
                    session_id,
                    customer_name,
                    subject,
                    description,
                    priority,
                    status,
                    assigned_agent,
                    created_at,
                    updated_at,
                    sla_due_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)
                """,
                (
                    ticket_number,
                    session_id,
                    customer_name,
                    subject,
                    description,
                    priority,
                    AppConfig.DEFAULT_AGENT,
                    created.isoformat(
                        timespec="seconds"
                    ),
                    created.isoformat(
                        timespec="seconds"
                    ),
                    due.isoformat(
                        timespec="seconds"
                    ),
                ),
            )

        return ticket_number, due.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def get_tickets(
        self,
        status: Optional[str] = None,
    ) -> list[sqlite3.Row]:

        if status:

            return list(
                self.connection.execute(
                    """
                    SELECT *
                    FROM tickets
                    WHERE status = ?
                    ORDER BY id DESC
                    """,
                    (status,),
                )
            )

        return list(
            self.connection.execute(
                """
                SELECT *
                FROM tickets
                ORDER BY id DESC
                """
            )
        )

    def get_ticket(
        self,
        ticket_number: str,
    ) -> Optional[sqlite3.Row]:

        return self.connection.execute(
            """
            SELECT *
            FROM tickets
            WHERE ticket_number = ?
            """,
            (ticket_number.upper(),),
        ).fetchone()

    def update_ticket(
        self,
        ticket_number: str,
        status: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> bool:

        ticket = self.get_ticket(
            ticket_number
        )

        if not ticket:
            return False

        new_status = (
            status
            or ticket["status"]
        )

        new_agent = (
            agent
            or ticket["assigned_agent"]
        )

        resolved_at = (
            self.now()
            if new_status == "resolved"
            else ticket["resolved_at"]
        )

        with self.connection:

            self.connection.execute(
                """
                UPDATE tickets
                SET status = ?,
                    assigned_agent = ?,
                    updated_at = ?,
                    resolved_at = ?
                WHERE ticket_number = ?
                """,
                (
                    new_status,
                    new_agent,
                    self.now(),
                    resolved_at,
                    ticket_number.upper(),
                ),
            )

        return True

    # ============================================================
    # AUDIT LOG
    # ============================================================

    def audit(
        self,
        action: str,
        details: str = "",
        session_id: Optional[str] = None,
    ) -> None:

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO audit_logs
                (
                    session_id,
                    action,
                    details,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    action,
                    details,
                    self.now(),
                ),
            )

    def get_audit_logs(
        self,
        limit: int = 50,
    ) -> list[sqlite3.Row]:

        return list(
            self.connection.execute(
                """
                SELECT
                    session_id,
                    action,
                    details,
                    created_at
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        )

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_statistics(
        self,
    ) -> dict[str, int]:

        return {
            "messages": self.connection.execute(
                "SELECT COUNT(*) FROM messages"
            ).fetchone()[0],

            "customers": self.connection.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0],

            "sessions": self.connection.execute(
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0],

            "knowledge": self.connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge
                WHERE active = 1
                """
            ).fetchone()[0],

            "escalations": self.connection.execute(
                """
                SELECT COUNT(*)
                FROM escalations
                WHERE status = 'open'
                """
            ).fetchone()[0],

            "tickets": self.connection.execute(
                "SELECT COUNT(*) FROM tickets"
            ).fetchone()[0],

            "open_tickets": self.connection.execute(
                """
                SELECT COUNT(*)
                FROM tickets
                WHERE status IN ('open', 'in_progress')
                """
            ).fetchone()[0],

            "resolved_tickets": self.connection.execute(
                """
                SELECT COUNT(*)
                FROM tickets
                WHERE status = 'resolved'
                """
            ).fetchone()[0],

            "audit_logs": self.connection.execute(
                "SELECT COUNT(*) FROM audit_logs"
            ).fetchone()[0],
        }

    # ============================================================
    # SLA
    # ============================================================

    def get_sla_breaches(self) -> list[sqlite3.Row]:

        now = self.now()

        return list(
            self.connection.execute(
                """
                SELECT *
                FROM tickets
                WHERE status NOT IN ('resolved', 'closed')
                AND sla_due_at < ?
                ORDER BY sla_due_at
                """,
                (now,),
            )
        )

    # ============================================================
    # EXPORT
    # ============================================================

    def export_messages(
        self,
        filename: str = "conversation_export.csv",
    ) -> Path:

        output = Path(filename)

        rows = self.connection.execute(
            """
            SELECT
                session_id,
                role,
                text,
                intent,
                created_at
            FROM messages
            ORDER BY id
            """
        ).fetchall()

        with output.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "session_id",
                    "role",
                    "text",
                    "intent",
                    "created_at",
                ]
            )

            for row in rows:

                writer.writerow(
                    [
                        row["session_id"],
                        row["role"],
                        row["text"],
                        row["intent"],
                        row["created_at"],
                    ]
                )

        return output

    def export_tickets(
        self,
        filename: str = "ticket_export.csv",
    ) -> Path:

        output = Path(filename)

        rows = self.get_tickets()

        with output.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "ticket_number",
                    "session_id",
                    "customer_name",
                    "subject",
                    "description",
                    "priority",
                    "status",
                    "assigned_agent",
                    "created_at",
                    "updated_at",
                    "sla_due_at",
                    "resolved_at",
                ]
            )

            for row in rows:

                writer.writerow(
                    [
                        row["ticket_number"],
                        row["session_id"],
                        row["customer_name"],
                        row["subject"],
                        row["description"],
                        row["priority"],
                        row["status"],
                        row["assigned_agent"],
                        row["created_at"],
                        row["updated_at"],
                        row["sla_due_at"],
                        row["resolved_at"],
                    ]
                )

        return output

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(self) -> dict[str, str]:

        try:

            self.connection.execute(
                "SELECT 1"
            ).fetchone()

            return {
                "database": "OK",
                "status": "HEALTHY",
            }

        except sqlite3.Error:

            return {
                "database": "ERROR",
                "status": "DEGRADED",
            }

    # ============================================================
    # CLOSE
    # ============================================================

    def close(self) -> None:

        self.connection.close()


# ================================================================
# CHAT APPLICATION
# ================================================================

class TextChat:
    """Professional Phase 4 business support chatbot."""

    MAX_MESSAGE_LENGTH = AppConfig.MAX_MESSAGE_LENGTH

    def __init__(self) -> None:

        self.database = BusinessDatabase()

        self.session_id = self.create_session_id()

        self.session: dict[
            str,
            Optional[str]
        ] = {
            "intent": None,
            "customer_name": None,
            "priority": None,
            "issue": None,
            "product": None,
            "reference": None,
            "status": "active",
            "last_question": None,
        }

        self.running = True

        self.database.create_session(
            self.session_id
        )

        self.database.audit(
            "SESSION_CREATED",
            "New customer support session started.",
            self.session_id,
        )

        self.print_welcome()

    # ============================================================
    # SESSION ID
    # ============================================================

    @staticmethod
    def create_session_id() -> str:

        return (
            datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + "-"
            + secrets.token_hex(3)
        )

    # ============================================================
    # DISPLAY
    # ============================================================

    def print_welcome(self) -> None:

        print("=" * 82)

        print(
            f"              {AppConfig.APP_NAME.upper()}"
        )

        print(
            "                       PHASE 4"
        )

        print("=" * 82)

        self.add_message(
            (
                f"Welcome to {AppConfig.BUSINESS_NAME}. "
                "I'm your professional support assistant. "
                "I can help identify your request, maintain "
                "conversation context, create structured "
                "support tickets, and guide your issue "
                "toward the appropriate next step. "
                "How may I assist you today?"
            ),
            False,
        )

        print()
        print(
            "Type 'help' to see available commands."
        )
        print()

    def add_message(
        self,
        text: str,
        is_user: bool,
        intent: Optional[str] = None,
    ) -> None:

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        sender = (
            "You"
            if is_user
            else "Support Bot"
        )

        print()
        print(
            f"[{timestamp}] {sender}:"
        )

        print(
            f"  {text}"
        )

        self.database.save_message(
            self.session_id,
            "user" if is_user else "assistant",
            text,
            intent,
        )

    # ============================================================
    # TEXT UTILITIES
    # ============================================================

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:

        return " ".join(
            text.lower().strip().split()
        )

    @staticmethod
    def contains_any(
        text: str,
        phrases: tuple[str, ...],
    ) -> bool:

        for phrase in phrases:

            pattern = (
                rf"\b{re.escape(phrase)}\b"
            )

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    @staticmethod
    def extract_reference(
        text: str,
    ) -> Optional[str]:

        patterns = (
            r"\b(?:ord|order)[-_ ]?\d{3,}\b",
            r"\b(?:tkt|ticket)[-_ ]?\d{3,}\b",
            r"\b(?:ref|reference)[-_ ]?\d{3,}\b",
            r"#\d{3,}\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    @staticmethod
    def extract_name(
        text: str,
    ) -> Optional[str]:

        patterns = (
            r"\bmy name is ([A-Za-z][A-Za-z' -]{1,40})\b",
            r"\bi am ([A-Za-z][A-Za-z' -]{1,40})\b",
            r"\bi'm ([A-Za-z][A-Za-z' -]{1,40})\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                name = match.group(
                    1
                ).strip(
                    " .,!?:;"
                )

                if len(
                    name.split()
                ) <= 4:

                    return " ".join(
                        word.capitalize()
                        for word in name.split()
                    )

        return None

    @staticmethod
    def contains_sensitive_information(
        text: str,
    ) -> bool:

        patterns = (
            r"\b\d{13,19}\b",

            r"\b\d{3,4}\b.*"
            r"\b(?:cvv|cvc)\b",

            r"\b(?:cvv|cvc)\b.*"
            r"\b\d{3,4}\b",

            r"\b(?:password|passcode)"
            r"\s*[:=]\s*\S+",

            r"\b(?:otp|one[- ]time password)"
            r"\s*[:=]\s*\S+",

            r"\b(?:api[_ -]?key|access[_ -]?token)"
            r"\s*[:=]\s*\S+",
        )

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ============================================================
    # INTENT DETECTION
    # ============================================================

    def identify_intent(
        self,
        text: str,
    ) -> str:

        intent_groups = [

            (
                "greeting",
                (
                    "hello",
                    "hi",
                    "hey",
                    "good morning",
                    "good afternoon",
                    "good evening",
                ),
            ),

            (
                "about",
                (
                    "who are you",
                    "what are you",
                    "your purpose",
                    "what is your purpose",
                ),
            ),

            (
                "help",
                (
                    "help",
                    "what can you do",
                    "how can you help",
                ),
            ),

            (
                "thanks",
                (
                    "thank you",
                    "thanks",
                    "appreciate your help",
                    "much appreciated",
                ),
            ),

            (
                "goodbye",
                (
                    "goodbye",
                    "bye",
                    "see you",
                    "close this",
                ),
            ),

            (
                "time",
                (
                    "what time",
                    "current time",
                    "time is it",
                ),
            ),

            (
                "date",
                (
                    "what date",
                    "today's date",
                    "current date",
                    "what day is it",
                ),
            ),

            (
                "wellbeing",
                (
                    "how are you",
                    "are you available",
                    "are you there",
                ),
            ),

            (
                "account_access",
                (
                    "login",
                    "log in",
                    "sign in",
                    "account access",
                    "locked out",
                    "cannot access my account",
                    "can't access my account",
                    "forgot my password",
                    "password reset",
                ),
            ),

            (
                "billing",
                (
                    "payment",
                    "charged",
                    "charge",
                    "billing",
                    "invoice",
                    "refund",
                    "transaction",
                    "paid",
                    "payment failed",
                ),
            ),

            (
                "technical",
                (
                    "website",
                    "application",
                    "app",
                    "software",
                    "system",
                    "server",
                    "error",
                    "bug",
                    "crash",
                    "not working",
                    "broken",
                    "technical issue",
                    "technical problem",
                    "unavailable",
                ),
            ),

            (
                "order_status",
                (
                    "order",
                    "delivery",
                    "shipment",
                    "shipping",
                    "tracking",
                    "where is my order",
                    "order status",
                ),
            ),

            (
                "sales",
                (
                    "price",
                    "pricing",
                    "cost",
                    "quote",
                    "quotation",
                    "plan",
                    "subscription",
                    "product information",
                    "buy",
                    "purchase",
                ),
            ),

            (
                "complaint",
                (
                    "complaint",
                    "complain",
                    "unhappy",
                    "disappointed",
                    "poor service",
                    "bad service",
                    "escalate",
                    "manager",
                    "supervisor",
                ),
            ),

            (
                "partnership",
                (
                    "partnership",
                    "partner with",
                    "supplier",
                    "vendor",
                    "business proposal",
                    "collaboration",
                ),
            ),
        ]

        for intent, phrases in intent_groups:

            if self.contains_any(
                text,
                phrases,
            ):
                return intent

        return "general"

    # ============================================================
    # PRIORITY
    # ============================================================

    def determine_priority(
        self,
        text: str,
    ) -> str:

        if self.contains_any(
            text,
            (
                "urgent",
                "emergency",
                "critical",
                "immediately",
                "right now",
                "entire business is down",
                "production is down",
                "system is down",
            ),
        ):
            return "high"

        if self.contains_any(
            text,
            (
                "today",
                "as soon as possible",
                "cannot work",
                "unable to work",
                "affecting customers",
            ),
        ):
            return "medium"

        return (
            self.session.get(
                "priority"
            )
            or "normal"
        )

    # ============================================================
    # SESSION UPDATE
    # ============================================================

    def update_session(
        self,
        text: str,
        intent: str,
    ) -> None:

        self.session["intent"] = intent

        self.session["priority"] = (
            self.determine_priority(text)
        )

        self.session["issue"] = text

        reference = self.extract_reference(
            text
        )

        if reference:
            self.session["reference"] = reference

        name = self.extract_name(
            text
        )

        if name:

            self.session[
                "customer_name"
            ] = name

            self.database.update_session(
                self.session_id,
                name,
                "active",
            )

        self.database.save_customer(
            self.session_id,
            self.session,
        )

    # ============================================================
    # TICKET CREATION
    # ============================================================

    def create_support_ticket(
        self,
        subject: str,
        description: str,
        priority: Optional[str] = None,
    ) -> str:

        priority = (
            priority
            or self.session.get("priority")
            or "normal"
        )

        ticket_number, due = (
            self.database.create_ticket(
                self.session_id,
                self.session.get(
                    "customer_name"
                ),
                subject,
                description,
                priority,
            )
        )

        self.database.audit(
            "TICKET_CREATED",
            (
                f"{ticket_number} created with "
                f"{priority} priority. "
                f"SLA due: {due}"
            ),
            self.session_id,
        )

        return (
            f"Support ticket {ticket_number} "
            f"has been created successfully.\n\n"
            f"Priority: {priority.upper()}\n"
            f"SLA target: {due}\n"
            f"Status: OPEN\n"
            f"Assigned agent: "
            f"{AppConfig.DEFAULT_AGENT}\n\n"
            "Please keep the ticket number for "
            "future reference."
        )

    # ============================================================
    # RESPONSES
    # ============================================================

    def greeting_response(self) -> str:

        name = self.session.get(
            "customer_name"
        )

        if name:

            return (
                f"Hello, {name}. Thank you for "
                "contacting our professional support "
                "desk. How may I assist you today?"
            )

        return (
            "Hello, and thank you for contacting "
            "our professional support desk. "
            "Please describe the question, issue, "
            "or business objective you would like "
            "us to address."
        )

    def about_response(self) -> str:

        return (
            f"I am {AppConfig.APP_NAME}, "
            f"version {AppConfig.VERSION}. "
            "I am designed to support real-world "
            "business workflows by classifying "
            "requests, maintaining session context, "
            "storing conversation history, searching "
            "a local knowledge base, creating support "
            "tickets, tracking priority and SLA "
            "targets, recording audit events, and "
            "structuring issues for human support."
        )

    def help_response(self) -> str:

        return (
            "I can assist with account access, billing "
            "and payments, technical issues, orders "
            "and delivery, product and pricing enquiries, "
            "complaints, partnerships, and general "
            "business questions.\n\n"
            "Business commands:\n"
            "  help\n"
            "  history\n"
            "  stats\n"
            "  session\n"
            "  knowledge\n"
            "  escalations\n"
            "  tickets\n"
            "  sla\n"
            "  audit\n"
            "  config\n"
            "  health\n"
            "  export\n"
            "  clear\n"
            "  quit / exit"
        )

    def technical_response(
        self,
        text: str,
    ) -> str:

        self.session["status"] = (
            "technical_details_requested"
        )

        self.database.save_customer(
            self.session_id,
            self.session,
        )

        return (
            "I understand that you're experiencing "
            "a technical issue. Let's isolate the "
            "problem systematically.\n\n"
            "Please provide:\n"
            "1. The affected product, application, "
            "or website.\n"
            "2. What you were trying to do.\n"
            "3. What happened instead, including "
            "any non-sensitive error message.\n"
            "4. When the issue started and whether "
            "other users are affected.\n\n"
            "If the issue is business-critical, "
            "I can structure it as a support ticket "
            "for human follow-up.\n\n"
            "Please do not provide passwords, access "
            "tokens, OTPs, or other credentials."
        )

    def billing_response(
        self,
        text: str,
    ) -> str:

        if self.contains_any(
            text,
            (
                "charged twice",
                "double charge",
                "duplicate charge",
                "charged two times",
            ),
        ):

            return (
                "I understand that you are reporting "
                "a possible duplicate charge. Please "
                "provide the relevant invoice or "
                "transaction reference, approximate "
                "date, and amount. Do not provide "
                "your full card number, CVV, PIN, "
                "password, or verification code.\n\n"
                "If the duplicate charge requires "
                "formal investigation, I can create "
                "a support ticket."
            )

        if self.contains_any(
            text,
            (
                "refund",
                "money back",
                "want my money back",
            ),
        ):

            return (
                "I can help structure the refund "
                "request. Please provide what was "
                "purchased, the approximate transaction "
                "date, the reason for the request, "
                "and any order or invoice reference. "
                "Never share payment credentials.\n\n"
                "Once the relevant details are available, "
                "the request can be recorded for support "
                "review."
            )

        if self.contains_any(
            text,
            (
                "payment failed",
                "payment declined",
                "couldn't pay",
                "could not pay",
            ),
        ):

            return (
                "I understand that the payment did "
                "not complete successfully. Please "
                "tell me whether it was declined "
                "immediately or appeared successful "
                "before failing. If an error message "
                "was displayed, provide the wording "
                "without sharing payment credentials."
            )

        return (
            "I can assist with the billing enquiry. "
            "Please clarify whether the issue concerns "
            "an unexpected charge, invoice, failed "
            "payment, duplicate transaction, or "
            "refund. Include the relevant reference "
            "and approximate date if available."
        )

    def account_response(
        self,
        text: str,
    ) -> str:

        if self.contains_any(
            text,
            (
                "forgot my password",
                "password reset",
                "forgot password",
            ),
        ):

            return (
                "Please use the official password-reset "
                "process for the account. If the reset "
                "message does not arrive or the process "
                "fails, tell me what happens and I can "
                "help troubleshoot the issue. Never "
                "send your password or verification code."
            )

        if self.contains_any(
            text,
            (
                "locked out",
                "account locked",
                "locked account",
            ),
        ):

            return (
                "I understand that you are unable to "
                "access the account because it appears "
                "to be locked. Please tell me what "
                "message you receive when attempting "
                "to sign in and whether you have already "
                "completed account recovery. Do not "
                "provide your password or security code."
            )

        return (
            "I can help investigate the account-access "
            "problem. Please describe what happens "
            "when you attempt to sign in, including "
            "any non-sensitive error message."
        )

    def order_response(
        self,
        text: str,
    ) -> str:

        reference = self.extract_reference(
            text
        )

        if reference:

            self.session[
                "reference"
            ] = reference

            self.session[
                "status"
            ] = "reference_received"

            self.database.save_customer(
                self.session_id,
                self.session,
            )

            return (
                f"Thank you. I have recorded "
                f"reference {reference}. "
                "This application does not have "
                "access to a live order-management "
                "system, so I will not invent a "
                "current status.\n\n"
                "Please confirm whether you need "
                "the order status, delivery date, "
                "tracking assistance, or help with "
                "a delayed or missing order."
            )

        return (
            "I can help with the order enquiry. "
            "Please provide your order or reference "
            "number if available and tell me whether "
            "you need the current status, delivery "
            "information, tracking assistance, or "
            "help with a delayed or missing order."
        )

    def sales_response(
        self,
        text: str,
    ) -> str:

        return (
            "I'd be pleased to help with the product "
            "or pricing enquiry. Please tell me what "
            "you need the product or service to "
            "accomplish, approximately how many users "
            "or units are involved, your expected "
            "timeframe, and any requirements important "
            "to your organization.\n\n"
            "This local version does not have access "
            "to a live pricing catalogue, so I will "
            "not invent current prices."
        )

    def complaint_response(
        self,
        text: str,
    ) -> str:

        self.session["priority"] = "high"

        self.session["status"] = (
            "escalation_requested"
        )

        self.database.save_customer(
            self.session_id,
            self.session,
        )

        escalation_id = (
            self.database.create_escalation(
                self.session_id,
                text,
                "high",
            )
        )

        self.database.audit(
            "ESCALATION_CREATED",
            f"Escalation #{escalation_id} created.",
            self.session_id,
        )

        return (
            "I'm sorry that your experience has "
            "not met expectations. I take the "
            "concern seriously.\n\n"
            f"I have classified this as a "
            f"HIGH-priority escalation "
            f"(#{escalation_id}).\n\n"
            "Please provide what happened, when it "
            "happened, which product or service was "
            "affected, and the resolution you believe "
            "would be appropriate.\n\n"
            "If a formal support record is required, "
            "I can create a ticket from the information "
            "you provide."
        )

    def partnership_response(
        self,
        text: str,
    ) -> str:

        return (
            "Thank you for the business proposal. "
            "To assess the request properly, please "
            "provide a brief description of your "
            "organization, the proposed partnership "
            "or collaboration, the value it could "
            "create, the relevant department, and "
            "your preferred next step."
        )

    def general_response(
        self,
        text: str,
    ) -> str:

        knowledge_answer = (
            self.database.search_knowledge(
                text
            )
        )

        if knowledge_answer:
            return knowledge_answer

        recent_messages = (
            self.database.get_session_messages(
                self.session_id,
                8,
            )
        )

        if len(recent_messages) >= 3:

            return (
                "I understand that this is part "
                "of the current conversation. To "
                "make sure I address the correct "
                "objective, please tell me the "
                "specific outcome you need. I can "
                "then help identify the appropriate "
                "next step."
            )

        return (
            "Thank you for your message. I can "
            "assist, but I need a little more "
            "context to provide a useful response. "
            "Please explain what you are trying "
            "to accomplish, what happened, and "
            "what outcome you would like."
        )

    # ============================================================
    # RESPONSE ENGINE
    # ============================================================

    def get_response(
        self,
        message: str,
    ) -> str:

        text = self.normalize_text(
            message
        )

        intent = self.identify_intent(
            text
        )

        self.update_session(
            text,
            intent,
        )

        if intent == "greeting":
            return self.greeting_response()

        if intent == "about":
            return self.about_response()

        if intent == "help":
            return self.help_response()

        if intent == "thanks":

            return (
                "You're very welcome. I'm glad "
                "I could assist. If you have another "
                "question or issue, please describe "
                "it and I'll continue from the current "
                "conversation."
            )

        if intent == "goodbye":

            self.running = False

            self.database.update_session(
                self.session_id,
                self.session.get(
                    "customer_name"
                ),
                "closed",
            )

            return (
                "Thank you for contacting our support "
                "desk. I appreciate the opportunity "
                "to assist you. Goodbye."
            )

        if intent == "time":

            current_time = datetime.now().strftime(
                "%I:%M:%S %p"
            )

            return (
                f"The current local system time "
                f"is {current_time}."
            )

        if intent == "date":

            current_date = datetime.now().strftime(
                "%A, %d %B %Y"
            )

            return (
                f"Today's date is {current_date}."
            )

        if intent == "wellbeing":

            return (
                "I'm available and ready to assist. "
                "Please describe the question, issue, "
                "or business objective you would like "
                "to address."
            )

        if intent == "account_access":
            return self.account_response(text)

        if intent == "billing":
            return self.billing_response(text)

        if intent == "technical":
            return self.technical_response(text)

        if intent == "order_status":
            return self.order_response(text)

        if intent == "sales":
            return self.sales_response(text)

        if intent == "complaint":
            return self.complaint_response(text)

        if intent == "partnership":
            return self.partnership_response(text)

        return self.general_response(text)

    # ============================================================
    # MESSAGE PROCESSING
    # ============================================================

    def send_message(
        self,
        message: str,
    ) -> None:

        message = " ".join(
            message.strip().split()
        )

        if not message:

            print(
                "Support Bot: Please enter a "
                "question or describe the issue."
            )

            return

        if len(message) > self.MAX_MESSAGE_LENGTH:

            print(
                f"Support Bot: Your message exceeds "
                f"the {self.MAX_MESSAGE_LENGTH}-character "
                "limit. Please summarize the key "
                "information."
            )

            return

        if self.contains_sensitive_information(
            message
        ):

            self.database.audit(
                "SECURITY_BLOCK",
                "Potential sensitive credential input blocked.",
                self.session_id,
            )

            self.add_message(
                (
                    "For your security, please do "
                    "not send passwords, full payment "
                    "card numbers, PINs, OTPs, CVVs, "
                    "access tokens, or authentication "
                    "credentials. Please remove that "
                    "information and send only the "
                    "non-sensitive details relevant "
                    "to your request."
                ),
                False,
            )

            return

        try:

            intent = self.identify_intent(
                message
            )

            self.add_message(
                message,
                True,
                intent,
            )

            response = self.get_response(
                message
            )

            self.add_message(
                response,
                False,
                self.session.get(
                    "intent"
                ),
            )

        except Exception as error:

            self.database.audit(
                "APPLICATION_ERROR",
                type(error).__name__,
                self.session_id,
            )

            print(
                "[Internal processing error handled safely.]"
            )

            self.add_message(
                (
                    "I'm sorry, but I encountered "
                    "an unexpected processing problem. "
                    "Your request could not be completed. "
                    "Please try again with a shorter "
                    "description."
                ),
                False,
            )

    # ============================================================
    # DISPLAY COMMANDS
    # ============================================================

    def show_history(self) -> None:

        rows = (
            self.database.get_session_messages(
                self.session_id,
                AppConfig.MAX_SESSION_MESSAGES,
            )
        )

        print()
        print("=" * 82)
        print(
            "                    CONVERSATION HISTORY"
        )
        print("=" * 82)

        if not rows:

            print(
                "No conversation history is available."
            )

        else:

            for row in rows:

                print(
                    f"[{row['created_at']}] "
                    f"{row['role'].title()}: "
                    f"{row['text']}"
                )

        print("=" * 82)

    def show_stats(self) -> None:

        statistics = (
            self.database.get_statistics()
        )

        session_messages = len(
            self.database.get_session_messages(
                self.session_id,
                AppConfig.MAX_SESSION_MESSAGES,
            )
        )

        print()
        print("=" * 82)
        print(
            "                       SYSTEM STATISTICS"
        )
        print("=" * 82)

        for key, value in statistics.items():

            print(
                f"{key.replace('_', ' ').title():<25}: "
                f"{value}"
            )

        print()
        print(
            f"Current session messages : "
            f"{session_messages}"
        )

        print(
            f"Current intent           : "
            f"{self.session.get('intent') or 'Not determined'}"
        )

        print(
            f"Current priority         : "
            f"{self.session.get('priority') or 'Normal'}"
        )

        print("=" * 82)

    def show_session(self) -> None:

        print()
        print("=" * 82)
        print(
            "                         SESSION CONTEXT"
        )
        print("=" * 82)

        fields = (
            ("Session ID", None),
            ("Intent", "intent"),
            ("Customer name", "customer_name"),
            ("Priority", "priority"),
            ("Issue", "issue"),
            ("Product", "product"),
            ("Reference", "reference"),
            ("Status", "status"),
        )

        for label, key in fields:

            if key is None:
                value = self.session_id
            else:
                value = self.session.get(key)

            if not value:
                value = "Not provided"

            print(
                f"{label:<20}: {value}"
            )

        print("=" * 82)

    def show_knowledge(self) -> None:

        entries = (
            self.database.get_knowledge()
        )

        print()
        print("=" * 82)
        print(
            "                         KNOWLEDGE BASE"
        )
        print("=" * 82)

        for entry in entries:

            print()
            print(
                f"[{entry['id']}] "
                f"{entry['topic']}"
            )

            print(
                f"Keywords: {entry['keywords']}"
            )

            print(
                f"Answer: {entry['answer']}"
            )

        print("=" * 82)

    def show_escalations(self) -> None:

        escalations = (
            self.database.get_open_escalations()
        )

        print()
        print("=" * 82)
        print(
            "                         OPEN ESCALATIONS"
        )
        print("=" * 82)

        if not escalations:

            print(
                "No open escalations."
            )

        else:

            for escalation in escalations:

                print(
                    f"#{escalation['id']} | "
                    f"{escalation['priority'].upper()} | "
                    f"{escalation['created_at']}"
                )

                print(
                    f"Session: "
                    f"{escalation['session_id']}"
                )

                print(
                    f"Reason: "
                    f"{escalation['reason']}"
                )

                print()

        print("=" * 82)

    # ============================================================
    # TICKETS
    # ============================================================

    def show_tickets(self) -> None:

        tickets = (
            self.database.get_tickets()
        )

        print()
        print("=" * 110)
        print(
            "                              SUPPORT TICKETS"
        )
        print("=" * 110)

        if not tickets:

            print("No support tickets found.")

        else:

            for ticket in tickets:

                print(
                    f"{ticket['ticket_number']} | "
                    f"{ticket['priority'].upper():<6} | "
                    f"{ticket['status'].upper():<12} | "
                    f"{ticket['assigned_agent']}"
                )

                print(
                    f"Subject: "
                    f"{ticket['subject']}"
                )

                print(
                    f"Customer: "
                    f"{ticket['customer_name'] or 'Not provided'}"
                )

                print(
                    f"SLA due: "
                    f"{ticket['sla_due_at']}"
                )

                print("-" * 110)

        print("=" * 110)

    def show_sla(self) -> None:

        breaches = (
            self.database.get_sla_breaches()
        )

        tickets = self.database.get_tickets()

        active = [
            ticket
            for ticket in tickets
            if ticket["status"]
            not in ("resolved", "closed")
        ]

        print()
        print("=" * 82)
        print(
            "                         SLA MONITOR"
        )
        print("=" * 82)

        print(
            f"Active tickets : {len(active)}"
        )

        print(
            f"SLA breaches   : {len(breaches)}"
        )

        if breaches:

            print()
            print("BREACHED TICKETS:")

            for ticket in breaches:

                print(
                    f"- {ticket['ticket_number']} | "
                    f"{ticket['priority'].upper()} | "
                    f"Due: {ticket['sla_due_at']}"
                )

        print("=" * 82)

    # ============================================================
    # AUDIT
    # ============================================================

    def show_audit(self) -> None:

        logs = (
            self.database.get_audit_logs()
        )

        print()
        print("=" * 100)
        print(
            "                         AUDIT LOG"
        )
        print("=" * 100)

        if not logs:

            print("No audit events recorded.")

        else:

            for log in logs:

                print(
                    f"[{log['created_at']}] "
                    f"{log['action']}"
                )

                if log["session_id"]:

                    print(
                        f"Session: "
                        f"{log['session_id']}"
                    )

                if log["details"]:

                    print(
                        f"Details: "
                        f"{log['details']}"
                    )

                print()

        print("=" * 100)

    # ============================================================
    # CONFIGURATION
    # ============================================================

    def show_config(self) -> None:

        config = (
            self.database.get_all_config()
        )

        print()
        print("=" * 82)
        print(
            "                       BUSINESS CONFIGURATION"
        )
        print("=" * 82)

        for key, value in config.items():

            print(
                f"{key:<25}: {value}"
            )

        print("=" * 82)

    # ============================================================
    # HEALTH
    # ============================================================

    def show_health(self) -> None:

        health = (
            self.database.health_check()
        )

        print()
        print("=" * 82)
        print(
            "                         SYSTEM HEALTH"
        )
        print("=" * 82)

        print(
            f"Application : {AppConfig.APP_NAME}"
        )

        print(
            f"Version     : {AppConfig.VERSION}"
        )

        print(
            f"Database    : {health['database']}"
        )

        print(
            f"Status      : {health['status']}"
        )

        print("=" * 82)

    # ============================================================
    # EXPORT
    # ============================================================

    def export_data(self) -> None:

        messages = (
            self.database.export_messages()
        )

        tickets = (
            self.database.export_tickets()
        )

        self.database.audit(
            "DATA_EXPORTED",
            (
                f"Messages: {messages.name}; "
                f"Tickets: {tickets.name}"
            ),
            self.session_id,
        )

        print()
        print(
            "Business data exported successfully."
        )

        print(
            f"Messages: {messages.resolve()}"
        )

        print(
            f"Tickets : {tickets.resolve()}"
        )

    # ============================================================
    # CLEAR SESSION
    # ============================================================

    def clear_session(self) -> None:

        old_session = self.session_id

        self.database.update_session(
            old_session,
            self.session.get(
                "customer_name"
            ),
            "closed",
        )

        self.database.audit(
            "SESSION_CLOSED",
            "Session closed by user.",
            old_session,
        )

        self.session_id = (
            self.create_session_id()
        )

        self.session = {
            "intent": None,
            "customer_name": None,
            "priority": None,
            "issue": None,
            "product": None,
            "reference": None,
            "status": "active",
            "last_question": None,
        }

        self.database.create_session(
            self.session_id
        )

        self.database.audit(
            "SESSION_CREATED",
            "New session created after reset.",
            self.session_id,
        )

        print()
        print(
            f"Previous session {old_session} "
            "has been closed."
        )

        print(
            f"New session: {self.session_id}"
        )

        self.add_message(
            (
                "The new conversation session "
                "is ready. How may I assist you?"
            ),
            False,
        )

    # ============================================================
    # HELP
    # ============================================================

    def show_help(self) -> None:

        print()
        print("=" * 82)
        print(
            "                              HELP"
        )
        print("=" * 82)

        print(
            "You can communicate with the chatbot "
            "using normal language."
        )

        print()
        print("Commands:")

        commands = [
            ("help", "Show help information"),
            ("history", "Show current conversation"),
            ("stats", "Show system statistics"),
            ("session", "Show current context"),
            ("knowledge", "Show knowledge base"),
            ("escalations", "Show open escalations"),
            ("tickets", "Show support tickets"),
            ("sla", "Show SLA information"),
            ("audit", "Show audit events"),
            ("config", "Show business configuration"),
            ("health", "Run system health check"),
            ("export", "Export business data to CSV"),
            ("clear", "Close current session and start another"),
            ("quit / exit", "Exit the chatbot"),
        ]

        for command, description in commands:

            print(
                f"  {command:<16} - {description}"
            )

        print()
        print(
            "Security: never provide passwords, PINs, "
            "OTPs, CVVs, full card numbers, access "
            "tokens, or authentication credentials."
        )

        print("=" * 82)

    # ============================================================
    # APPLICATION LOOP
    # ============================================================

    def run(self) -> None:

        print(
            "You may begin by describing your "
            "question or business issue."
        )

        print(
            "Type 'help' for available commands.\n"
        )

        try:

            while self.running:

                try:

                    user_input = input(
                        "You > "
                    ).strip()

                except (
                    EOFError,
                    KeyboardInterrupt,
                ):

                    print()

                    print(
                        "Thank you for contacting "
                        "the support desk. Goodbye!"
                    )

                    break

                command = self.normalize_text(
                    user_input
                )

                if command in (
                    "quit",
                    "exit",
                    "q",
                ):

                    print()

                    print(
                        "Thank you for contacting "
                        "the support desk. Goodbye!"
                    )

                    break

                if command == "help":
                    self.show_help()
                    continue

                if command == "history":
                    self.show_history()
                    continue

                if command == "stats":
                    self.show_stats()
                    continue

                if command == "session":
                    self.show_session()
                    continue

                if command == "knowledge":
                    self.show_knowledge()
                    continue

                if command == "escalations":
                    self.show_escalations()
                    continue

                if command == "tickets":
                    self.show_tickets()
                    continue

                if command == "sla":
                    self.show_sla()
                    continue

                if command == "audit":
                    self.show_audit()
                    continue

                if command == "config":
                    self.show_config()
                    continue

                if command == "health":
                    self.show_health()
                    continue

                if command == "export":
                    self.export_data()
                    continue

                if command == "clear":
                    self.clear_session()
                    continue

                self.send_message(
                    user_input
                )

        finally:

            self.database.audit(
                "APPLICATION_SHUTDOWN",
                "Chatbot application stopped.",
                self.session_id,
            )

            self.database.close()


# ================================================================
# ENTRY POINT
# ================================================================

def main() -> None:
    """Application entry point."""

    chatbot = TextChat()

    chatbot.run()


if __name__ == "__main__":
    main()