from google.cloud import aiplatform
import vertexai

PROJECT_ID = "project-bd8c584b-bec0-462d-850"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

print(f"Listing models in {LOCATION}...")
try:
    # This is a bit tricky with the SDK, so we'll try a simple generation with a fallback model
    # usually 'text-bison@001' is available if Gemini isn't.
    from vertexai.language_models import TextGenerationModel
    
    print("Attempting to load 'text-bison' (PaLM 2)...")
    model = TextGenerationModel.from_pretrained("text-bison")
    response = model.predict("Hello")
    print(f"Success! 'text-bison' is available. Response: {response.text}")
    
except Exception as e:
    print(f"Failed to use text-bison: {e}")

try:
    from vertexai.generative_models import GenerativeModel
    print("\nAttempting to load 'gemini-1.0-pro-001' (specific version)...")
    model = GenerativeModel("gemini-1.0-pro-001")
    response = model.generate_content("Hello")
    print(f"Success! 'gemini-1.0-pro-001' is available. Response: {response.text}")
except Exception as e:
    print(f"Failed to use gemini-1.0-pro-001: {e}")
