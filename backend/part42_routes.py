"""Drop-in Part 4.2 routes for the existing ATLAS FastAPI app."""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from backend.database import DB_PATH
from backend.part42_engine import run_backtest, saved_candles, sample_candles

router = APIRouter()

@router.get('/strategy')
def strategy_dashboard():
    return FileResponse(Path(__file__).resolve().parent.parent / 'frontend' / 'strategy.html')

@router.get('/api/part42')
def strategy_results(data: str = Query(default='sample', pattern='^(sample|saved)$'),
                     short: int = Query(default=5, ge=2, le=100),
                     long: int = Query(default=20, ge=3, le=200)):
    if short >= long:
        raise HTTPException(400, 'Short SMA must be shorter than long SMA')
    candles = sample_candles() if data == 'sample' else saved_candles(DB_PATH)
    results = run_backtest(candles, short=short, long=long)
    results['data_source'] = ('SYNTHETIC DEMO — NOT REAL MARKET DATA' if data == 'sample'
                              else 'BTC-USD saved Yahoo Finance observations (received by bar close)')
    results['data_mode'] = data
    results['sufficient_data'] = len(candles) >= long + 2
    results['warning'] = ('Synthetic prices demonstrate system mechanics; do not present as investment performance.'
                          if data == 'sample' else
                          'Historical observations may be sparse. A backtest with few bars or no trades is inconclusive.')
    return results
