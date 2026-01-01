import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("nexus.brain")

# Initialize Vertex AI
PROJECT_ID = "nexus-dyron-777"
REGION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
except Exception as e:
    logger.error(f"Failed to initialize Vertex AI: {e}")

MODEL_ID = "claude-3-5-haiku@20241022"

def analyze_market(data: Any) -> Dict[str, Any]:
    """
    Analyzes market data using Vertex AI (Claude 3.5 Haiku).
    
    Args:
        data (Any): The OHLCV data or market context to analyze.
        
    Returns:
        Dict[str, Any]: JSON response containing signal and confidence.
    """
    try:
        model = GenerativeModel(MODEL_ID)
        
        system_instruction = (
            "You are NEXUS, an execution algorithm. Analyze this OHLCV data. "
            "Output strictly JSON: {signal: 'BUY'|'SELL'|'WAIT', confidence: 0.0-1.0}."
        )
        
        # Convert data to string if it's not already
        data_str = str(data)
        
        prompt = f"{system_instruction}\n\nData:\n{data_str}"
        
        logger.info(f"Sending analysis request to {MODEL_ID}")
        
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
        result_text = response.text
        logger.info("Analysis complete.")
        
        # Parse JSON
        result_json = json.loads(result_text)
        return result_json

    except Exception as e:
        logger.error(f"Error during market analysis: {e}")
        return {"signal": "WAIT", "confidence": 0.0, "error": str(e)}
