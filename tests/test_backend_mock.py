import pytest
from flask import Flask
import sys
import os

# Add parent directory to path to import nexus_bridge
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_bridge import app, users
from werkzeug.security import generate_password_hash

# Mock MT5
from unittest.mock import MagicMock
import nexus_bridge
nexus_bridge.mt5 = MagicMock()
nexus_bridge.mt5.initialize.return_value = True
nexus_bridge.connection_state["status"] = "CONNECTED"

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def get_auth_headers():
    return {
        'Authorization': 'Basic ' + 'admin:securepassword'.encode('ascii').decode('ascii')
    }

def test_trade_validation_success(client):
    nexus_bridge.mt5.symbol_info.return_value = MagicMock(visible=True)
    nexus_bridge.mt5.symbol_info_tick.return_value = MagicMock(ask=1.1000)
    nexus_bridge.mt5.symbol_info_tick.return_value = MagicMock(ask=1.1000)
    mock_result = MagicMock(retcode=nexus_bridge.mt5.TRADE_RETCODE_DONE)
    mock_result.order = 12345
    nexus_bridge.mt5.order_send.return_value = mock_result
    
    response = client.post('/trade', 
        json={
            "symbol": "EURUSD",
            "type": "BUY",
            "lots": 0.1,
            "sl": 1.0900,
            "tp": 1.1100
        },
        headers={'Authorization': 'Basic YWRtaW46c2VjdXJlcGFzc3dvcmQ='} # admin:securepassword
    )
    assert response.status_code == 200

def test_trade_validation_fail_lots(client):
    response = client.post('/trade', 
        json={
            "symbol": "EURUSD",
            "type": "BUY",
            "lots": -0.1, # Invalid
            "sl": 1.0900,
            "tp": 1.1100
        },
        headers={'Authorization': 'Basic YWRtaW46c2VjdXJlcGFzc3dvcmQ='}
    )
    assert response.status_code == 400
    assert "Validation Error" in response.json['error']

def test_ai_analysis_validation_fail_timeframe(client):
    response = client.post('/ai/analyze', 
        json={
            "symbol": "EURUSD",
            "timeframe": "INVALID" 
        },
        headers={'Authorization': 'Basic YWRtaW46c2VjdXJlcGFzc3dvcmQ='}
    )
    assert response.status_code == 400
