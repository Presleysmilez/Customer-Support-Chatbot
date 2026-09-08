#!/usr/bin/env python3
"""
Professional Business Support Chatbox
Phase 3

Python: 3.11+

Phase 3 capabilities:
- Everything from Phase 2
- Persistent SQLite database
- Persistent conversation history
- Persistent customer/session records
- Local business knowledge base
- Knowledge-base management
- Improved conversation context
- Customer information extraction
- Escalation tracking
- Conversation statistics
- CSV conversation export
- Session management
- Security protection
- Graceful error handling

Standard library only.
No external packages required.
"""

from __future__ import annotations

import csv
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class BusinessDatabase:
    """Persistent SQLite storage for the chatbot."""

    def __init__(self, database_file: str = "business_chatbot.db") -> None:
        self.database_file = Path(database_file)

        self.connection = sqlite3.connect(
            self.database_file
        )

        self.connection.row_factory = sqlite3.Row

        self.create_tables()
        self.seed_knowledge()

    # ============================================================
    # DATABASE SETUP
    # ============================================================

    def create_tables(self) -> None:
        """Create required database tables."""

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
                """
            )

    def seed_knowledge(self) -> None:
        """Add basic knowledge if the knowledge base is empty."""

        count = self.connection.execute(
            "SELECT COUNT(*) FROM knowledge"
        ).fetchone()[0]

        if count > 0:
            return

        default_knowledge = [
            (
                "security",
                "security password otp pin cvv credentials",
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
                    "Our support process is designed to understand the "
                    "request, collect relevant non-sensitive information, "
                    "identify the appropriate support area, and determine "
                    "the appropriate next step."
                ),
            ),
            (
                "refund",
                "refund money return payment refund request",
                (
                    "A refund request should normally include the relevant "
                    "order or invoice reference, approximate transaction "
                    "date, reason for the request, and desired resolution. "
                    "Do not provide payment credentials."
                ),
            ),
            (
                "business_hours",
                "hours opening working business support",
                (
                    "Official business hours have not yet been configured "
                    "in the local knowledge base."
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
        """Save a conversation message."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO messages
                (session_id, role, text, intent, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    text,
                    intent,
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[sqlite3.Row]:
        """Return messages for a session."""

        rows = self.connection.execute(
            """
            SELECT role, text, intent, created_at
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
        """Persist customer/session information."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO customers (
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
                    customer_name = excluded.customer_name,
                    product = excluded.product,
                    priority = excluded.priority,
                    issue = excluded.issue,
                    reference = excluded.reference,
                    status = excluded.status,
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
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

    # ============================================================
    # KNOWLEDGE BASE
    # ============================================================

    def search_knowledge(
        self,
        text: str,
    ) -> Optional[str]:
        """Search the local knowledge base."""

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
        """Add a knowledge-base entry."""

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
        """Return all active knowledge entries."""

        return list(
            self.connection.execute(
                """
                SELECT id, topic, keywords, answer
                FROM knowledge
                WHERE active = 1
                ORDER BY id
                """
            )
        )

    # ============================================================
    # ESCALATION STORAGE
    # ============================================================

    def create_escalation(
        self,
        session_id: str,
        reason: str,
        priority: str,
    ) -> None:
        """Create an escalation record."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO escalations
                (session_id, reason, priority, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    reason,
                    priority,
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

    def get_open_escalations(self) -> list[sqlite3.Row]:
        """Return open escalation records."""

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
                ORDER BY id DESC
                """
            )
        )

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_statistics(self) -> dict[str, int]:

        return {
            "messages": self.connection.execute(
                "SELECT COUNT(*) FROM messages"
            ).fetchone()[0],

            "customers": self.connection.execute(
                "SELECT COUNT(*) FROM customers"
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
        }

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

    # ============================================================
    # CLOSE
    # ============================================================

    def close(self) -> None:
        self.connection.close()


class TextChat:
    """Professional Phase 3 business support chatbot."""

    MAX_MESSAGE_LENGTH = 2000

    def __init__(self) -> None:

        self.database = BusinessDatabase()

        self.session_id = (
            datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

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
            "status": None,
            "last_question": None,
        }

        self.running = True

        self.print_welcome()

    # ============================================================
    # DISPLAY
    # ============================================================

    def print_welcome(self) -> None:

        print("=" * 78)

        print(
            "                 PROFESSIONAL BUSINESS SUPPORT"
        )

        print(
            "                              PHASE 3"
        )

        print("=" * 78)

        self.add_message(
            (
                "Welcome to our professional support desk. "
                "I'm here to understand your request, maintain "
                "the relevant conversation context, and guide "
                "you toward the appropriate next step. "
                "How may I assist you today?"
            ),
            False,
        )

        print()
        print(
            "You can describe your request naturally."
        )
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
    # SESSION
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

        self.database.save_customer(
            self.session_id,
            self.session,
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
                f"Hello, {name}. Thank you "
                "for contacting our professional "
                "support desk. How may I assist "
                "you today?"
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
            "I am a Phase 3 professional business "
            "support chatbot. I can classify "
            "customer requests, maintain session "
            "context, store conversation history, "
            "search a local knowledge base, collect "
            "non-sensitive customer information, "
            "and structure issues for escalation."
        )

    def help_response(self) -> str:

        return (
            "I can assist with account access, "
            "billing and payments, technical issues, "
            "orders and delivery, product and pricing "
            "enquiries, complaints, partnerships, "
            "and general business questions.\n\n"
            "You can also use commands such as "
            "'history', 'stats', 'session', "
            "'knowledge', 'escalations', 'export', "
            "and 'clear'."
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
                "password, or verification code."
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
                "Never share payment credentials."
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
                "This local application does not "
                "have access to a live order-management "
                "system, so I will not invent a current "
                "status. Please confirm whether you "
                "need the order status, delivery date, "
                "tracking assistance, or help with a "
                "delayed or missing order."
            )

        return (
            "I can help with the order enquiry. "
            "Please provide your order or reference "
            "number if available and tell me whether "
            "you need the current status, delivery "
            "information, tracking assistance, or help "
            "with a delayed or missing order."
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

        self.database.create_escalation(
            self.session_id,
            text,
            "high",
        )

        return (
            "I'm sorry that your experience has not "
            "met expectations. I take the concern "
            "seriously. I have classified this as a "
            "high-priority concern.\n\n"
            "Please provide what happened, when it "
            "happened, which product or service was "
            "affected, and the resolution you believe "
            "would be appropriate. The request has "
            "been structured for human review."
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

            self.add_message(
                (
                    "For your security, please do "
                    "not send passwords, full payment "
                    "card numbers, PINs, OTPs, CVVs, "
                    "or authentication credentials. "
                    "Please remove that information "
                    "and send only the non-sensitive "
                    "details relevant to your request."
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

            print(
                f"[Internal error handled safely: "
                f"{type(error).__name__}]"
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
    # COMMANDS
    # ============================================================

    def show_history(self) -> None:

        rows = (
            self.database.get_session_messages(
                self.session_id,
                1000,
            )
        )

        print()
        print("=" * 78)
        print(
            "                    CONVERSATION HISTORY"
        )
        print("=" * 78)

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

        print("=" * 78)

    def show_stats(self) -> None:

        statistics = (
            self.database.get_statistics()
        )

        session_messages = len(
            self.database.get_session_messages(
                self.session_id,
                10000,
            )
        )

        print()
        print("=" * 78)
        print(
            "                       SYSTEM STATISTICS"
        )
        print("=" * 78)

        print(
            f"Current session messages : "
            f"{session_messages}"
        )

        print(
            f"Database messages        : "
            f"{statistics['messages']}"
        )

        print(
            f"Customer records         : "
            f"{statistics['customers']}"
        )

        print(
            f"Knowledge entries        : "
            f"{statistics['knowledge']}"
        )

        print(
            f"Open escalations         : "
            f"{statistics['escalations']}"
        )

        print(
            f"Current intent            : "
            f"{self.session.get('intent') or 'Not determined'}"
        )

        print(
            f"Priority                  : "
            f"{self.session.get('priority') or 'Normal'}"
        )

        print(
            f"Reference                 : "
            f"{self.session.get('reference') or 'None'}"
        )

        print("=" * 78)

    def show_session(self) -> None:

        print()
        print("=" * 78)
        print(
            "                         SESSION CONTEXT"
        )
        print("=" * 78)

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

        print("=" * 78)

    def show_knowledge(self) -> None:

        entries = (
            self.database.get_knowledge()
        )

        print()
        print("=" * 78)
        print(
            "                         KNOWLEDGE BASE"
        )
        print("=" * 78)

        for entry in entries:

            print()
            print(
                f"[{entry['id']}] "
                f"{entry['topic']}"
            )

            print(
                f"Keywords: "
                f"{entry['keywords']}"
            )

            print(
                f"Answer: "
                f"{entry['answer']}"
            )

        print("=" * 78)

    def show_escalations(self) -> None:

        escalations = (
            self.database.get_open_escalations()
        )

        print()
        print("=" * 78)
        print(
            "                         OPEN ESCALATIONS"
        )
        print("=" * 78)

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
                    f"Reason: "
                    f"{escalation['reason']}"
                )

                print()

        print("=" * 78)

    def export_data(self) -> None:

        output = (
            self.database.export_messages()
        )

        print()
        print(
            f"Conversation data exported to:"
        )
        print(
            f"{output.resolve()}"
        )

    def clear_session(self) -> None:

        old_session = self.session_id

        self.session_id = (
            datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        for key in self.session:
            self.session[key] = None

        print()
        print(
            f"Session {old_session} has been "
            "cleared."
        )

        self.add_message(
            (
                "The new conversation session "
                "is ready. How may I assist you?"
            ),
            False,
        )

    def show_help(self) -> None:

        print()
        print("=" * 78)
        print(
            "                              HELP"
        )
        print("=" * 78)

        print(
            "You can communicate with the chatbot "
            "using normal language."
        )

        print()
        print("Commands:")

        print(
            "  help          - Show help information"
        )

        print(
            "  history       - Show current conversation"
        )

        print(
            "  stats         - Show system statistics"
        )

        print(
            "  session       - Show current context"
        )

        print(
            "  knowledge     - Show local knowledge base"
        )

        print(
            "  escalations   - Show open escalations"
        )

        print(
            "  export        - Export messages to CSV"
        )

        print(
            "  clear         - Start a new session"
        )

        print(
            "  quit / exit   - Exit the chatbot"
        )

        print()
        print(
            "Security: never provide passwords, PINs, "
            "OTPs, CVVs, full card numbers, access "
            "tokens, or authentication credentials."
        )

        print("=" * 78)

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

            self.database.close()


def main() -> None:
    """Application entry point."""

    chatbot = TextChat()

    chatbot.run()


if __name__ == "__main__":
    main()