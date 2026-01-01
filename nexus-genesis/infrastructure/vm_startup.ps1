# NEXUS VM Startup Script
# ========================
#
# This script runs on Google Cloud VM startup.
# Ensures MetaTrader and bridge are always running.
#
# VM: Windows Server with MT5 installed
# Auto-start: Yes
# Recovery: Auto-restart on failure

# ============================================================================
# CONFIGURATION
# ============================================================================

$NEXUS_HOME = "C:\NEXUS"
$MT5_PATH = "C:\Program Files\MetaTrader 5\terminal64.exe"
$BRIDGE_PORT = 5000
$LOG_FILE = "$NEXUS_HOME\logs\startup.log"

# ============================================================================
# LOGGING
# ============================================================================

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $LOG_FILE -Value $logEntry
    Write-Host $logEntry
}

# Create directories
New-Item -ItemType Directory -Force -Path "$NEXUS_HOME\logs" | Out-Null

Write-Log "NEXUS VM STARTUP INITIATED"

# ============================================================================
# START METATRADER 5
# ============================================================================

function Start-MetaTrader {
    Write-Log "Starting MetaTrader 5..."
    
    $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
    
    if ($mt5Process) {
        Write-Log "MetaTrader 5 already running (PID: $($mt5Process.Id))"
    } else {
        if (Test-Path $MT5_PATH) {
            Start-Process -FilePath $MT5_PATH -ArgumentList "/portable"
            Start-Sleep -Seconds 10
            
            $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
            if ($mt5Process) {
                Write-Log "MetaTrader 5 started successfully (PID: $($mt5Process.Id))"
            } else {
                Write-Log "ERROR: Failed to start MetaTrader 5"
            }
        } else {
            Write-Log "ERROR: MetaTrader 5 not found at $MT5_PATH"
        }
    }
}

# ============================================================================
# START BRIDGE SERVICE
# ============================================================================

function Start-Bridge {
    Write-Log "Starting NEXUS Bridge Service..."
    
    $bridgePath = "$NEXUS_HOME\bridge\nexus_mt_bridge.py"
    
    if (Test-Path $bridgePath) {
        # Check if already running
        $existingBridge = Get-NetTCPConnection -LocalPort $BRIDGE_PORT -ErrorAction SilentlyContinue
        
        if ($existingBridge) {
            Write-Log "Bridge already running on port $BRIDGE_PORT"
        } else {
            # Start bridge in background
            $job = Start-Job -ScriptBlock {
                param($path, $home)
                Set-Location $home
                python $path
            } -ArgumentList $bridgePath, "$NEXUS_HOME\bridge"
            
            Start-Sleep -Seconds 5
            
            # Verify
            $existingBridge = Get-NetTCPConnection -LocalPort $BRIDGE_PORT -ErrorAction SilentlyContinue
            if ($existingBridge) {
                Write-Log "Bridge started successfully on port $BRIDGE_PORT"
            } else {
                Write-Log "WARNING: Bridge may not have started correctly"
            }
        }
    } else {
        Write-Log "Bridge script not found, creating..."
        Create-BridgeScript
    }
}

# ============================================================================
# CREATE BRIDGE SCRIPT
# ============================================================================

