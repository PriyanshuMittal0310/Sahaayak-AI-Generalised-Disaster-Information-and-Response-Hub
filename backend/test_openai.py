import os
from dotenv import load_dotenv
from services.nlp_service import get_openai_client

# Load environment variables
load_dotenv()

# Test OpenAI client initialization
print("Testing OpenAI client initialization...")
client = get_openai_client()

if client:
    print("✅ OpenAI client initialized successfully!")
    
    # Test a simple completion
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=5
        )
        print("✅ OpenAI API test successful!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
else:
    print("❌ Failed to initialize OpenAI client")
    print("Please check that your OPENAI_API_KEY is set in the .env file")
