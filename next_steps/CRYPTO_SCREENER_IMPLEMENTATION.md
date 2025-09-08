# CryptoPrism Crypto Screener - Implementation Guide

**Quick Start Guide for React + FastAPI Crypto Screener**  
**Implementation Time:** 7 weeks  
**Team Size:** 2 developers  

---

## Overview

This guide provides a practical roadmap for implementing the CryptoPrism crypto screener using React frontend and FastAPI backend, leveraging your existing 9 months of technical indicator development and database infrastructure.

## Pre-Implementation Checklist

### ✅ Assets Already Available
- [x] PostgreSQL database with 1000+ cryptocurrencies
- [x] 100+ technical indicators across momentum, oscillators, ratios
- [x] Real-time signal generation (bullish/bearish/neutral)
- [x] Database performance optimization completed
- [x] Validation and QA toolkits implemented

### 📋 New Requirements
- [ ] React 18+ development environment
- [ ] FastAPI backend infrastructure
- [ ] User authentication system
- [ ] API layer for frontend communication
- [ ] Deployment pipeline

## 7-Week Implementation Timeline

### Week 1: Backend Foundation & Database Setup

#### Day 1-2: Project Structure & Dependencies
```bash
# Create backend project
mkdir cryptoprism-screener-backend
cd cryptoprism-screener-backend

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-jose bcrypt python-multipart redis
```

#### Day 3-4: Database Models & Authentication
```python
# models/user.py - New user management tables
from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default='free')
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Day 5-7: Core API Endpoints
```python
# api/v1/screener.py - Main screening endpoint
from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])

@router.get("/")
async def screen_cryptocurrencies(
    market_cap_min: Optional[float] = Query(None),
    market_cap_max: Optional[float] = Query(None),
    price_change_24h_min: Optional[float] = Query(None),
    bullish_signals_min: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    # Integration with existing FE_DMV_ALL and crypto_listings_latest_1000 tables
    pass
```

**Week 1 Deliverables:**
- Working FastAPI backend with authentication
- Database integration with existing CryptoPrism tables
- Core screening API endpoint
- User management system

### Week 2: Advanced Backend Features

#### Day 8-10: Screening Engine Implementation
```python
# services/screener_service.py
class ScreenerService:
    async def advanced_screen(
        self,
        filters: Dict[str, Any],
        sort_config: Dict[str, str],
        user_id: Optional[UUID] = None
    ) -> List[CryptoScreenResult]:
        
        # Build dynamic query using existing technical indicator tables
        query = """
        SELECT 
            cl.slug, cl.name, cl.symbol, cl.price, cl.market_cap,
            cl.volume_24h, cl.price_change_percentage_24h,
            dmv.bullish, dmv.bearish, dmv.neutral,
            mom.m_mom_rsi_9, mom.m_mom_rsi_18,
            osc.m_osc_macd_crossover_bin,
            rat.alpha_vs_btc, rat.beta_vs_btc, rat.sharpe_ratio
        FROM crypto_listings_latest_1000 cl
        JOIN "FE_DMV_ALL" dmv ON cl.slug = dmv.slug
        LEFT JOIN "FE_MOMENTUM" mom ON cl.slug = mom.slug
        LEFT JOIN "FE_OSCILLATORS_SIGNALS" osc ON cl.slug = osc.slug  
        LEFT JOIN "FE_RATIOS_SIGNALS" rat ON cl.slug = rat.slug
        WHERE 1=1
        """
        
        # Apply dynamic filters
        # Add sorting and pagination
        # Return structured results
```

#### Day 11-14: Watchlists & Alerts
```python
# api/v1/watchlists.py
@router.post("/")
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    user = Depends(get_current_user)
):
    # Create user watchlist with coins from screener results
    pass

# Background task for alerts
from celery import Celery

@celery.task
def check_price_alerts():
    # Monitor watchlisted coins for alert conditions
    # Send notifications via email/webhook
    pass
