import json
from groq import Groq
import re, os
from dotenv import load_dotenv

load_dotenv()
api_Key = os.getenv("GROQ_KEY")
client = Groq(api_key=api_Key)

def user_info_agent(user_message: str, message_history: list, persona: str = None) -> str:
    """
    Enhanced agent that considers persona preferences when planning
    """
    
    system_prompt = f"""
    You are a specialized travel planning assistant focused on creating one-day city tours.
    Your role is to act as a friendly, professional tour guide.
    
    Follow these rules:
    1. Greet the user warmly if it's their first message
    2. Keep responses focused on the user's needs without mentioning internal processes
    3. Never mention preferences being blank or persona updates in responses
    4. Ask for missing information in a natural, conversational way
    
    Missing information priority:
    1. City (if empty)
    2. Timings (if empty)
    3. Budget (if empty)
    4. Interests (if empty, consider persona preferences)
    5. Starting point (if empty)
    
    Response format:
    1. Start with a warm greeting if it's the first message
    2. Acknowledge any information provided
    3. Ask for missing information in a natural way
    4. Say "Thanks, I will be now developing an optimize tour plan for you." only when all information is complete
    
    Remember:
    - Keep the tone friendly and professional
    - Don't mention system processes or internal notes
    - Focus on gathering information naturally
    - Consider persona preferences in suggestions but don't mention them explicitly
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for msg in message_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error processing request: {str(e)}"

def extract_preferences(user_message: str, persona: str = None) -> dict:   
    """
    Enhanced preference extraction that considers persona traits
    """
    system_prompt = f"""
    You are a JSON extraction assistant. Extract user preferences with the following rules:
    1. Use this exact JSON structure
    2. Only fill in fields with explicit user mentions
    3. Use null for unknown fields
    4. Normalize data (e.g., lowercase interests)
    
    6. Be precise in extracting information

    JSON Schema:
    {{
        "city": "string or null",
        "time_range": "string or null (format: 'HH:MM AM/PM - HH:MM AM/PM')",
        "budget": "string or null (options: 'low', 'medium', 'high')",
        "interests": ["list of lowercase strings or empty list"],
        "starting_point": "string or null",
        "persona": "{persona if persona else 'null'}"
    }}
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.01,
            max_tokens=512,
            response_format={"type": "json_object"}
        )

        response_content = completion.choices[0].message.content

        try:
            preferences = json.loads(response_content)
            return preferences
        except json.JSONDecodeError:
            json_match = re.search(r'```json\n(.*?)```', response_content, re.DOTALL)
            if json_match:
                preferences = json.loads(json_match.group(1))
                return preferences
            
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                preferences = json.loads(json_match.group(0))
                return preferences

            raise ValueError("Could not extract valid JSON")

    except Exception as e:
        return {
            "error": f"Extraction error: {str(e)}"
        }
