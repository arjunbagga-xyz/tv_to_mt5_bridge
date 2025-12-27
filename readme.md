# TradingView to MetaTrader 5 Pro Bridge - System Manual

## 1. System Architecture: The "Silo" Concept

This system treats every chart in MetaTrader as a separate **"Virtual Bank Account" (Silo)**.

-   **Virtual Equity:** The EA ignores your actual account balance. It calculates its own equity based on **Allocated Capital + Realized Profit** from its own trades.
-   **Safety:** Strategies only risk their allocated capital, never touching your main cash balance.
-   **Separation:** You can run 5 different strategies on EURUSD on the same account using unique **Magic Numbers**.

---

## 2. Installation & Setup

### A. The Python Broadcaster (Server)

1.  **Install Flask:**
    ```bash
    pip install flask
    ```
2.  **Run:**
    ```bash
    python universal_listener.py
    ```
    *Note: If Port 80 is blocked, it defaults to Port 5000.*

### B. Connect to Internet (Ngrok)

1.  **Run:**
    ```bash
    ngrok http 80
    ```
    *(or 5000)*
2.  **Copy URL:** e.g., `https://a1b2.ngrok-free.app`.

### C. MetaTrader 5 Setup (Client)

1.  **Install EA:** Copy code to **MetaEditor (F4)** -> `TradingViewBridge_Final.mq5` -> **Compile (F7)**.
2.  **Attach to Chart:** Drag EA onto a chart (e.g., EURUSD).
3.  **Configure Inputs:**
    *   `InpAllocatedCapital`: Amount of money this strategy owns (e.g., 1000).
    *   `InpMagicNumber`: Unique ID (e.g., 1001).
    *   `InpSizeMode`: Choose **Margin %** or **Risk %** (requires SL).

---

## 3. Mastering Trade IDs (Pyramiding & Management)

The `id` field in the JSON is crucial for advanced strategies. It maps to the **Order Comment** in MetaTrader.

-   **Without ID:** A `close_buy` command closes **ALL** Buy trades for that symbol/magic number.
-   **With ID:** A `close_buy` command closes **ONLY** the trade with the matching comment.

### Method A: The Placeholder Method (Easiest)

Use this if you name your trades in Pine Script (e.g., "Long_A", "Long_B").

1.  **Pine Script:** Name your entries clearly.
    ```pinescript
    strategy.entry("Trend_Trade", strategy.long)
    strategy.entry("Scalp_Trade", strategy.long)
    ```

2.  **TradingView Alert Box:** Use the `{{strategy.order.id}}` placeholder.
    **Message:**
    ```json
    {
      "ticker": "{{ticker}}",
      "action": "{{strategy.order.action}}",
      "size_pct": 100,
      "id": "{{strategy.order.id}}"
    }
    ```

    **Result:** When "Trend_Trade" fires, TV sends `id: "Trend_Trade"`. The EA opens a trade with comment "Trend_Trade". When that specific strategy closes, it sends the same ID, and the EA closes only that trade.

### Method B: The Code-Based Method (Advanced)

Use this if you need calculated IDs or want to embed the JSON inside the script.

1.  **Pine Script:** Construct the JSON string inside your code.
    ```pinescript
    // Create a dynamic ID
    string my_id = "Trade_" + str.tostring(bar_index)

    // Create JSON for Entry
    string json_entry = '{"action": "buy", "ticker": "' + syminfo.ticker + '", "size_pct": 10, "id": "' + my_id + '"}'

    // Create JSON for Exit
    string json_exit = '{"action": "close_buy", "ticker": "' + syminfo.ticker + '", "id": "' + my_id + '"}'

    // Execute
    strategy.entry(my_id, strategy.long, alert_message = json_entry)
    strategy.exit("Exit_" + my_id, my_id, stop=1.0500, alert_message = json_exit)
    ```

2.  **TradingView Alert Box:**
    **Message:** `{{strategy.order.alert_message}}`

---

## 4. Comprehensive Alert Scenarios

**Paste your Ngrok URL + `/webhook` into the Alert Webhook field.**

### Scenario 1: Simple Broadcast (One Trade per Symbol)
**Goal:** Send a Buy signal to any EA listening to EURUSD.
*   **MT5 Setup:** Chart EURUSD, Magic 1001.
*   **TV Payload:**
    ```json
    {
      "ticker": "EURUSD",
      "action": "buy",
      "size_pct": 100
    }
    ```