function Create-BridgeScript {
    $bridgeDir = "$NEXUS_HOME\bridge"
    New-Item -ItemType Directory -Force -Path $bridgeDir | Out-Null
    
    $bridgeScript = @'
"""
NEXUS MT Bridge - Local REST API
================================

Runs alongside MetaTrader 5 on the VM.
Receives signed trade instructions from NEXUS backend.
"""

from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import hmac
import hashlib
import os

app = Flask(__name__)

# Initialize MT5
if not mt5.initialize():
    print(f"MT5 initialization failed: {mt5.last_error()}")
else:
    print(f"MT5 initialized: {mt5.terminal_info()}")

SIGNING_KEY = os.getenv("MT_BRIDGE_SIGNING_KEY", "nexus-bridge-key").encode()

def verify_signature(data, signature):
    """Verify request signature."""
    msg = f"{data.get('id')}:{data.get('symbol')}:{data.get('type')}:{data.get('volume')}:{data.get('timestamp')}"
    expected = hmac.new(SIGNING_KEY, msg.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/health', methods=['GET'])
def health():
    connected = mt5.account_info() is not None
    return jsonify({
        "status": "online",
        "mt5_connected": connected,
        "timestamp": str(datetime.now())
    })

@app.route('/account', methods=['GET'])
def account():
    info = mt5.account_info()
    if info:
        return jsonify({
            "login": info.login,
            "server": info.server,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "leverage": info.leverage,
            "currency": info.currency,
            "connected": True,
            "trade_allowed": info.trade_allowed
        })
    return jsonify({"error": "Not connected"}), 500

@app.route('/positions', methods=['GET'])
def positions():
    positions = mt5.positions_get()
    result = []
    for p in positions or []:
        result.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "open_price": p.price_open,
            "current_price": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit,
            "swap": p.swap,
            "open_time": str(datetime.fromtimestamp(p.time)),
            "magic": p.magic
        })
    return jsonify({"positions": result})

@app.route('/quotes', methods=['GET'])
def quotes():
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "XAUUSD"]
    quotes_data = []
    for sym in symbols:
        tick = mt5.symbol_info_tick(sym)
        if tick:
            quotes_data.append({
                "symbol": sym,
                "bid": tick.bid,
                "ask": tick.ask,
                "volume": tick.volume
            })
    return jsonify({"quotes": quotes_data})

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    
    # Verify signature
    if not verify_signature(data, data.get('signature', '')):
        return jsonify({"success": False, "error": "Invalid signature"}), 403
    
    symbol = data.get('symbol')
    order_type = mt5.ORDER_TYPE_BUY if data.get('type') == 'BUY' else mt5.ORDER_TYPE_SELL
    volume = float(data.get('volume', 0.01))
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return jsonify({"success": False, "error": f"Symbol {symbol} not found"})
    
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    
    request_order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": data.get('sl', 0.0),
        "tp": data.get('tp', 0.0),
        "deviation": 20,
        "magic": data.get('magic', 777777),
        "comment": data.get('comment', 'NEXUS'),
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request_order)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return jsonify({
            "success": True,
            "ticket": result.order,
            "price": result.price,
            "volume": result.volume
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Order failed: {result.retcode} - {result.comment}"
        })

@app.route('/close', methods=['POST'])
def close():
    data = request.json
    ticket = data.get('ticket')
    
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return jsonify({"success": False, "error": "Position not found"})
    
    pos = position[0]
    order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(pos.symbol)
    price = tick.bid if pos.type == 0 else tick.ask
    
    request_order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": pos.magic,
        "comment": "NEXUS_CLOSE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request_order)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return jsonify({"success": True, "ticket": ticket})
    else:
        return jsonify({"success": False, "error": str(result.retcode)})

if __name__ == '__main__':
    from datetime import datetime
    app.run(host='0.0.0.0', port=5000, threaded=True)
'@

    Set-Content -Path "$bridgeDir\nexus_mt_bridge.py" -Value $bridgeScript
    Write-Log "Bridge script created at $bridgeDir\nexus_mt_bridge.py"
    
    # Create requirements
    $requirements = @"
flask
MetaTrader5
"@
    Set-Content -Path "$bridgeDir\requirements.txt" -Value $requirements
}

# ============================================================================
# HEALTH MONITOR
# ============================================================================

function Start-HealthMonitor {
    Write-Log "Starting health monitor..."
    
    # Create scheduled task for continuous monitoring
    $action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-File $NEXUS_HOME\scripts\health_check.ps1"
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd
    
    Register-ScheduledTask -TaskName "NEXUS_HealthMonitor" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    
    Write-Log "Health monitor scheduled"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

try {
    Start-MetaTrader
    Start-Bridge
    Start-HealthMonitor
    
    Write-Log "NEXUS VM STARTUP COMPLETE"
    Write-Log "System is ONLINE and awaiting commands"
    
} catch {
    Write-Log "STARTUP ERROR: $_"
}
