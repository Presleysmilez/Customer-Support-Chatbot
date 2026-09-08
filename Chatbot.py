#!/usr/bin/env python3
"""
Professional Business Support Chatbox
Phase 2

Python: 3.11+

Phase 2 capabilities:
- Professional business conversation
- Context-aware follow-up questions
- Conversation memory
- Business intent detection
- Customer-support workflows
- Technical-support workflow
- Billing and payment workflow
- Account-access workflow
- Sales and product inquiries
- Complaint and escalation handling
- Order/service-status workflow
- Customer information collection
- Real-time date and time
- Conversation history
- Conversation statistics
- Clear/reset session
- Help system
- Input validation
- Sensitive-information protection
- Graceful error handling

This version uses only Python standard-library modules.
No external packages are required.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


class TextChat:
    """Professional business support chatbot."""

    MAX_MESSAGE_LENGTH = 2000

    def __init__(self) -> None:
        self.history: list[dict[str, object]] = []

        self.session: dict[str, Optional[str]] = {
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
        self._print_welcome()

    # ============================================================
    # DISPLAY
    # ============================================================

    def _print_welcome(self) -> None:
        """Display the initial chatbot welcome message."""

        print("=" * 78)
        print("                    PROFESSIONAL BUSINESS SUPPORT")
        print("=" * 78)

        self.add_message(
            "Welcome to our professional support desk. "
            "I'm here to understand your request, gather the relevant "
            "information, and guide you toward the appropriate next step. "
            "How may I assist you today?",
            is_user=False,
        )

        print()
        print(
            "You can describe your request naturally. For example:"
        )
        print(
            "  'I cannot access my business account.'"
        )
        print(
            "  'I was charged twice for the same order.'"
        )
        print(
            "  'Our website has been unavailable since this morning.'"
        )
        print(
            "  'I'd like information about your pricing.'"
        )
        print()
        print(
            "Type 'help' to see available commands."
        )
        print()

    def add_message(self, text: str, is_user: bool) -> None:
        """Display and store a conversation message."""

        timestamp = datetime.now().strftime("%H:%M:%S")

        sender = "You" if is_user else "Support Bot"

        print()
        print(f"[{timestamp}] {sender}:")
        print(f"  {text}")

        self.history.append(
            {
                "is_user": is_user,
                "text": text,
                "timestamp": timestamp,
            }
        )

    # ============================================================
    # TEXT UTILITIES
    # ============================================================

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize whitespace and casing."""

        return " ".join(text.lower().strip().split())

    @staticmethod
    def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
        """Check whether text contains one of the supplied phrases."""

        for phrase in phrases:
            pattern = rf"\b{re.escape(phrase)}\b"

            if re.search(pattern, text, flags=re.IGNORECASE):
                return True

        return False

    @staticmethod
    def extract_reference(text: str) -> Optional[str]:
        """
        Attempt to extract a common order/ticket/reference number.

        Examples:
        ORD-10452
        TKT-2041
        REF12345
        #123456
        """

        patterns = (
            r"\b(?:ord|order)[-_ ]?\d{3,}\b",
            r"\b(?:tkt|ticket)[-_ ]?\d{3,}\b",
            r"\b(?:ref|reference)[-_ ]?\d{3,}\b",
            r"#\d{3,}\b",
        )

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                return match.group(0)

        return None

    @staticmethod
    def contains_sensitive_information(text: str) -> bool:
        """
        Detect common categories of highly sensitive information.

        This is intentionally conservative.
        """

        sensitive_patterns = (
            r"\b\d{13,19}\b",       # Possible card number
            r"\b\d{3,4}\b.*\b(?:cvv|cvc)\b",
            r"\b(?:cvv|cvc)\b.*\b\d{3,4}\b",
            r"\b(?:password|passcode)\s*[:=]\s*\S+",
            r"\b(?:otp|one[- ]time password)\s*[:=]\s*\S+",
        )

        return any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in sensitive_patterns
        )

    # ============================================================
    # INTENT DETECTION
    # ============================================================

    def identify_intent(self, text: str) -> str:
        """Identify the most likely business intent."""

        if self.contains_any(
            text,
            (
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
            ),
        ):
            return "greeting"

        if self.contains_any(
            text,
            (
                "who are you",
                "what are you",
                "your purpose",
                "what is your purpose",
            ),
        ):
            return "about"

        if self.contains_any(
            text,
            (
                "help",
                "what can you do",
                "how can you help",
            ),
        ):
            return "help"

        if self.contains_any(
            text,
            (
                "thank you",
                "thanks",
                "appreciate your help",
                "much appreciated",
            ),
        ):
            return "thanks"

        if self.contains_any(
            text,
            (
                "goodbye",
                "bye",
                "see you",
                "close this",
            ),
        ):
            return "goodbye"

        if self.contains_any(
            text,
            (
                "what time",
                "current time",
                "time is it",
            ),
        ):
            return "time"

        if self.contains_any(
            text,
            (
                "what date",
                "today's date",
                "current date",
                "what day is it",
            ),
        ):
            return "date"

        if self.contains_any(
            text,
            (
                "how are you",
                "are you available",
                "are you there",
            ),
        ):
            return "wellbeing"

        if self.contains_any(
            text,
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
        ):
            return "account_access"

        if self.contains_any(
            text,
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
        ):
            return "billing"

        if self.contains_any(
            text,
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
        ):
            return "technical"

        if self.contains_any(
            text,
            (
                "order",
                "delivery",
                "shipment",
                "shipping",
                "tracking",
                "where is my order",
                "order status",
            ),
        ):
            return "order_status"

        if self.contains_any(
            text,
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
        ):
            return "sales"

        if self.contains_any(
            text,
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
        ):
            return "complaint"

        if self.contains_any(
            text,
            (
                "partnership",
                "partner with",
                "supplier",
                "vendor",
                "business proposal",
                "collaboration",
            ),
        ):
            return "partnership"

        return "general"

    # ============================================================
    # PRIORITY
    # ============================================================

    def determine_priority(self, text: str) -> str:
        """Determine the urgency of a request."""

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

        return "normal"

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    def update_session(self, text: str, intent: str) -> None:
        """Update conversation state."""

        self.session["intent"] = intent

        priority = self.determine_priority(text)

        if priority != "normal":
            self.session["priority"] = priority

        reference = self.extract_reference(text)

        if reference:
            self.session["reference"] = reference

        self.session["issue"] = text

    def recent_user_messages(self, limit: int = 4) -> list[str]:
        """Return recent user messages."""

        messages = [
            str(message["text"])
            for message in self.history
            if message["is_user"]
        ]

        return messages[-limit:]

    # ============================================================
    # CONVERSATION RESPONSES
    # ============================================================

    def greeting_response(self) -> str:
        return (
            "Hello, and thank you for contacting our support desk. "
            "I'm ready to assist you. Please describe the issue, question, "
            "or business objective you would like us to address."
        )

    def about_response(self) -> str:
        return (
            "I am a professional business support chatbot designed to "
            "understand customer requests, maintain conversation context, "
            "identify the relevant support area, gather useful information, "
            "and provide structured guidance. In this Phase 2 version, "
            "responses are generated locally by the application's "
            "conversation engine. A real AI/LLM service can be integrated "
            "in the next phase."
        )

    def help_response(self) -> str:
        return (
            "I can assist with several common business-support scenarios, "
            "including account access, billing and payments, technical "
            "issues, orders and delivery, product or pricing enquiries, "
            "complaints, partnerships, and general business questions.\n\n"
            "For the best result, describe what happened, when it happened, "
            "what you expected, and what outcome you need."
        )

    def technical_response(self, text: str) -> str:
        """Handle technical-support conversations."""

        if self.session.get("status") == "technical_details_requested":
            return (
                "Thank you for providing that information. Based on what "
                "you've described, the next step is to isolate whether the "
                "problem is caused by the application, the user's "
                "environment, or a wider service interruption. "
                "Please confirm whether the issue affects other users as "
                "well. If possible, also provide the exact error message "
                "without including passwords, access tokens, or other "
                "credentials."
            )

        self.session["status"] = "technical_details_requested"

        return (
            "I understand that you're experiencing a technical issue. "
            "I'll help narrow it down systematically.\n\n"
            "Please provide these four details:\n"
            "1. The affected product, application, or website.\n"
            "2. What you were trying to do.\n"
            "3. What happened instead, including any error message.\n"
            "4. When the problem started and whether other users are affected.\n\n"
            "Please do not send passwords, access tokens, verification "
            "codes, or other confidential credentials."
        )

    def billing_response(self, text: str) -> str:
        """Handle billing and payment conversations."""

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
                "I understand that you're reporting a possible duplicate "
                "charge. Please provide the relevant invoice or transaction "
                "reference if you have one, along with the approximate date "
                "and amount of the transaction. Do not provide your full "
                "card number, CVV, PIN, password, or verification code."
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
                "I can help you organize the refund request. Please explain "
                "what was purchased, the approximate transaction date, the "
                "reason for the refund, and any available order or invoice "
                "reference. A payment reference is preferable to sharing "
                "full payment credentials."
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
                "I understand that the payment did not complete successfully. "
                "Please tell me whether the payment was declined immediately "
                "or appeared successful before failing. If an error message "
                "was displayed, provide the wording without sharing any "
                "card details, PINs, passwords, or security codes."
            )

        return (
            "I can assist with the billing enquiry. Please clarify whether "
            "the issue concerns an unexpected charge, an invoice, a failed "
            "payment, a duplicate transaction, or a refund. If available, "
            "include the relevant order or invoice reference and the "
            "approximate date. Please do not share full payment credentials."
        )

    def account_response(self, text: str) -> str:
        """Handle account-access conversations."""

        if self.contains_any(
            text,
            (
                "forgot my password",
                "password reset",
                "forgot password",
            ),
        ):
            return (
                "If you've forgotten your password, the appropriate first "
                "step is to use the official password-reset process for the "
                "account. If the reset message does not arrive or the reset "
                "process fails, tell me what happens and I can help you "
                "troubleshoot the issue. Please never send your password or "
                "verification code here."
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
                "I understand that you're unable to access the account "
                "because it appears to be locked. Please tell me what "
                "message you receive when attempting to sign in and whether "
                "you have already completed the account-recovery process. "
                "Do not provide your password or security code."
            )

        return (
            "I can help investigate the account-access problem. Please "
            "describe what happens when you attempt to sign in, including "
            "any non-sensitive error message. Also let me know whether the "
            "problem affects only your account or other users as well."
        )

    def order_response(self, text: str) -> str:
        """Handle order and delivery conversations."""

        reference = self.extract_reference(text)

        if reference:
            self.session["reference"] = reference

            return (
                f"Thank you. I have identified the reference "
                f"{reference}. In this Phase 2 version, I cannot access a "
                f"live order-management system, so I cannot truthfully "
                f"provide the current shipment status. However, I can "
                f"organize the request for a real support system. Please "
                f"confirm whether you are enquiring about the order status, "
                f"delivery date, delayed shipment, or a delivery problem."
            )

        return (
            "I can help with the order enquiry. Please provide your order "
            "or reference number if available and tell me whether you need "
            "the current status, delivery information, tracking assistance, "
            "or help with a delayed or missing order."
        )

    def sales_response(self, text: str) -> str:
        """Handle product and sales enquiries."""

        return (
            "I'd be pleased to help with the product or pricing enquiry. "
            "To recommend an appropriate option, please tell me what you "
            "need the service or product to accomplish, approximately how "
            "many users or units are involved, your expected timeframe, and "
            "any requirements that are important to your organization.\n\n"
            "Please note that this Phase 2 chatbot does not have access to "
            "a live pricing catalogue, so I will not invent current prices."
        )

    def complaint_response(self, text: str) -> str:
        """Handle complaints and escalation requests."""

        self.session["priority"] = "high"

        return (
            "I'm sorry that your experience has not met expectations. "
            "I take the concern seriously. To help structure the matter "
            "for review, please provide:\n"
            "1. What happened.\n"
            "2. When it happened.\n"
            "3. Which product or service was affected.\n"
            "4. What resolution you believe would be appropriate.\n\n"
            "Once those details are clear, the issue can be prepared for "
            "the appropriate support or management team."
        )

    def partnership_response(self, text: str) -> str:
        """Handle partnership and business-development enquiries."""

        return (
            "Thank you for your business proposal. To assess the request "
            "properly, please provide a brief description of your "
            "organization, the proposed partnership or collaboration, "
            "the value you believe it could create, the relevant service "
            "or department, and your preferred next step."
        )

    def general_response(self, text: str) -> str:
        """Handle general business questions."""

        recent = self.recent_user_messages()

        if len(recent) > 1:
            return (
                "Thank you for clarifying. I understand that this is part "
                "of the same conversation, and I want to make sure I address "
                "the correct objective. Please state the specific outcome "
                "you need, and I will help break the request into the "
                "appropriate next steps."
            )

        return (
            "Thank you for your message. I can help, but I need a little "
            "more context to provide a useful business response. Please "
            "tell me what you are trying to accomplish, what problem you "
            "are experiencing, and what outcome you would like."
        )

    # ============================================================
    # RESPONSE ENGINE
    # ============================================================

    def get_response(self, message: str) -> str:
        """Generate a professional response."""

        text = self.normalize_text(message)

        intent = self.identify_intent(text)

        self.update_session(text, intent)

        if intent == "greeting":
            return self.greeting_response()

        if intent == "about":
            return self.about_response()

        if intent == "help":
            return self.help_response()

        if intent == "thanks":
            return (
                "You're very welcome. I'm glad I could assist. "
                "If you have another question or issue, please describe it "
                "and I'll continue from the current conversation."
            )

        if intent == "goodbye":
            self.running = False

            return (
                "Thank you for contacting our support desk. "
                "I appreciate the opportunity to assist you. Goodbye."
            )

        if intent == "time":
            current_time = datetime.now().strftime("%I:%M:%S %p")

            return (
                f"The current local system time is {current_time}."
            )

        if intent == "date":
            current_date = datetime.now().strftime("%A, %d %B %Y")

            return (
                f"Today's date is {current_date}."
            )

        if intent == "wellbeing":
            return (
                "I'm available and ready to assist. Please describe the "
                "question, issue, or business objective you would like "
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

    def send_message(self, message: str) -> None:
        """Validate and process a user message."""

        message = " ".join(message.strip().split())

        if not message:
            print(
                "\nSupport Bot: Please enter a question or describe "
                "the issue you need assistance with."
            )
            return

        if len(message) > self.MAX_MESSAGE_LENGTH:
            print(
                f"\nSupport Bot: Your message exceeds the "
                f"{self.MAX_MESSAGE_LENGTH}-character limit. "
                "Please summarize the key information."
            )
            return

        if self.contains_sensitive_information(message):
            self.add_message(
                "For your security, please do not send passwords, "
                "full payment-card numbers, PINs, OTPs, CVVs, or other "
                "authentication credentials. Please remove that information "
                "and send only the non-sensitive details relevant to your "
                "request.",
                is_user=False,
            )
            return

        self.add_message(message, is_user=True)

        try:
            response = self.get_response(message)

            self.add_message(
                response,
                is_user=False,
            )

        except Exception:
            self.add_message(
                "I’m sorry, but I encountered an unexpected processing "
                "problem. Your request could not be completed. Please try "
                "again, and if the issue continues, provide a shorter "
                "description of the request.",
                is_user=False,
            )

    # ============================================================
    # COMMANDS
    # ============================================================

    def show_history(self) -> None:
        """Display conversation history."""

        if not self.history:
            print("\nNo conversation history is available.")
            return

        print()
        print("=" * 78)
        print("                         CONVERSATION HISTORY")
        print("=" * 78)

        for message in self.history:
            sender = (
                "You"
                if message["is_user"]
                else "Support Bot"
            )

            print(
                f"[{message['timestamp']}] "
                f"{sender}: {message['text']}"
            )

        print("=" * 78)

    def show_stats(self) -> None:
        """Display conversation statistics."""

        user_messages = sum(
            1
            for message in self.history
            if message["is_user"]
        )

        bot_messages = len(self.history) - user_messages

        print()
        print("=" * 78)
        print("                         SESSION STATISTICS")
        print("=" * 78)

        print(f"User messages       : {user_messages}")
        print(f"Bot messages        : {bot_messages}")
        print(f"Total messages      : {len(self.history)}")

        print(
            f"Current intent      : "
            f"{self.session.get('intent') or 'Not determined'}"
        )

        print(
            f"Priority            : "
            f"{self.session.get('priority') or 'Normal'}"
        )

        print(
            f"Reference           : "
            f"{self.session.get('reference') or 'None'}"
        )

        print("=" * 78)

    def show_session(self) -> None:
        """Display non-sensitive session information."""

        print()
        print("=" * 78)
        print("                         SESSION CONTEXT")
        print("=" * 78)

        fields = (
            ("Intent", "intent"),
            ("Customer name", "customer_name"),
            ("Priority", "priority"),
            ("Product", "product"),
            ("Reference", "reference"),
            ("Status", "status"),
        )

        for label, key in fields:
            value = self.session.get(key)

            if not value:
                value = "Not provided"

            print(f"{label:<20}: {value}")

        print("=" * 78)

    def clear_history(self) -> None:
        """Reset the conversation."""

        self.history.clear()

        for key in self.session:
            self.session[key] = None

        self.add_message(
            "The conversation has been reset successfully. "
            "Please describe the new question, problem, or business "
            "objective you would like help with.",
            is_user=False,
        )

    def show_help(self) -> None:
        """Display available commands."""

        print()
        print("=" * 78)
        print("                              HELP")
        print("=" * 78)

        print(
            "You can communicate with the chatbot using normal language."
        )

        print()
        print("Examples:")
        print(
            "  I cannot access my business account."
        )
        print(
            "  My payment failed this morning."
        )
        print(
            "  Our website has stopped working."
        )
        print(
            "  I need information about your pricing."
        )
        print(
            "  I want to complain about a service."
        )

        print()
        print("Commands:")
        print("  help       - Display this help information")
        print("  history    - Display the conversation history")
        print("  stats      - Display session statistics")
        print("  session    - Display current conversation context")
        print("  clear      - Reset the current conversation")
        print("  quit       - Exit the chatbot")
        print("  exit       - Exit the chatbot")

        print()
        print(
            "Security: never provide passwords, PINs, OTPs, CVVs, "
            "full payment-card numbers, or authentication credentials."
        )

        print("=" * 78)

    # ============================================================
    # APPLICATION LOOP
    # ============================================================

    def run(self) -> None:
        """Start the chatbot."""

        print(
            "You may begin by describing your question or business issue."
        )
        print(
            "Type 'help' for available commands.\n"
        )

        while self.running:
            try:
                user_input = input("You > ").strip()

            except (EOFError, KeyboardInterrupt):
                print()
                print(
                    "Thank you for contacting the support desk. Goodbye!"
                )
                break

            if not user_input:
                print(
                    "Support Bot: Please enter a message so I can assist you."
                )
                continue

            command = self.normalize_text(user_input)

            if command in ("quit", "exit", "q"):
                print()
                print(
                    "Thank you for contacting the support desk. Goodbye!"
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

            if command == "clear":
                self.clear_history()
                continue

            self.send_message(user_input)


def main() -> None:
    """Application entry point."""

    chatbot = TextChat()
    chatbot.run()


if __name__ == "__main__":
    main()