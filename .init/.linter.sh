#!/bin/bash
cd /home/kavia/workspace/code-generation/crewai-collaborative-chatbot-system-36230-36240/chatbot_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

