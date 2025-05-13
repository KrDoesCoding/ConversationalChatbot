<!DOCTYPE html>
<head>
    <title>Conversational AI Chatbot</title>
    
</head>
<body>

  <h1>Conversational AI Chatbot with Voice Interaction</h1>
  <p>
      An intelligent voice-based chatbot system that uses advanced AI models to have interactive, human-like conversations via speech. It listens to users, processes queries with a custom language model, and responds with natural-sounding voice output — all in real-time.
  </p>

  <hr>

  <h2>Overview</h2>
  <p>
      This project is a <strong>voice-enabled conversational chatbot</strong> that combines <strong>speech recognition</strong>,
      <strong>voice activity detection</strong>, <strong>custom LLM-based response generation</strong>, and 
      <strong>text-to-speech synthesis</strong> to simulate an interactive AI assistant. The bot remembers context, detects 
      when a user is speaking, generates intelligent responses, and speaks them back — offering an immersive 
      voice-based AI experience.
  </p>

  <hr>

  <h2>Features</h2>
  <ul>
      <li><strong>Voice Input</strong> with Real-Time VAD using <a href="https://github.com/snakers4/silero-vad" target="_blank">Silero VAD</a></li>
      <li><strong>Custom LLM-based Response Generation</strong> (using Groq API for LLaMA models)</li>
      <li><strong>Conversational Memory</strong> to maintain context across interactions</li>
      <li><strong>Realistic Text-to-Speech (TTS)</strong> using Microsoft Edge Neural Voices</li>
      <li><strong>Low Latency</strong> via threaded async pipelines and preloading</li>
      <li><strong>Modular and extensible</strong> for future multimodal support</li>
  </ul>

  <hr>

  <h2>How It Works</h2>
  <ol>
      <li><strong>Voice Activation (VAD):</strong>
          <ul>
              <li>Uses Silero VAD to detect when the user is actively speaking.</li>
              <li>Prevents recording while the AI is speaking to avoid overlap.</li>
          </ul>
      </li>
      <li><strong>Speech Recognition:</strong>
          <ul>
              <li>Converts user speech into text using a <strong>Groq-hosted</strong> <code>speech-to-text</code> model (via <code>stt_groq.py</code>).</li>
          </ul>
      </li>
      <li><strong>Response Generation:</strong>
          <ul>
              <li>The user query, along with memory, is sent to a <strong>language model API</strong> to generate a contextual response (<code>llm.py</code>).</li>
              <li>Uses LLaMA models or similar hosted via Groq API.</li>
          </ul>
      </li>
      <li><strong>Conversational Memory:</strong>
          <ul>
              <li>Maintains a SQLite-based history of conversations (<code>memory.py</code>) for contextual replies.</li>
          </ul>
      </li>
      <li><strong>Voice Output (TTS):</strong>
          <ul>
              <li>The response is spoken aloud using neural Microsoft Edge voices via the <code>edge-tts</code> library (<code>tts.py</code>).</li>
              <li>Audio is generated and played in near real-time using Pygame.</li>
          </ul>
      </li>
      <li><strong>Frontend Integration:</strong>
          <ul>
              <li>An HTML-based minimal interface (<code>fe.html</code>) that can be connected to the backend.</li>
          </ul>
      </li>
  </ol>

  <hr>

  <h2>Models Used</h2>
  <ul>
      <li><strong>STT:</strong> Whisper-like Speech-to-Text via <a href="https://groq.com/" target="_blank">Groq API</a></li>
      <li><strong>LLM:</strong> Groq-hosted <code>LLaMA 3</code> and <code>Mixtral</code> models</li>
      <li><strong>TTS:</strong> Microsoft Edge Neural Voices using <code>edge-tts</code></li>
  </ul>

</body>
</html>
