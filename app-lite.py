from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Simplified prediction without heavy ML dependencies
def simple_heart_prediction(data):
    """Lightweight prediction algorithm matching your dataset structure"""
    risk_score = 0
    risk_factors = []
    
    # Age factor
    age = float(data.get('Age', 0))
    if age > 65:
        risk_score += 15
        risk_factors.append("Advanced age")
    elif age > 50:
        risk_score += 8
    
    # Sex factor (males generally higher risk)
    if data.get('Sex') == 'M':
        risk_score += 5
    
    # Chest pain type
    chest_pain = data.get('ChestPainType', '')
    if chest_pain == 'TA':  # Typical Angina
        risk_score += 20
        risk_factors.append("Typical angina symptoms")
    elif chest_pain == 'ATA':  # Atypical Angina
        risk_score += 10
        risk_factors.append("Atypical chest pain")
    elif chest_pain == 'ASY':  # Asymptomatic
        risk_score += 5
    
    # Blood pressure
    resting_bp = float(data.get('RestingBP', 0))
    if resting_bp > 140:
        risk_score += 15
        risk_factors.append("High blood pressure")
    elif resting_bp > 130:
        risk_score += 8
    
    # Cholesterol
    cholesterol = float(data.get('Cholesterol', 0))
    if cholesterol > 240:
        risk_score += 15
        risk_factors.append("High cholesterol")
    elif cholesterol > 200:
        risk_score += 8
    
    # Fasting blood sugar
    if float(data.get('FastingBS', 0)) == 1:
        risk_score += 10
        risk_factors.append("Elevated fasting blood sugar")
    
    # ECG abnormalities
    resting_ecg = data.get('RestingECG', '')
    if resting_ecg == 'ST':
        risk_score += 8
        risk_factors.append("ECG abnormalities")
    elif resting_ecg == 'LVH':
        risk_score += 12
        risk_factors.append("Left ventricular hypertrophy")
    
    # Maximum heart rate
    max_hr = float(data.get('MaxHR', 0))
    if max_hr < 100:
        risk_score += 12
        risk_factors.append("Low maximum heart rate")
    
    # Exercise induced angina
    if data.get('ExerciseAngina') == 'Y':
        risk_score += 15
        risk_factors.append("Exercise-induced chest pain")
    
    # ST depression
    oldpeak = float(data.get('Oldpeak', 0))
    if oldpeak > 2:
        risk_score += 15
        risk_factors.append("Significant ST depression")
    elif oldpeak > 1:
        risk_score += 8
    
    # ST slope
    st_slope = data.get('ST_Slope', '')
    if st_slope == 'Down':
        risk_score += 12
        risk_factors.append("Downsloping ST segment")
    elif st_slope == 'Flat':
        risk_score += 6
    
    return {
        'riskScore': min(risk_score, 100),
        'hasHeartDisease': risk_score > 50,
        'riskFactors': risk_factors,
        'modelUsed': False
    }

@app.route('/')
def index():
    try:
        with open('index.html', 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "index.html not found", 404

@app.route('/style.css')
def style():
    try:
        with open('style.css', 'r') as file:
            return file.read(), 200, {'Content-Type': 'text/css'}
    except FileNotFoundError:
        return "style.css not found", 404

@app.route('/script.js')
def script():
    try:
        with open('script.js', 'r') as file:
            return file.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "script.js not found", 404

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        prediction = simple_heart_prediction(data)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'riskScore': 50,
            'hasHeartDisease': False,
            'riskFactors': ['Error occurred during prediction']
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
