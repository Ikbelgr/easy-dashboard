# Easy Dashboard

A comprehensive Streamlit dashboard for analyzing transaction data, customer cohorts, and business performance metrics.

## 🚀 Features

- **Key Performance Indicators (KPIs)** - Real-time metrics for transactions, customers, and financial data
- **Monthly Summary** - Transaction analysis by channel and status
- **Customer Analytics** - Unique and new customer tracking
- **Cohort Analysis** - Customer retention and behavior analysis
- **Geographic Breakdown** - Analysis by country, city, and governorate
- **RFM Segmentation** - Customer value and behavior segmentation
- **Promo Code Analysis** - Marketing campaign effectiveness
- **Month Comparison** - Period-over-period analysis

## 📊 Dashboard Sections

1. **Monthly Summary** - Transaction trends and channel analysis
2. **Customers** - Customer behavior and growth metrics
3. **Cohort Analysis** - Customer retention patterns
4. **Breakdowns** - Geographic and categorical analysis
5. **Cities** - City-specific transaction analysis
6. **Promo Codes** - Marketing campaign performance
7. **RFM Segmentation** - Customer value analysis
8. **Month Comparison** - Period comparison tools

## 📁 Project Structure

```
cohort_dashboard/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .streamlit/           # Streamlit configuration
│   └── config.toml      # Theme and server settings
└── src/                  # Source code modules
    ├── __init__.py
    ├── cohort.py         # Cohort analysis functions
    ├── data_loader.py    # Data loading and preprocessing
    ├── plots.py          # Plotting functions
    ├── summary.py        # Summary statistics
    └── utils.py          # Utility functions
```

## 🔧 Configuration

The dashboard supports:
- **Date Range Filtering** - Select custom date ranges
- **Country Filtering** - Filter by country
- **CSV File Upload** - Upload your transaction data
- **Real-time Updates** - KPIs update based on selected filters

## 📈 Data Requirements

Your CSV file should include these columns:
- `customer_id` or `id_client` - Unique customer identifier
- `transaction_date` or `createdAt` - Transaction timestamp
- `amountToSend` - Transaction amount
- `status` - Transaction status (complete, in progress, cancelled)
- `distributionChannel` - Transaction channel
- `country` - Country code or name
- Optional: `reason`, `network`, `gov`, `ville`, `promoCode`

## 🌐 Live Demo

Access the live dashboard: https://easy-dashboard.streamlit.app/ 

**Repository:** https://github.com/Ikbelgr/easy-dashboard

**Live Dashboard Features:**
- 📊 Real-time KPIs and analytics
- 📈 Interactive charts and visualizations
- 🔍 Advanced analytics including RFM segmentation 