```

**Week 2 Deliverables:**
- Advanced screening engine with all technical indicators
- Watchlist management system
- Alert system with background processing
- API documentation via Swagger

### Week 3: Frontend Foundation

#### Day 15-17: React Project Setup
```bash
# Create React application
npx create-react-app cryptoprism-screener --template typescript
cd cryptoprism-screener

# Install key dependencies
npm install @tanstack/react-query zustand react-router-dom axios
npm install @headlessui/react @heroicons/react tailwindcss
npm install recharts react-table @types/node
```

#### Day 18-21: Core Components
```tsx
// components/screener/ScreenerTable.tsx
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

interface ScreenerProps {
  filters: ScreeningFilters;
}

export const ScreenerTable: React.FC<ScreenerProps> = ({ filters }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['screener', filters],
    queryFn: () => api.screen(filters),
    refetchInterval: 30000 // Real-time updates every 30 seconds
  });

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        {/* Advanced table with sorting, filtering, virtualization */}
      </table>
    </div>
  );
};
```

**Week 3 Deliverables:**
- Working React application with TypeScript
- Main screener table with real-time data
- Filter panel for screening criteria
- Responsive design foundation

### Week 4: Advanced Frontend Features

#### Day 22-25: Interactive Charts & Visualization
```tsx
// components/charts/TechnicalChart.tsx
import { Line, Bar } from 'recharts';

export const TechnicalChart: React.FC<{ symbol: string }> = ({ symbol }) => {
  // Fetch historical data and technical indicators
  // Display candlestick charts with indicator overlays
  // Interactive tooltips and zoom functionality
};

// components/screener/FilterPanel.tsx
export const FilterPanel: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Market Cap Range */}
        <RangeSlider
          label="Market Cap"
          min={0}
          max={1000000000000}
          onChange={handleMarketCapChange}
        />
        
        {/* Technical Indicators */}
        <Select
          label="RSI (14)"
          options={[
            { value: 'oversold', label: 'Oversold (<30)' },
            { value: 'overbought', label: 'Overbought (>70)' },
          ]}
        />
        
        {/* Signal Strength */}
        <RangeSlider
          label="Bullish Signals"
          min={0}
          max={20}
          onChange={handleBullishSignalChange}
        />
      </div>
    </div>
  );
};
```

#### Day 26-28: Watchlist Management
```tsx
// pages/WatchlistsPage.tsx
export const WatchlistsPage: React.FC = () => {
  const { data: watchlists } = useQuery(['watchlists'], api.getWatchlists);
  
  return (
    <div className="space-y-6">
      <WatchlistGrid watchlists={watchlists} />
      <CreateWatchlistModal />
    </div>
  );
};
```

**Week 4 Deliverables:**
- Interactive technical charts with indicators
- Advanced filtering interface
- Watchlist management UI
- Export functionality (CSV, Excel)

### Week 5: Integration & Polish

#### Day 29-31: Real-time Updates & WebSocket
```python
# Backend WebSocket endpoint
from fastapi import WebSocket
import asyncio

@app.websocket("/ws/screener")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send real-time price and indicator updates
        await websocket.send_json({
            "type": "price_update",
            "data": get_latest_prices()
        })
        await asyncio.sleep(30)
```

```tsx
// Frontend WebSocket integration
import { useWebSocket } from 'hooks/useWebSocket';

export const ScreenerTable: React.FC = () => {
  const { lastMessage } = useWebSocket('ws://localhost:8000/ws/screener');
  
  // Update table data in real-time
  useEffect(() => {
    if (lastMessage?.data) {
      updateCryptoPrices(JSON.parse(lastMessage.data));
    }
  }, [lastMessage]);
};
```

#### Day 32-35: User Dashboard & Settings
```tsx
// pages/DashboardPage.tsx
export const DashboardPage: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Portfolio Overview */}
      <PortfolioSummaryCard />
      
      {/* Recent Alerts */}
      <AlertsCard />
      
      {/* Top Movers */}
      <TopMoversCard />
      
      {/* Custom Watchlists */}
      <WatchlistsCard />
    </div>
  );
};
```

**Week 5 Deliverables:**
- Real-time data updates via WebSocket
- User dashboard with personalized content
- Settings and preferences management
- Performance optimizations

### Week 6: Testing & Quality Assurance

#### Day 36-39: Backend Testing
```python
# tests/test_screener.py
import pytest
from fastapi.testclient import TestClient

