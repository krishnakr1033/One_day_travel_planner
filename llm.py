import json
from groq import Groq
import re, os
from dotenv import load_dotenv
import weatherForcast_agent
from langchain_groq import ChatGroq
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType


load_dotenv()
api_Key = os.getenv("GROQ_KEY")
client = Groq(api_key=api_Key)

def get_weather(city: str) -> str:
    weather_data = weatherForcast_agent.weatherForecast(city)
    return json.dumps(weather_data, indent=2)

weather_tool = Tool(
    name="WeatherInfo",
    func=get_weather,
    description="Returns hourly weather forecast for a given city"
)

llm = ChatGroq(temperature=0.7, model="llama3-8b-8192", groq_api_key=api_Key)

agent_executor = initialize_agent(
    tools=[weather_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def user_info_agent(user_message: str, message_history: list, persona: str = None, weather_json: dict = None) -> str:
    """
    Enhanced agent that considers persona preferences and weather data when planning.
    """

    # Prepare weather section of the prompt
    weather_info_text = ""
    if weather_json:
        try:
            weather_info_text = f"\n\nHere is the hourly weather forecast data (already retrieved):\n{json.dumps(weather_json, indent=2)}\n"
        except Exception:
            weather_info_text = "\n\nWeather data is available but couldn't be parsed properly."

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
    4. Say "Thanks, I will be now developing an optimized tour plan for you." only when all information is complete
    5. While you are making the travel itinerary, use the weather data below (if present) to inform the plan. If there are conditions like rain, heat, or wind, mention how they might affect travel.

    {weather_info_text}

    Remember:
    - Keep the tone friendly and professional
    - Don’t mention system processes or internal notes
    - Focus on gathering information naturally
    - Consider persona preferences in suggestions but don’t mention them explicitly
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
            max_tokens=2048,
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
        "city": "string or null (prefer to ask detailed address e.g. "Jodhpur, rajasthan, India")",
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
    
def run_with_weather_agent(user_msg: str, persona: str = None):
    """
    Extract preferences and invoke weather-based agent planning
    """
    preferences = extract_preferences(user_msg, persona)
    city = preferences.get("city")

    if city:
        query = f"""
        The user wants to travel in {city}.
        Consider weather conditions and provide a short, optimized one-day itinerary.
        Mention anything weather-related (e.g., rain, heat, wind) that might impact travel decisions.
        """
    else:
        query = "User hasn't specified the city yet. Ask for detailed location before planning the tour."

    try:
        response = agent_executor.run(query)
    except Exception as e:
        response = f"Agent error: {str(e)}"

    return {
        "preferences": preferences,
        "response": response
    }

