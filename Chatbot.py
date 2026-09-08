#!/usr/bin/env python3
"""
Simple professional text-based chatbox.
"""

import sys
from datetime import datetime


class TextChat:
    def __init__(self):
        self.history = []
        self._print_welcome()

    def _print_welcome(self):
        print("=" * 50)
        print("  Professional Chatbox (Text Mode)")
        print("=" * 50)
        self.add_message(
            "Hello! Welcome to Professional Chatbox. How can I help you today?",
            is_user=False,
        )

    def add_message(self, text: str, is_user: bool):
        timestamp = datetime.now().strftime("%H:%M")
        if is_user:
            prefix = f"[{timestamp}] You"
            # Right-align feel by indenting less on the left
            print(f"\n{prefix}:")
            print(f"  {text}")
        else:
            prefix = f"[{timestamp}] Bot"
            print(f"\n{prefix}:")
            print(f"  {text}")
        self.history.append((is_user, text, timestamp))

    def send_message(self, message: str):
        message = message.strip()
        if not message:
            return

        self.add_message(message, is_user=True)

        # Temporary response — replace with your AI call later
        response = (
            "I received your message. "
            "The AI service will be connected in the next stage."
        )
        self.add_message(response, is_user=False)

    def run(self):
        print("\nType your message and press Enter. Type 'quit' or 'exit' to leave.\n")
        while True:
            try:
                user_input = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if user_input:
                self.send_message(user_input)


def main():
    chat = TextChat()
    chat.run()


if __name__ == "__main__":
    main()