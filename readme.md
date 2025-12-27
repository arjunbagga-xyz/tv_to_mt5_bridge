TradingView → MetaTrader 5 Pro Bridge
System Manual
1. System Architecture: The “Silo” Concept

This system treats every chart in MetaTrader 5 as a separate Virtual Bank Account (Silo).

Safety: Each strategy only risks its allocated capital — your main balance is never touched.

Separation: You can run multiple strategies on the same symbol (e.g., 5 EURUSD strategies) using Magic Numbers.

2. Installation
Python Server
pip install flask
python universal_listener.py

Internet Connection
ngrok http 80


Or ngrok http 5000 if Flask selects port 5000.

Save the generated URL
Example:

https://my-url.ngrok-free.app

MetaTrader 5

Install TradingViewBridge_Final.mq5 in MetaEditor (F4)

Compile (F7)

Enable Algo Trading in the MT5 toolbar

3. End-to-End Scenarios (Setup Guide)
Scenario 1: One Alert (Simple Broadcast)

Goal:
Send a Buy signal to any EA listening to EURUSD

MT5 Setup

Chart: EURUSD

Attach EA

AllocatedCapital: 1000

Magic: 1001

TradingView Alert
{"ticker": "EURUSD", "action": "buy", "size_pct": 100}

Scenario 2: One Account, Two Symbols (Filtering)

Goal:
Trade EURUSD and GBPUSD independently on a single account

MT5 Setup

Chart 1 (EURUSD)

AllocatedCapital: 2000

Magic: 1001

Chart 2 (GBPUSD)

AllocatedCapital: 2000

Magic: 1002

TradingView Alerts
{"ticker": "EURUSD", "action": "buy", "size_pct": 100}

{"ticker": "GBPUSD", "action": "sell", "size_pct": 100}


Result:
The bridge broadcasts both alerts.
Each chart only accepts its own symbol.

Scenario 3: Two Accounts, Pyramiding & Silos

Goal:

Account 1 pyramids EURUSD

Account 2 trades BTCUSD

Complete separation

MT5 Setup — Account 1

Chart: EURUSD

AllocatedCapital: 5000

Magic: 1001

MT5 Setup — Account 2 (Different Terminal)

Chart: BTCUSD

AllocatedCapital: 1000

Magic: 2001

TradingView Setup (Pine Script Logic)

Entries

{"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Trade_A"}

{"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Trade_B"}

{"ticker": "BTCUSD", "action": "buy", "size_pct": 100, "magic": 2001}


Selective Close

{"ticker": "EURUSD", "action": "close_buy", "magic": 1001, "id": "Trade_A"}

4. Pine Script Conversion Guide (CRITICAL)

To make your TradingView strategy compatible, you must map GUI inputs to the JSON payload.

Step 1: Create Inputs in Pine

Add this at the top of your script:

// GUI Input for Bridge Risk
u_risk = input.float(5.0, title="Bridge Risk %", step=0.1)

Step 2: Define the JSON Generator
// Construct JSON strings using the Input value
string json_open =
     '{"action": "buy", "ticker": "' + syminfo.ticker +
     '", "size_pct": ' + str.tostring(u_risk) +
     ', "id": "Trade_A"}'

string json_close =
     '{"action": "close_buy", "ticker": "' + syminfo.ticker +
     '", "id": "Trade_A"}'

Step 3: Inject into Strategy Commands
if (buy_condition)
    strategy.entry("Trade_A", strategy.long, alert_message = json_open)

if (sell_condition)
    strategy.close("Trade_A", alert_message = json_close)

Step 4: Create the TradingView Alert

Click Create Alert on the strategy

Message Box

{{strategy.order.alert_message}}


Webhook URL

Your Ngrok URL