### Scenario 2: Targeted Account (Specific Magic Number)
**Goal:** You have two BTC charts. One is "Scalp" (Magic 2001), one is "Swing" (Magic 2002). Target ONLY the Swing account.
*   **MT5 Setup:** Chart BTCUSD, Magic 2002.
*   **TV Payload:**
    ```json
    {
      "ticker": "BTCUSD",
      "action": "buy",
      "size_pct": 50,
      "magic": 2002
    }
    ```

### Scenario 3: Risk-Based Sizing (Professional)
**Goal:** Risk exactly 1% of the Silo Capital. Requires SL.
*   **MT5 Setup:** Chart EURUSD, Magic 1001, `InpSizeMode = SIZE_MODE_RISK_PCT`.
*   **TV Payload:**
    ```json
    {
      "ticker": "EURUSD",
      "action": "buy",
      "size_pct": 1,
      "sl_price": 1.0450,
      "tp_price": 1.0600,
      "magic": 1001
    }
    ```

### Scenario 4: Strategy Splitting (Same Symbol, Different Logic)
**Goal:** Run a "Trend" strategy and a "Counter-Trend" strategy on GBPUSD simultaneously on the same account.

1.  **Trend Silo (MT5):**
    *   Chart: GBPUSD
    *   Magic: 3001
    *   Capital: $5000
2.  **Counter-Trend Silo (MT5):**
    *   Chart: GBPUSD
    *   Magic: 3002
    *   Capital: $2000
3.  **TV Payloads:**
    *   **Trend Buy:** `{"ticker": "GBPUSD", "action": "buy", "size_pct": 100, "magic": 3001}`
    *   **Counter Sell:** `{"ticker": "GBPUSD", "action": "sell", "size_pct": 100, "magic": 3002}`

**Result:** You can be Long and Short on GBPUSD at the same time (Hedging), handled by separate silos.

### Scenario 5: Advanced Pyramiding (Adding & Partial Closing)
**Goal:** Open 3 positions. Close the first one early. Let others run.

1.  **Entry 1 (Base):**
    `{"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Base"}`
2.  **Entry 2 (Add-on):**
    `{"ticker": "EURUSD", "action": "buy", "size_pct": 10, "magic": 1001, "id": "Add1"}`
3.  **Close ONLY "Base" (Take Profit):**
    `{"ticker": "EURUSD", "action": "close_buy", "magic": 1001, "id": "Base"}`

**Result:** "Base" trade closes. "Add1" trade remains open.

### Scenario 6: The "Reversal" (Flip Position)
**Goal:** You are Long. Signal says go Short. You need to close the Buy and open a Sell.

**TV Payload (Two Commands in One Logic):**
Currently, you need to send two separate webhooks or handle this in Pine Script logic.

**Pine Script Logic:**
```pinescript
if (go_short_condition)
    // Close the Long (ID: LongTrend)
    strategy.close("LongTrend", alert_message='{"action": "close_buy", "ticker": "EURUSD", "magic": 1001, "id": "LongTrend"}')
    // Open the Short (ID: ShortTrend)
    strategy.entry("ShortTrend", strategy.short, alert_message='{"action": "sell", "ticker": "EURUSD", "size_pct": 100, "magic": 1001, "id": "ShortTrend"}')
```

---

## 5. Reference Guide

### Supported Actions

| Action | Description |
| :--- | :--- |
| `buy` | Open a Buy order. |
| `sell` | Open a Sell order. |
| `close_buy` | Close Buy positions. (If `id` provided, closes ONLY matching comment). |
| `close_sell` | Close Sell positions. (If `id` provided, closes ONLY matching comment). |
| `close_all` | Close Everything for this symbol/silo. |

### JSON Field Reference

| Field | Description |
| :--- | :--- |
| `ticker` | **Required.** The symbol (e.g., "EURUSD"). |
| `action` | **Required.** See table above. |
| `size_pct` | Percentage of Silo Equity to use. |
| `magic` | (Optional) Target a specific EA Magic Number. |
| `id` | (Optional) Unique ID for the trade (becomes MT5 Comment). |
| `sl_price` | Stop Loss Price (Required for Risk Mode). |
| `tp_price` | Take Profit Price. |

---

## 6. Troubleshooting

*   **Lot Size 0 Error:**
    Your allocated capital is too small. Enable `InpForceMinLot` in EA inputs to force 0.01 lots for testing.
*   **Symbol Mismatch:**
    If TV sends "BTCUSD" but broker uses "BTCUSD.pro", set `InpTVSymbolName` to "BTCUSD" in the EA Inputs.
*   **Alerts Not Reaching MT5:**
    1.  Check if Ngrok window is open.
    2.  Check if Python script is running.
    3.  Check if `MT5_COMMON_PATH` in Python matches your MT5 "Common Data Folder".
