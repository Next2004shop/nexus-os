import vertexai
from vertexai.preview.language_models import TextGenerationModel
from google.cloud import aiplatform

PROJECT_ID = "project-bd8c584b-bec0-462d-850"
LOCATION = "us-central1"

print(f"Initializing for {PROJECT_ID} in {LOCATION}...")
aiplatform.init(project=PROJECT_ID, location=LOCATION)

print("Listing available models...")
try:
    models = aiplatform.Model.list()
    print(f"Custom Models found: {len(models)}")
    for m in models:
        print(f" - {m.display_name} ({m.resource_name})")
except Exception as e:
    print(f"Error listing custom models: {e}")

print("\nChecking Foundation Models availability...")
# There isn't a simple "list all foundation models" API that works consistently across versions,
# so we will try to instantiate a few common ones and report success/failure.

candidates = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-pro",
    "text-bison",
    "text-bison@001",
    "text-bison@002",
    "chat-bison",
    "chat-bison@001"
]

from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextGenerationModel

for model_name in candidates:
    print(f"Testing {model_name}...", end=" ")
    try:
        if "bison" in model_name:
            model = TextGenerationModel.from_pretrained(model_name)
            model.predict("test")
        else:
            model = GenerativeModel(model_name)
            model.generate_content("test")
        print("AVAILABLE ✅")
    except Exception as e:
        print(f"FAILED ❌ ({str(e)[:100]}...)")
