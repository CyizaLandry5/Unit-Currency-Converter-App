from flask import Flask, jsonify, request
from flask_cors import CORS
from currency_converter import CurrencyConverter
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize converter
API_KEY = os.environ.get('API KEY HANO-for security reasons wont post them here')
converter = CurrencyConverter(api_key=API_KEY)

@app.route('/')
def index():
    return jsonify({
        "message": "Currency Converter API",
        "endpoints": {
            "/convert": "POST - Convert currencies",
            "/currencies": "GET - List supported currencies",
            "/history": "GET - Get conversion history",
            "/rate/<from_curr>/<to_curr>": "GET - Get exchange rate"
        }
    })

@app.route('/convert', methods=['POST'])
def convert_currency():
    """Convert currency API endpoint."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    amount = data.get('amount')
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    if not all([amount, from_currency, to_currency]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        amount = float(amount)
        result = converter.convert(amount, from_currency, to_currency)
        
        if result is None:
            return jsonify({"error": "Conversion failed"}), 400
        
        return jsonify({
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "result": result,
            "rate": converter.get_exchange_rate(from_currency, to_currency)
        })
    
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/currencies', methods=['GET'])
def get_currencies():
    """Get list of supported currencies."""
    return jsonify({
        "currencies": converter.get_supported_currencies(),
        "count": len(converter.get_supported_currencies())
    })

@app.route('/history', methods=['GET'])
def get_history():
    """Get conversion history."""
    limit = request.args.get('limit', default=10, type=int)
    history = converter.get_conversion_history(limit=limit)
    
    history_list = []
    for record in history:
        amount, from_curr, to_curr, result, date = record
        history_list.append({
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result,
            "date": date
        })
    
    return jsonify({"history": history_list, "count": len(history_list)})

@app.route('/rate/<from_currency>/<to_currency>', methods=['GET'])
def get_rate(from_currency, to_currency):
    """Get exchange rate between two currencies."""
    rate = converter.get_exchange_rate(from_currency, to_currency)
    
    if rate is None:
        return jsonify({"error": "Rate not available"}), 404
    
    return jsonify({
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate
    })

@app.route('/swap', methods=['POST'])
def swap_currencies():
    """Swap currencies in a conversion."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    amount = data.get('amount')
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    if not all([amount, from_currency, to_currency]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        amount = float(amount)
        result = converter.convert(amount, to_currency, from_currency)
        
        if result is None:
            return jsonify({"error": "Conversion failed"}), 400
        
        return jsonify({
            "original": {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency
            },
            "swapped": {
                "amount": amount,
                "from_currency": to_currency,
                "to_currency": from_currency,
                "result": result
            }
        })
    
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)