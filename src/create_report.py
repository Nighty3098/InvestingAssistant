import pandas as pd
import yfinance as yf

from pathlib import Path
import joblib
import os

class AdvicePredictor:
    def analyze_fundamentals(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            pe_ratio = info.get("trailingPE", 0)
            roe = info.get("returnOnEquity", 0)
            debt_to_equity = info.get("debtToEquity", 0)
            revenue_growth = info.get("revenueGrowth", 0)
            beta = info.get("beta", 0)
            
            audit_risk = info.get("auditRisk", 0)
            board_risk = info.get("boardRisk", 0)
            compensation_risk = info.get("compensationRisk", 0)
            shareholder_risk = info.get("shareHolderRightsRisk", 0)
            overall_risk = info.get("overallRisk", 0)

            score = 0
            if pe_ratio and pe_ratio < 25: score += 2
            if roe and roe > 0.15: score += 2
            if debt_to_equity and debt_to_equity < 1: score += 2
            if revenue_growth and revenue_growth > 0.1: score += 2
            if beta and 0.5 <= beta <= 1.5: score += 2

            risk_penalty = 0
            if audit_risk and audit_risk > 5: risk_penalty += 1
            if board_risk and board_risk > 5: risk_penalty += 1
            if compensation_risk and compensation_risk > 5: risk_penalty += 1
            if shareholder_risk and shareholder_risk > 5: risk_penalty += 1
            if overall_risk and overall_risk > 5: risk_penalty += 2

            final_score = max(0, score - risk_penalty)
            return final_score, {
                'audit_risk': audit_risk,
                'board_risk': board_risk,
                'compensation_risk': compensation_risk,
                'shareholder_risk': shareholder_risk,
                'overall_risk': overall_risk
            }
        except Exception as e:
            print(f"Error analyzing fundamentals: {e}")
            return 0, {}

    def analyze(self, ticker, forecast_growth=0):
        try:
            data = yf.download(ticker, period="1y")
            if data.empty:
                return f"Data not found for {ticker}"

            fundamental_score, risk_metrics = self.analyze_fundamentals(ticker)
            
            risk_assessment = ""
            if risk_metrics:
                risk_assessment = (
                    f"\n⚠️ **Risk Assessment** (0-10 scale):\n"
                    f"🔍 Audit Risk: {risk_metrics['audit_risk']}/10\n"
                    f"👥 Board Risk: {risk_metrics['board_risk']}/10\n"
                    f"💰 Compensation Risk: {risk_metrics['compensation_risk']}/10\n"
                    f"👨‍⚖️ Shareholder Rights Risk: {risk_metrics['shareholder_risk']}/10\n"
                    f"⚠️ Overall Risk: {risk_metrics['overall_risk']}/10\n"
                )

            message = (
                f"🔍 **Analysis for {ticker}**\n"
                f"────────────────────────────\n"
                f"📊 Fundamental rating: {fundamental_score}/10\n"
                f"{risk_assessment}\n\n"
            )

            if fundamental_score >= 8:
                message += (
                    "✅ **STRONG BUY**\n"
                    "- Excellent fundamentals\n"
                    "- Low risk profile\n"
                    "- High growth potential"
                )
            elif fundamental_score >= 6:
                message += (
                    "🟢 **BUY**\n"
                    "- Good fundamentals\n"
                    "- Moderate risk\n"
                    "- Solid growth prospects"
                )
            elif fundamental_score >= 4:
                message += (
                    "🟡 **HOLD**\n"
                    "- Average fundamentals\n"
                    "- Elevated risks\n"
                    "- Needs monitoring"
                )
            else:
                message += (
                    "🔴 **SELL/AVOID**\n"
                    "- Weak fundamentals\n"
                    "- High risk profile\n"
                    "- Limited upside potential"
                )

            if risk_metrics.get('overall_risk', 0) >= 7:
                message += "\n\n🚨 **WARNING**: High overall risk detected!"

            if forecast_growth > 30 and fundamental_score < 4:
                message += (
                    "\n\n⚠️ **Signals Conflict**: Technical growth {forecast_growth:.0f}%"
                    "inconsistent with fundamental risks.\n"
                    "Recommended: Wait for confirmation of improved financials."                )

            return message

        except Exception as e:
            print(f"Error in analyze: {str(e)}")
            return "N/A"

class ReportTable:
    def __init__(self, ticker) -> None:
        self.report_path = f"client_data/{ticker}_report.xlsx"
    
    def download_data(self, ticker):
        ticker = yf.Ticker(ticker)
        ticker_info = ticker.info
        return ticker_info
    
    def save_report(self, data):
        df = pd.DataFrame([data])

        with pd.ExcelWriter(self.report_path) as writer:
            df.to_excel(writer, sheet_name='REPORT', index=False)

        return self.report_path
