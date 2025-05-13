from groq import Groq

# Initialize API
API_KEY = "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"
client = Groq(api_key=API_KEY)

def process_transcript_with_llm(prompt, memory_context="", session_id=None):
    """Processes the transcribed text with the LLM and generates a response.
    
    Args:
        prompt (str): The user's transcribed speech
        memory_context (str): Previous conversation history to provide context
        session_id (str): The current session ID for tracking conversation flow
    """
    try:
        # Create a system message that establishes the assistant persona and includes memory
        system_message = "You are a helpful voice assistant. Keep your responses brief and conversational. Be personable but concise since this is voice output."
        
        if memory_context:
            system_message += f"\n\n{memory_context}"
            
        # Add session context if available
        if session_id:
            system_message += f"\n\nCurrent conversation session: {session_id}"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.0,
            max_tokens=150,
            top_p=1.0,
            stream=False
        )

        if completion and completion.choices:
            response = completion.choices[0].message.content.strip()
            return response
        else:
            return "Error: No response from AI"
    except Exception as e:
        print(f"Error in LLM Processing: {e}")
        return "Error processing request"