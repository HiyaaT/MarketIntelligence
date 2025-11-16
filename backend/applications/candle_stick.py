import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_restful import Resource, Api 
def generate_mock_candlestick_data(start_price=100.0, days=7):
    """Generates mock OHL-C data suitable for chartjs-chart-financial."""
    data = []
    
    # Calculate start date
    current_date = datetime.now()
    # Ensure we get exactly 'days' worth of dates ending today
    dates = [(current_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)][::-1]
    
    current_close = start_price
    
    for date_str in dates:
        # Simulate market movement
        open_price = round(current_close + (random.random() * 2 - 1) * 0.5, 2)
        
        # Determine movement range
        change = (random.random() * 5) + 1 # Max 5% movement
        
        # Calculate high and low
        high_price = round(max(open_price, current_close) + change * random.random(), 2)
        low_price = round(min(open_price, current_close) - change * random.random(), 2)
        
        # Calculate new close (must be between low and high)
        if open_price > current_close:
            # Bullish day
            close_price = round(random.uniform(open_price, high_price) * 0.9 + random.uniform(low_price, open_price) * 0.1, 2)
        else:
            # Bearish day
            close_price = round(random.uniform(low_price, open_price) * 0.9 + random.uniform(open_price, high_price) * 0.1, 2)
        
        # Ensure final close is within H/L boundary
        close_price = min(max(close_price, low_price), high_price)
        
        # Store OHL-C data
        data.append({
            'x': date_str,
            'o': open_price,
            'h': high_price,
            'l': low_price,
            'c': close_price
        })
        
        current_close = close_price # Next day's price is based on this close
        
    return data

# --- RESOURCE CLASS FORMAT ---
class CandlestickResource(Resource):
    """
    Defines the resource for the /api/v1/chart/candlestick endpoint.
    This class is intended to be added to a Flask-RESTful API instance elsewhere.
    """
    def get(self):
        """API endpoint to return mock candlestick data for a GET request."""
        ticker = request.args.get('stock', 'DEFAULT').upper()
        
        # Call the generator with 7 days specified
        mock_data = generate_mock_candlestick_data(start_price=100.0, days=7)
        
        # Flask-RESTful handles JSON serialization via jsonify
        return jsonify({
            'ticker': ticker,
            'title': f'{ticker} Candlestick Chart (7 Days)',
            'data': mock_data
        })