class TestScreenerAPI:
    def test_basic_screening(self, client: TestClient):
        response = client.get("/api/v1/screener?limit=10")
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 10
    
    def test_advanced_filters(self, client: TestClient):
        response = client.get(
            "/api/v1/screener?market_cap_min=1000000000&bullish_signals_min=10"
        )
        assert response.status_code == 200
        # Verify filtering logic
```

#### Day 40-42: Frontend Testing & E2E
```tsx
// tests/screener.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ScreenerTable } from 'components/screener/ScreenerTable';

describe('ScreenerTable', () => {
  test('displays cryptocurrency data correctly', async () => {
    render(<ScreenerTable filters={{}} />);
    
    await waitFor(() => {
      expect(screen.getByText('Bitcoin')).toBeInTheDocument();
      expect(screen.getByText('Ethereum')).toBeInTheDocument();
    });
  });
});

// Cypress E2E tests
describe('Crypto Screener E2E', () => {
  it('can filter and sort cryptocurrencies', () => {
    cy.visit('/screener');
    cy.get('[data-testid="market-cap-filter"]').type('1000000000');
    cy.get('[data-testid="apply-filters"]').click();
    cy.get('[data-testid="crypto-table"]').should('contain', 'Bitcoin');
  });
});
```

**Week 6 Deliverables:**
- Comprehensive backend API tests
- Frontend unit and integration tests
- End-to-end testing with Cypress
- Performance testing and optimization

### Week 7: Production Deployment

#### Day 43-45: Docker & Infrastructure
```dockerfile
# Dockerfile.backend
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend  
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Day 46-49: CI/CD & Monitoring
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      
      - name: Run Frontend Tests  
        run: |
          cd frontend
          npm install
          npm test
          npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Cloud Run
        # Deployment scripts
```

**Week 7 Deliverables:**
- Production-ready Docker containers
- Automated CI/CD pipeline
- Cloud deployment (GCP/AWS/Azure)
- Monitoring and logging setup

## Quick Development Commands

### Backend Development
```bash
# Start development server
cd backend
uvicorn main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Generate API documentation
# Visit http://localhost:8000/docs
```

### Frontend Development  
```bash
# Start development server
cd frontend
npm start

# Run tests
npm test

# Build for production
npm run build

# Run E2E tests
npx cypress open
```

### Full Stack Development
```bash
# Start both frontend and backend
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2  
cd frontend && npm start

