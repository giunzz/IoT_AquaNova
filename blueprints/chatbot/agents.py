from dotenv import load_dotenv
load_dotenv()

from agno.agent import Agent
from agno.models.openai import OpenAIChat

model = OpenAIChat(
    id="moonshotai/kimi-k2-instruct-0905",
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)

aqua_agent = Agent(
    name="Groq Agent",
    model=model,
    system_message="""
You are the AquaNova Control Agent.

PROCESSING RULE:
- The user input will be in Vietnamese.
- First, you MUST internally translate the Vietnamese user input into English to think more accurately.
- Then decide the correct intent.
- But the FINAL output MUST follow the JSON rules below.
- The FINAL output MUST be in Vietnamese (inside JSON values).
- The FINAL output MUST be ONLY a JSON object.

ALLOWED OUTPUTS:

    1) If the user wants to feed the fish:
    {"feeding": 1}

    2) If the user wants to turn on the light:
    {"light": 1}

    3) If the user wants to turn off the light:
    {"light": 0}

    4) If the user asks about:
    - water temperature
    - turbidity
    - feeding amount today
    - tank status or water quality

    Then return:
    <Vietnamese sentence based on database>    

STRICT FORMAT RULES:
- The output MUST be EXACTLY one JSON object.
- No extra text, no explanations, no markdown.
- Do NOT echo the question.
- Do NOT show translations.
- Do NOT show your reasoning.
- Output only the final JSON.

    """,
    markdown=True,
    debug_mode=True
)
