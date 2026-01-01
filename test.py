import urllib.request
import json
import time

# CONFIG
URL = "http://localhost:5000/webhook" # Or port 5000
HEADERS = {'Content-Type': 'application/json'}

def send_alert(data, description):
    print(f"\n--- TEST: {description} ---")
    try:
        req = urllib.request.Request(URL, data=json.dumps(data).encode('utf-8'), headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            print(f"Sent: {data}")
            print(f"Response: {response.read().decode('utf-8')}")
    except Exception as e:
        print(f"FAILED. Ensure server is running on {URL}. Error: {e}")

def main():
    print("=== TRADINGVIEW BRIDGE SCENARIO TESTER ===")
    print("Ensure 'universal_listener.py' is running first!")
    
    while True:
        print("\nSELECT SCENARIO:")
        print("1. One Alert (Simple Broadcast)")
        print("2. One Account, 2 Symbols (Filter by Ticker)")
        print("3. Two Accounts, Pyramiding & Silos (Magic + IDs)")
        print("4. Risk-Based Sizing (Needs SL)")
        print("5. Exit")
        
        choice = input("Enter choice (1-5): ")
        
        if choice == '1':
            # Scenario: Broadcast buy to anyone listening to EURUSD
            send_alert({
                "ticker": "EURUSD",
                "action": "buy",
                "size_pct": 100
            }, "Broadcasting BUY EURUSD (100% Margin)")

        elif choice == '2':
            # Scenario: Send EURUSD then GBPUSD. EAs should filter.
            send_alert({
                "ticker": "EURUSD",
                "action": "buy",
                "size_pct": 50
            }, "Buy EURUSD (50%)")
            
            time.sleep(1)
            
            send_alert({
                "ticker": "GBPUSD",
                "action": "sell",
                "size_pct": 50
            }, "Sell GBPUSD (50%)")

        elif choice == '3':
            # Scenario: 
            # - Buy EURUSD on Account 1 (Magic 1001) - Trade A
            # - Buy EURUSD on Account 1 (Magic 1001) - Trade B (Pyramid)
            # - Buy BTCUSD on Account 2 (Magic 2001)
            # - Close ONLY Trade A on Account 1
            
            send_alert({
                "ticker": "EURUSD",
                "action": "buy",
                "size_pct": 20,
                "magic": 1001,
                "id": "Trade_A"
            }, "Acc 1 (1001): Buy EURUSD Trade_A")
            
            time.sleep(1)
            
            send_alert({
                "ticker": "EURUSD",
                "action": "buy",
                "size_pct": 20,
                "magic": 1001,
                "id": "Trade_B"
            }, "Acc 1 (1001): Buy EURUSD Trade_B (Pyramid)")
            
            time.sleep(1)
            
            send_alert({
                "ticker": "BTCUSD",
                "action": "buy",
                "size_pct": 100,
                "magic": 2001
            }, "Acc 2 (2001): Buy BTCUSD (Different Silo)")
            
            time.sleep(3)
            
            send_alert({
                "ticker": "EURUSD",
                "action": "close_buy",
                "magic": 1001,
                "id": "Trade_A"
            }, "Acc 1 (1001): Close ONLY Trade_A")

        elif choice == '4':
            # Scenario: Risk 2% of equity with specific SL
            send_alert({
                "ticker": "EURUSD",
                "action": "buy",
                "size_pct": 2,
                "sl_price": 1.0450,
                "tp_price": 1.0600
            }, "Buy EURUSD (Risk 2% with SL 1.0450)")

        elif choice == '5':
            break

if __name__ == "__main__":
    main()
