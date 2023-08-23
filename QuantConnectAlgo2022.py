# Algorithm coded in Python on the QuantConnect Platform
# region imports
from AlgorithmImports import *


# endregion
class CasualSkyBluePigeon(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)  # Set Start Date
        # self.SetEndDate(2022,1,1)

        self.SetCash(10000000)  # Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.SetBenchmark(self.spy)

        self.portfolio = ["AVX", "RYDAF", "COP", "EQNR", "KMI", "DVN", "TRMD", "XLE", "PBF", "MGYOY", "DQ", "CWEN",
                          "EE", "ENPH", "EVA", "ORA"]

        # take each ticker in the portfolio and make a map of the form
        # self.equities["AVX"].macd or self.equities["AVX"].equity
        self.equities = {}
        for ticker in self.portfolio:
            equity = Object()
            equity.symbol = self.AddEquity(ticker, Resolution.Hour).Symbol
            # define our daily macd(12,26) with a 9 day signal
            equity.macd = self.MACD(equity.symbol, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)
            # ADX FILTER
            equity.adx = self.ADX(equity.symbol, 14, Resolution.Hour)
            # vwap
            equity.vwap = self.VWAP(equity.symbol)

            self.equities[ticker] = equity

        # self.PlotIndicator("MACD/Signal", True, self.macd, self.macd.Signal)
        # self.PlotIndicator("Fast/Slow", self.macd.Fast, self.macd.Slow)
        # self.PlotIndicator("ADX", self.adx)
        # self.PlotIndicator("VWAP", self.vwap)

    def OnData(self, data: Slice):
        for ticker, equity in self.equities.items():

            # wait for our macd to fully initialize
            if not equity.macd.IsReady:
                self.Debug("Macd Not Ready")
                continue

            if not data.ContainsKey(equity.symbol) or data[equity.symbol] is None:
                continue

            price = data.Bars[equity.symbol].Value
            holdings = self.Portfolio[equity.symbol].Quantity
            currentMACD = (
                                      equity.macd.Current.Value - equity.macd.Signal.Current.Value) / equity.macd.Fast.Current.Value

            if holdings <= 0 and currentMACD > 0 and equity.adx.Current.Value > 30 and price < equity.vwap.Current.Value:  # ready to buy
                self.SetHoldings(equity.symbol, 1.0 / len(self.portfolio))
                self.Log(f"Buying {ticker}")
            elif holdings >= 0 and currentMACD < 0 and equity.adx.Current.Value > 50 and price > equity.vwap.Current.Value:  # ready to sell
                self.Liquidate(equity.symbol)
                self.Log(f"Selling {ticker}")

    def OnEndOfAlgorithm(self):
        self.Liquidate()
        self.Log(f"Selling everything (End of Algorithm)")
