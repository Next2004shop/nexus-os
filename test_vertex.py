import vertexai
from vertexai.generative_models import GenerativeModel
import os

PROJECT_ID = "project-bd8c584b-bec0-462d-850"
LOCATION = "us-central1"

print(f"Initializing Vertex AI for project {PROJECT_ID} in {LOCATION}...")
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print("Init successful.")
    
    print("Loading model gemini-1.0-pro...")
    model = GenerativeModel("gemini-1.0-pro")
    
    print("Generating content...")
    response = model.generate_content("Hello, are you working?")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
