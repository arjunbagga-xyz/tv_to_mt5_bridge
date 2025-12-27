TradingView to MetaTrader 5 Pro Bridge - System Manual

1. System Architecture: The "Silo" Concept

This system treats every chart in MetaTrader as a separate "Virtual Bank Account" (Silo).

Safety: Strategies only risk their allocated capital, never touching your main cash balance.

Separation: You can run 5 different strategies on EURUSD on the same account using Magic Numbers.

2. Installation

Python Server:

Install: pip install flask

Run: python universal_listener.py

Internet Connection:

Run: ngrok http 80 (or 5000 if Python chose 5000).

Save the URL (e.g., https://my-url.ngrok-free.app).

MetaTrader 5:

Install TradingViewBridge_Final.mq5 in MetaEditor (F4) -> Compile (F7).

Enable Algo Trading in MT5 Toolbar.

3. End-to-End Scenarios (Setup Guide)

Scenario 1: One Alert (Simple Broadcast)

Goal: Send a Buy signal to any EA listening to EURUSD.

MT5 Setup:

Open EURUSD Chart. Attach EA.

AllocatedCapital: 1000. Magic: 1001.

TV Setup:

Alert JSON: {"ticker": "EURUSD", "action": "buy", "size_pct": 100}

Scenario 2: One Account, 2 Symbols (Filtering)

Goal: Trade EURUSD and GBPUSD independently on one account.

MT5 Setup:

Chart 1 (EURUSD): AllocatedCapital: 2000, Magic: 1001.

Chart 2 (GBPUSD): AllocatedCapital: 2000, Magic: 1002.

TV Setup:

Alert 1: {"ticker": "EURUSD", "action": "buy", "size_pct": 100}

Alert 2: {"ticker": "GBPUSD", "action": "sell", "size_pct": 100}

Result: The Bridge broadcasts both. Chart 1 only accepts EURUSD. Chart 2 only accepts GBPUSD.

Scenario 3: 2 Accounts, Pyramiding & Silos

Goal: Acc 1 pyramids EURUSD. Acc 2 trades BTCUSD. Separation is key.

MT5 Setup (Account 1):

Chart 1 (EURUSD): AllocatedCapital: 5000, Magic: 1001.

MT5 Setup (Account 2 - Different Terminal):

Chart 1 (BTCUSD): AllocatedCapital: 1000, Magic: 2001.

TV Setup (Pine Script Logic):

Entry 1 (Acc 1): {"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Trade_A"}

Entry 2 (Acc 1): {"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Trade_B"}

Entry 3 (Acc 2): {"ticker": "BTCUSD", "action": "buy", "size_pct": 100, "magic": 2001}

Close Only A: {"ticker": "EURUSD", "action": "close_buy", "magic": 1001, "id": "Trade_A"}

4. Pine Script Conversion Guide (CRITICAL)

To make your TradingView Strategy compatible, you must map your GUI settings to the JSON payload.

Step 1: Create Inputs in Pine

Add this to the top of your script so you can control Risk % from the settings menu.

// GUI Input for Bridge Risk
u_risk = input.float(5.0, title="Bridge Risk %", step=0.1)


Step 2: Define the JSON Generator

Create a variable that updates automatically.

// Construct JSON string using the Input value
string json_open = '{"action": "buy", "ticker": "' + syminfo.ticker + '", "size_pct": ' + str.tostring(u_risk) + ', "id": "Trade_A"}'

string json_close = '{"action": "close_buy", "ticker": "' + syminfo.ticker + '", "id": "Trade_A"}'


Step 3: Inject into Commands

Use alert_message in your entries and exits.

if (buy_condition)
    strategy.entry("Trade_A", strategy.long, alert_message = json_open)

if (sell_condition)
    strategy.close("Trade_A", alert_message = json_close)


Step 4: Create the Alert

Click "Create Alert" on the Strategy.

Message Box: {{strategy.order.alert_message}}

Webhook: Your Ngrok URL.

Now, when you change "Bridge Risk %" in the Strategy Settings, the JSON sent to MT5 updates automatically.
