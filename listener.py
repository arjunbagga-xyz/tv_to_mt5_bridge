import os
import sys
import time
import uuid
import platform
import threading
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================================================================
#  PATH CONFIGURATION (Auto-Detect)
# ==============================================================================
MANUAL_PATH = None 

def get_mt5_common_path():
    if MANUAL_PATH: return MANUAL_PATH
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        return os.path.join(os.environ['APPDATA'], "MetaQuotes", "Terminal", "Common", "Files")
    elif system == "Darwin": 
        # Mac Wine Paths
        paths = [
            os.path.join(home, "Library/PlayOnMac/wineprefix/MT5/drive_c/users/Public/Application Data/MetaQuotes/Terminal/Common/Files"),
            os.path.join(home, "Library/Application Support/CrossOver/Bottles/Metatrader/drive_c/users/crossover/AppData/Roaming/MetaQuotes/Terminal/Common/Files")
        ]
        for p in paths:
            if os.path.exists(p): return p
        return "."
    elif system == "Linux":
        # Auto-detect: Search for MetaQuotes directories in multiple Wine prefixes
        # MT5 can be installed in ~/.wine, ~/.mt5, or other custom prefixes
        possible_prefixes = [
            os.path.join(home, ".mt5"),      # Common MT5-specific prefix
            os.path.join(home, ".wine"),     # Default Wine prefix
        ]
        # Also check for any .wine* folders
        for item in os.listdir(home):
            if item.startswith(".wine") and os.path.isdir(os.path.join(home, item)):
                possible_prefixes.append(os.path.join(home, item))
        
        current_user = os.path.basename(home)
        
        for wine_prefix in possible_prefixes:
            users_dir = os.path.join(wine_prefix, "drive_c", "users")
            if not os.path.exists(users_dir):
                continue
                
            # Search through all Wine users for MetaQuotes folder
            for username in os.listdir(users_dir):
                # Skip system folders
                if username.lower() in ('public', 'default'):
                    continue
                candidate = os.path.join(users_dir, username, "AppData", "Roaming", 
                                         "MetaQuotes", "Terminal", "Common", "Files")
                if os.path.exists(os.path.dirname(candidate)):  # Check if Common folder exists
                    os.makedirs(candidate, exist_ok=True)
                    print(f" [Info] Found MT5 Common Files at: {candidate}")
                    return candidate
        
        # Fallback
        fallback = os.path.join(home, ".mt5/drive_c/users", current_user, 
                                "AppData/Roaming/MetaQuotes/Terminal/Common/Files")
        os.makedirs(fallback, exist_ok=True)
        return fallback
    return "."

MT5_COMMON_PATH = get_mt5_common_path()

# ==============================================================================
#  BACKGROUND CLEANER
# ==============================================================================
def file_cleanup_loop():
    print(f" [System] Cleaner watching: {MT5_COMMON_PATH}")
    while True:
        try:
            if os.path.exists(MT5_COMMON_PATH):
                now = time.time()
                for filename in os.listdir(MT5_COMMON_PATH):
                    if filename.startswith("signal_") and filename.endswith(".txt"):
                        filepath = os.path.join(MT5_COMMON_PATH, filename)
                        # Delete files older than 10 seconds
                        if os.path.getmtime(filepath) < now - 10:
                            try: os.remove(filepath)
                            except: pass
            time.sleep(2)
        except: time.sleep(5)

t = threading.Thread(target=file_cleanup_loop, daemon=True)
t.start()

# ==============================================================================
#  WEBHOOK LISTENER
# ==============================================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data: return jsonify({"error": "No JSON"}), 400

        print(f" [>] Received: {data}")

        # Parsing
        action = data.get('action', '').lower().strip()
        symbol = data.get('ticker', '').strip()
        
        # Sizing: Accept 'size_pct' or 'size', default 100
        size_val = float(data.get('size_pct', data.get('size', 100)))
        
        # Prices
        sl = float(data.get('sl_price', data.get('sl', 0.0)))
        tp = float(data.get('tp_price', data.get('tp', 0.0)))
        
        # Filters
        target_magic = int(data.get('magic', 0))
        
        # IDs: Sanitize to remove pipes
        trade_id = str(data.get('id', data.get('comment', ''))).replace('|', '_')

        if not action or not symbol:
            return jsonify({"error": "Invalid params"}), 400

        # Generate File
        unique_file_id = uuid.uuid4().hex[:8]
        filename = f"signal_{int(time.time())}_{unique_file_id}.txt"
        
        # Protocol: action|symbol|size|sl|tp|magic|trade_id|unique_id
        command_str = f"{action}|{symbol}|{size_val}|{sl}|{tp}|{target_magic}|{trade_id}|{unique_file_id}"

        if not os.path.exists(MT5_COMMON_PATH): os.makedirs(MT5_COMMON_PATH, exist_ok=True)
        
        filepath = os.path.join(MT5_COMMON_PATH, filename)
        with open(filepath, "w") as f:
            f.write(command_str)
        
        print(f" [OK] Broadcasted: {filename}")
        return jsonify({"status": "broadcasted", "file": filename}), 200

    except Exception as e:
        print(f" [ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("="*50)
    print(f" TRADINGVIEW BRIDGE ACTIVE")
    print(f" Signal Path: {MT5_COMMON_PATH}")
    print("="*50)
    try: app.run(host='0.0.0.0', port=80)
    except: 
        print(" [!] Port 80 busy. Using Port 5000.")
        app.run(host='0.0.0.0', port=5000)