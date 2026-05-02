# 💎 WealthFlow Pro
**Smart Personal Finance OS | Mobile-First | Premium Aesthetics**

WealthFlow Pro is a state-of-the-art personal finance management system designed for the modern user. It combines powerful financial tracking with a premium, glassmorphism-inspired interface that works seamlessly on both desktop and mobile devices.

## 🚀 Features

- **Command Center**: Real-time dashboard with Net Worth tracking, Monthly Burn metrics, and Cash Flow pulse.
- **EMI & Loan Tracker**: Comprehensive loan management for both loans given and taken. Track remaining installments (e.g., `3/24 Remaining`) and view upcoming due dates.
- **Credit Card Suite**: Advanced card management including:
    - **Utilization Tracking**: Visual gauges for card limits and outstanding balances.
    - **EMI Focus Mode**: Option to unlink standard transactions for a specialized EMI-only view.
    - **Balance Sync**: One-click synchronization to ensure your outstanding amount matches your transaction history.
- **Smart Alerts**: An actionable notification system for:
    - **Subscription Renewals**: Track upcoming renewals with a monthly "Done" acknowledgment system.
    - **Credit Card Bills & EMIs**: Direct payment tracking from the dashboard.
    - **Loan Dues**: Alerts for overdue or upcoming payments.
- **Wealth Portfolio**: Track your assets (Stocks, Crypto, Gold, Mutual Funds, etc.) with a dedicated editing suite.
- **Piggy Bank**: Goal-based savings tracker with custom emoji icons and progress bars.
- **Recurring Bills**: Advanced subscription management with support for Monthly, Quarterly, and Yearly cycles.
- **Smart Budgets**: Category-based spending guardrails with visual alerts and burn-rate gauges.
- **Multi-Currency Support**: Switch between INR, USD, EUR, and GBP instantly across the entire app.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) (Python)
- **Database**: [Turso](https://turso.tech/) (LibSQL / Edge Database)
- **Visuals**: [Plotly](https://plotly.com/) for interactive financial charts
- **Styling**: Custom Premium Glassmorphism CSS with Outfit Google Font

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ganeshnarapareddy/WealthFlow.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Turso credentials in `.streamlit/secrets.toml`:
   ```toml
   TURSO_URL = "your-turso-url"
   TURSO_TOKEN = "your-turso-auth-token"
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

---
*Built with ❤️ by Ganesh Narapareddy*