from flask import Flask, jsonify, request
import re

app = Flask(__name__)

# ✅ Mock Database for All Merchants
mock_db = {
    'dominos': {
        '+910123456789': {'points': 500},
        '+919876543210': {'points': 300},
        '+911234567890': {'points': 200},
        '+919112233445': {'points': 700},
        '+918765432109': {'points': 100},
    },
    'starbucks': {
        '+910123456789': {'points': 400},
        '+919876543210': {'points': 350},
        '+911234567890': {'points': 250},
        '+919112233445': {'points': 500},
        '+918765432109': {'points': 150},
    },
    'amazon': {
        '+910123456789': {'points': 600},
        '+919876543210': {'points': 450},
        '+911234567890': {'points': 300},
        '+919112233445': {'points': 900},
        '+918765432109': {'points': 50},
    },
    'flipkart': {
        '+910123456789': {'points': 550},
        '+919876543210': {'points': 400},
        '+911234567890': {'points': 320},
        '+919112233445': {'points': 800},
        '+918765432109': {'points': 200},
    }
}

# ✅ Standardize Phone Number Format
def format_phone(phone):
    """Ensures phone numbers are stored in a consistent format."""
    phone = phone.replace(" ", "").strip()
    if not phone.startswith("+91"):
        phone = "+91" + phone[-10:]  # Ensure it starts with +91
    return phone

# ✅ Phone Number Validation
def is_valid_phone(phone):
    return re.match(r'^\+?\d{10,15}$', phone) is not None

# ✅ Get Points for Any Merchant
@app.route('/api/<merchant>/rewards/<phone>', methods=['GET'])
@app.route('/api/<merchant>/rewards/rewards/<phone>', methods=['GET'])
def get_points(merchant, phone):
    phone = format_phone(phone)  # ✅ Standardize before lookup

    if merchant not in mock_db:
        return jsonify({'error': 'Merchant not found'}), 404
    if not is_valid_phone(phone):
        return jsonify({'error': 'Invalid phone number'}), 400

    points = mock_db[merchant].get(phone, {}).get('points', 0)
    print(f"✅ Fetching {merchant.capitalize()} Points for {phone}: {points}")
    return jsonify({'points': points})

# ✅ Update Points for Any Merchant
@app.route('/api/<merchant>/rewards/update', methods=['POST'])
@app.route('/api/<merchant>/rewards/rewards/update', methods=['POST'])
def update_points(merchant):
    if merchant not in mock_db:
        return jsonify({'error': 'Merchant not found'}), 404

    data = request.get_json()
    
    # ✅ Debugging: Print received data
    print(f"🔍 Received data for {merchant}: {data}")

    if not data:
        return jsonify({'error': 'Missing JSON data'}), 400

    phone = data.get("user_phone")
    points_change = data.get("points_change")

    if not phone or not is_valid_phone(phone):
        return jsonify({'error': 'Invalid phone number'}), 400
    if points_change is None or not isinstance(points_change, int):
        return jsonify({'error': 'Invalid or missing points_change'}), 400

    phone = format_phone(phone)

    if phone in mock_db[merchant]:
        mock_db[merchant][phone]['points'] += points_change
    else:
        mock_db[merchant][phone] = {'points': points_change}

    print(f"✅ Updated {merchant.capitalize()} Points for {phone}: {mock_db[merchant][phone]['points']}")
    return jsonify({'success': True, 'new_points': mock_db[merchant][phone]['points']})

# ✅ Reset Points (For Debugging)
@app.route('/api/<merchant>/rewards/reset', methods=['POST'])
@app.route('/api/<merchant>/rewards/rewards/reset', methods=['POST'])
def reset_points(merchant):
    """Resets a user's points for testing."""
    if merchant not in mock_db:
        return jsonify({'error': 'Merchant not found'}), 404

    data = request.get_json()
    phone = data.get("user_phone")

    if not phone or not is_valid_phone(phone):
        return jsonify({'error': 'Invalid phone number'}), 400

    phone = format_phone(phone)

    if phone in mock_db[merchant]:
        mock_db[merchant][phone]['points'] = 0  # ✅ Reset to 0
    else:
        mock_db[merchant][phone] = {'points': 0}

    print(f"✅ Reset {merchant.capitalize()} Points for {phone}")
    return jsonify({'success': True, 'new_points': 0})

# ✅ Check API Status
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'API is running'}), 200

# ✅ Start the Flask App
if __name__ == '__main__':
    print("🚀 API is starting on http://127.0.0.1:5001 ...")
    app.run(debug=True, port=5001)