# Or use concurrently
npm install -g concurrently
concurrently "cd backend && uvicorn main:app --reload" "cd frontend && npm start"
```

## Integration with Existing CryptoPrism Infrastructure

### Database Queries Example
```python
# services/screener_service.py - Using existing tables
async def get_crypto_with_indicators(self, filters: ScreeningFilters):
    query = """
    SELECT 
        cl.slug,
        cl.name,
        cl.symbol,
        cl.price,
        cl.market_cap,
        cl.volume_24h,
        cl.price_change_percentage_24h,
        
        -- Existing signal aggregation
        dmv.bullish,
        dmv.bearish,  
        dmv.neutral,
        
        -- Momentum indicators  
        mom.m_mom_rsi_9,
        mom.m_mom_rsi_18,
        mom.m_mom_roc,
        mom.m_mom_williams_percent,
        
        -- Oscillator signals
        osc.m_osc_macd_crossover_bin,
        osc.m_osc_cci_bin,
        osc.m_osc_adx_bin,
        
        -- Ratio analysis
        rat.alpha_vs_btc,
        rat.beta_vs_btc,
        rat.sharpe_ratio,
        rat.sortino_ratio,
        
        -- Volume/Value indicators
        tvv.obv_signal,
        tvv.vwap_position,
        
        -- Fundamental metrics
        met.ath_distance_percent,
        met.market_cap_rank,
        met.coin_age_days
        
    FROM crypto_listings_latest_1000 cl
    LEFT JOIN "FE_DMV_ALL" dmv ON cl.slug = dmv.slug
    LEFT JOIN "FE_MOMENTUM" mom ON cl.slug = mom.slug  
    LEFT JOIN "FE_OSCILLATORS_SIGNALS" osc ON cl.slug = osc.slug
    LEFT JOIN "FE_RATIOS_SIGNALS" rat ON cl.slug = rat.slug
    LEFT JOIN "FE_TVV_SIGNALS" tvv ON cl.slug = tvv.slug
    LEFT JOIN "FE_METRICS_SIGNAL" met ON cl.slug = met.slug
    WHERE 1=1
    """
    
    # Apply dynamic filters based on user input
    # This leverages ALL your existing technical work!
```

## Success Validation Checklist

### Week 1 ✅
- [ ] FastAPI backend running on localhost:8000
- [ ] User authentication working (/docs shows protected endpoints)
- [ ] Basic screener endpoint returns crypto data
- [ ] Database integration with existing tables confirmed

### Week 2 ✅  
- [ ] Advanced filtering returns accurate results
- [ ] Watchlist creation and management functional
- [ ] API documentation complete and tested
- [ ] Background alert system processing

### Week 3 ✅
- [ ] React frontend running on localhost:3000
- [ ] Main screener table displaying data from backend
- [ ] Basic filtering interface connected to API
- [ ] Authentication flow working end-to-end

### Week 4 ✅
- [ ] Interactive charts showing technical indicators
- [ ] Advanced filter panel with all indicator options
- [ ] Watchlist management UI fully functional
- [ ] Export functionality working

### Week 5 ✅
- [ ] Real-time updates working (WebSocket or polling)
- [ ] User dashboard personalized and functional
- [ ] Performance optimizations implemented
- [ ] Mobile-responsive design completed

### Week 6 ✅
- [ ] Backend test suite with >80% coverage
- [ ] Frontend tests passing with good coverage
- [ ] E2E tests covering main user flows
- [ ] Performance benchmarks meeting targets

### Week 7 ✅
- [ ] Application containerized and deployable
- [ ] CI/CD pipeline executing successfully
- [ ] Production deployment accessible and stable
- [ ] Monitoring and alerting operational

## Budget Estimation

### Development Costs (2 developers × 7 weeks)
- **Senior Full-Stack Developer:** $8,000/week × 7 weeks = $56,000
- **Mid-Level Developer:** $6,000/week × 7 weeks = $42,000
- **Total Development:** $98,000

### Infrastructure Costs (Annual)
- **Cloud Hosting (GCP/AWS):** $2,400/year
- **Database (Managed PostgreSQL):** $1,800/year  
- **CDN & Storage:** $600/year
- **Monitoring & Logging:** $1,200/year
- **Total Infrastructure:** $6,000/year

### Additional Costs
- **Design & UX:** $8,000
- **Security Audit:** $5,000  
- **Legal & Compliance:** $3,000
- **Marketing & Launch:** $10,000

**Total Project Cost:** ~$130,000

## Next Steps

1. **Review and Approve PRD:** Stakeholder sign-off on requirements
2. **Setup Development Environment:** Local dev environment for both developers
3. **Create Project Repositories:** Separate repos for frontend/backend
4. **Week 1 Sprint Planning:** Detailed task breakdown and assignments
5. **Design System Creation:** UI/UX design system and component library

**Ready to start development? Begin with Week 1 backend foundation setup!**