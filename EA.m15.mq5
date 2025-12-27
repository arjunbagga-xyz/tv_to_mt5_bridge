//+------------------------------------------------------------------+
//|                                     TradingViewBridge_Final.mq5  |
//|                                     Copyright 2025, AI Generated |
//+------------------------------------------------------------------+
#property copyright "AI Generated"
#property version   "5.20"

#include <Trade\Trade.mqh>

enum ENUM_SIZE_MODE
  {
   SIZE_MODE_MARGIN_PCT, // Use X% of Silo Equity as Margin
   SIZE_MODE_RISK_PCT    // Risk X% of Silo Equity (Requires SL)
  };

input group "Silo Configuration"
input double         InpAllocatedCapital = 1000.0;     // Virtual Bank Account ($)
input long           InpMagicNumber      = 1001;       // ID Card for this Silo

input group "Symbol Settings"
input string         InpTVSymbolName     = "";         // e.g. "BTCUSD" if chart is "BTCUSD.pro"
input int            InpSlippage         = 5;          // Max Slippage

input group "Risk Management"
input ENUM_SIZE_MODE InpSizeMode         = SIZE_MODE_MARGIN_PCT; 
input bool           InpForceMinLot      = true;       // Avoid Lot Size 0 errors

input group "System"
input bool           InpDebugMode        = true;       

CTrade         trade;
double         CurrentVirtualEquity;
string         ProcessedFiles[]; 

void ProcessSignalFile(string filename);
double CalculateLotSize(string symbol, double size_val, double sl_price);
void UpdateVirtualEquity();
void CloseTrades(string type, string specific_id);
bool IsFileProcessed(string filename);
void MarkFileProcessed(string filename);

int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   EventSetMillisecondTimer(200); 
   UpdateVirtualEquity();
   string sym = (InpTVSymbolName=="" ? Symbol() : InpTVSymbolName);
   PrintFormat(">>> Silo Ready. Magic: %d | Cap: $%.2f | Listening for: %s", InpMagicNumber, InpAllocatedCapital, sym);
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer()
  {
   string file_name;
   long search_handle = FileFindFirst("signal_*.txt", file_name, FILE_COMMON);
   if(search_handle != INVALID_HANDLE)
     {
      do
        {
         if(!IsFileProcessed(file_name))
           {
            ProcessSignalFile(file_name);
            MarkFileProcessed(file_name);
           }
        }
      while(FileFindNext(search_handle, file_name));
      FileFindClose(search_handle);
     }
  }

void ProcessSignalFile(string filename)
  {
   int handle = FileOpen(filename, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(handle == INVALID_HANDLE) return;
   string content = FileReadString(handle);
   FileClose(handle); 
   
   if(StringLen(content) < 3) return;

   // Parse: action|symbol|size|sl|tp|magic|id|uuid
   string data[];
   if(StringSplit(content, '|', data) < 2) return;
   
   string cmd = data[0];           
   string signal_symbol = data[1]; 
   double size_val = StringToDouble(data[2]); 
   double sl = (ArraySize(data) > 3) ? StringToDouble(data[3]) : 0;
   double tp = (ArraySize(data) > 4) ? StringToDouble(data[4]) : 0;
   long   signal_magic = (ArraySize(data) > 5) ? StringToInteger(data[5]) : 0;
   string signal_id = (ArraySize(data) > 6) ? data[6] : "";
   
   // Filters
   string my_listening_symbol = (InpTVSymbolName == "") ? Symbol() : InpTVSymbolName;
   if(signal_symbol != my_listening_symbol) return; 
   if(signal_magic != 0 && signal_magic != InpMagicNumber) return;

   if(InpDebugMode) Print(">>> Signal MATCH: ", content);

   // Close Logic
   if(StringFind(cmd, "close") >= 0)
     {
      CloseTrades(cmd, signal_id);
      return;
     }

   // Entry Logic
   UpdateVirtualEquity();
   if(CurrentVirtualEquity <= 0) return;

   double lots = CalculateLotSize(Symbol(), size_val, sl);
   if(lots <= 0) return;
   
   string comment = (signal_id == "") ? "TV_Silo" : signal_id;

   if(cmd == "buy") trade.Buy(lots, Symbol(), 0, sl, tp, comment);
   else if(cmd == "sell") trade.Sell(lots, Symbol(), 0, sl, tp, comment);
  }

double CalculateLotSize(string symbol, double size_val, double sl_price)
  {
   double lots = 0.0;
   double price_ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   if(InpSizeMode == SIZE_MODE_MARGIN_PCT)
     {
      double margin_money = CurrentVirtualEquity * (size_val / 100.0);
      double margin_one_lot;
      if(OrderCalcMargin(ORDER_TYPE_BUY, symbol, 1.0, price_ask, margin_one_lot) && margin_one_lot > 0)
         lots = margin_money / margin_one_lot;
     }
   else if(InpSizeMode == SIZE_MODE_RISK_PCT)
     {
      if(sl_price <= 0) return 0.0;
      double risk_money = CurrentVirtualEquity * (size_val / 100.0);
      double tick_val = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
      double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
      double distance = MathAbs(price_ask - sl_price);
      double points = distance / tick_size;
      if(points > 0 && tick_val > 0) lots = risk_money / (points * tick_val);
     }
   
   double step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double min_vol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_vol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   lots = MathFloor(lots / step) * step;
   
   if(lots < min_vol) return InpForceMinLot ? min_vol : 0.0;
   if(lots > max_vol) lots = max_vol;
   return lots;
  }

void CloseTrades(string type, string specific_id)
  {
   int total = PositionsTotal();
   for(int i = total - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0)
        {
         if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
           {
            if(PositionGetString(POSITION_SYMBOL) == Symbol())
               {
                if(specific_id != "")
                  {
                   string current_comment = PositionGetString(POSITION_COMMENT);
                   if(current_comment != specific_id) continue; 
                  }
                long pos_type = PositionGetInteger(POSITION_TYPE);
                if(type == "close_all") trade.PositionClose(ticket);
                else if(type == "close_buy" && pos_type == POSITION_TYPE_BUY) trade.PositionClose(ticket);
                else if(type == "close_sell" && pos_type == POSITION_TYPE_SELL) trade.PositionClose(ticket);
               }
           }
        }
     }
  }

bool IsFileProcessed(string filename)
  {
   int size = ArraySize(ProcessedFiles);
   for(int i=0; i<size; i++) if(ProcessedFiles[i] == filename) return true;
   return false;
  }

void MarkFileProcessed(string filename)
  {
   int size = ArraySize(ProcessedFiles);
   ArrayResize(ProcessedFiles, size + 1);
   ProcessedFiles[size] = filename;
   if(size > 50) ArrayRemove(ProcessedFiles, 0, 10);
  }

void UpdateVirtualEquity()
  {
   double profit = 0.0;
   HistorySelect(0, TimeCurrent());
   int total = HistoryDealsTotal(); 
   for(int i=0; i<total; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber)
         profit += HistoryDealGetDouble(ticket, DEAL_PROFIT) + 
                   HistoryDealGetDouble(ticket, DEAL_SWAP) + 
                   HistoryDealGetDouble(ticket, DEAL_COMMISSION);
     }
   CurrentVirtualEquity = InpAllocatedCapital + profit;
   if(CurrentVirtualEquity < 0) CurrentVirtualEquity = 0;
  }