from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for all domains on all routes

# Load the model
MODEL_LOADED = False
model = None

def load_model_safe():
    """Safely load the model with error handling"""
    global model, MODEL_LOADED
    try:
        # Try loading joblib model
        model = joblib.load('model.joblib')
        print("✅ Model loaded successfully from model.joblib!")
        MODEL_LOADED = True
        return True
    except Exception as e:
        print(f"⚠️  Model loading failed: {e}")
        print("Using fallback prediction algorithm")
        MODEL_LOADED = False
        return False

# Attempt to load model at startup
load_model_safe()

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        with open('index.html', 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "index.html not found", 404

@app.route('/style.css')
def style():
    """Serve the CSS file"""
    try:
        with open('style.css', 'r') as file:
            return file.read(), 200, {'Content-Type': 'text/css'}
    except FileNotFoundError:
        return "style.css not found", 404

@app.route('/script.js')
def script():
    """Serve the JavaScript file"""
    try:
        with open('script.js', 'r') as file:
            return file.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "script.js not found", 404

@app.route('/predict', methods=['POST'])
def predict():
    """Handle heart disease prediction using trained model or fallback"""
    try:
        # Get data from request
        data = request.json
        
        # Feature names (matching your dataset structure)
        feature_names = [
            'Age', 'Sex', 'ChestPainType', 'RestingBP', 'Cholesterol', 
            'FastingBS', 'RestingECG', 'MaxHR', 'ExerciseAngina', 
            'Oldpeak', 'ST_Slope'
        ]
        
        # If model is loaded, use it
        if MODEL_LOADED and model is not None:
            try:
                # Prepare features for your trained model
                features = prepare_features_for_model(data, feature_names)
                X = np.array(features).reshape(1, -1)
                
                # Make prediction with your trained model
                if hasattr(model, 'predict_proba'):
                    probability = model.predict_proba(X)[0]
                    risk_score = int(probability[1] * 100)
                    has_heart_disease = probability[1] > 0.5
                else:
                    prediction = model.predict(X)[0]
                    has_heart_disease = bool(prediction)
                    risk_score = 75 if has_heart_disease else 25
                
                return jsonify({
                    'riskScore': risk_score,
                    'hasHeartDisease': has_heart_disease,
                    'riskFactors': generate_risk_factors(data),
                    'modelUsed': True,
                    'message': 'Prediction from your trained model'
                })
                
            except Exception as e:
                print(f"Model prediction error: {e}")
                # Fall through to heuristic method
        
        # Fallback to smart heuristic if model fails or isn't loaded
        result = calculate_smart_prediction(data)
        result['modelUsed'] = False
        result['message'] = 'Prediction from smart algorithm (model not available)'
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'riskScore': 50,
            'hasHeartDisease': False,
            'riskFactors': ['Error occurred during prediction'],
            'modelUsed': False
        }), 500

def prepare_features_for_model(data, feature_names):
    """Convert form data to model features with proper encoding"""
    import pandas as pd
    
    # Create a single row DataFrame with your form data
    row_data = {
        'Age': float(data.get('Age', 0)),
        'Sex': data.get('Sex', 'M'),
        'ChestPainType': data.get('ChestPainType', 'ASY'),
        'RestingBP': float(data.get('RestingBP', 0)),
        'Cholesterol': float(data.get('Cholesterol', 0)),
        'FastingBS': int(data.get('FastingBS', 0)),
        'RestingECG': data.get('RestingECG', 'Normal'),
        'MaxHR': float(data.get('MaxHR', 0)),
        'ExerciseAngina': data.get('ExerciseAngina', 'N'),
        'Oldpeak': float(data.get('Oldpeak', 0)),
        'ST_Slope': data.get('ST_Slope', 'Flat')
    }
    
    df = pd.DataFrame([row_data])
    
    # Apply the same encoding that was likely used during training
    # One-hot encode categorical variables
    df_encoded = pd.get_dummies(df, columns=['Sex', 'ChestPainType', 'RestingECG', 'ExerciseAngina', 'ST_Slope'])
    
    # Ensure we have all possible categories (in case some are missing)
    expected_columns = [
        'Age', 'RestingBP', 'Cholesterol', 'FastingBS', 'MaxHR', 'Oldpeak',
        'Sex_F', 'Sex_M',
        'ChestPainType_ASY', 'ChestPainType_ATA', 'ChestPainType_NAP', 'ChestPainType_TA',
        'RestingECG_LVH', 'RestingECG_Normal', 'RestingECG_ST',
        'ExerciseAngina_N', 'ExerciseAngina_Y',
        'ST_Slope_Down', 'ST_Slope_Flat', 'ST_Slope_Up'
    ]
    
    # Add missing columns with 0
    for col in expected_columns:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
    
    # Reorder columns to match expected order
    df_encoded = df_encoded.reindex(columns=expected_columns, fill_value=0)
    
    return df_encoded.values[0]

def calculate_smart_prediction(data):
    """Smart prediction algorithm based on medical guidelines"""
    risk_score = 0
    risk_factors = []
    
    # Age factor (major risk factor)
    age = float(data.get('Age', 0))
    if age > 65:
        risk_score += 20
        risk_factors.append("Advanced age (>65)")
    elif age > 55:
        risk_score += 12
        risk_factors.append("Older age (>55)")
    elif age > 45:
        risk_score += 6
    
    # Sex factor  
    if data.get('Sex') == 'M':
        risk_score += 8
        risk_factors.append("Male gender")
    
    # Chest pain type (very important)
    chest_pain = data.get('ChestPainType', '')
    if chest_pain == 'TA':
        risk_score += 25
        risk_factors.append("Typical angina symptoms")
    elif chest_pain == 'ATA':
        risk_score += 15
        risk_factors.append("Atypical chest pain")
    elif chest_pain == 'ASY':
        risk_score += 10
        risk_factors.append("Asymptomatic presentation")
    
    # Blood pressure
    resting_bp = float(data.get('RestingBP', 0))
    if resting_bp >= 160:
        risk_score += 18
        risk_factors.append("Very high blood pressure")
    elif resting_bp >= 140:
        risk_score += 12
        risk_factors.append("High blood pressure")
    elif resting_bp >= 130:
        risk_score += 6
        risk_factors.append("Elevated blood pressure")
    
    # Cholesterol
    cholesterol = float(data.get('Cholesterol', 0))
    if cholesterol >= 280:
        risk_score += 18
        risk_factors.append("Very high cholesterol")
    elif cholesterol >= 240:
        risk_score += 12
        risk_factors.append("High cholesterol")
    elif cholesterol >= 200:
        risk_score += 6
        risk_factors.append("Borderline high cholesterol")
    
    # Fasting blood sugar
    if float(data.get('FastingBS', 0)) == 1:
        risk_score += 12
        risk_factors.append("Elevated fasting blood sugar")
    
    # ECG abnormalities
    resting_ecg = data.get('RestingECG', '')
    if resting_ecg == 'LVH':
        risk_score += 15
        risk_factors.append("Left ventricular hypertrophy")
    elif resting_ecg == 'ST':
        risk_score += 10
        risk_factors.append("ECG abnormalities")
    
    # Maximum heart rate (lower is worse)
    max_hr = float(data.get('MaxHR', 0))
    expected_max_hr = 220 - age
    if max_hr < expected_max_hr * 0.7:
        risk_score += 15
        risk_factors.append("Poor exercise capacity")
    elif max_hr < expected_max_hr * 0.8:
        risk_score += 8
        risk_factors.append("Reduced exercise capacity")
    
    # Exercise induced angina
    if data.get('ExerciseAngina') == 'Y':
        risk_score += 20
        risk_factors.append("Exercise-induced chest pain")
    
    # ST depression (oldpeak)
    oldpeak = float(data.get('Oldpeak', 0))
    if oldpeak >= 3:
        risk_score += 20
        risk_factors.append("Severe ST depression")
    elif oldpeak >= 2:
        risk_score += 15
        risk_factors.append("Significant ST depression")
    elif oldpeak >= 1:
        risk_score += 8
        risk_factors.append("Mild ST depression")
    
    # ST slope
    st_slope = data.get('ST_Slope', '')
    if st_slope == 'Down':
        risk_score += 15
        risk_factors.append("Downsloping ST segment")
    elif st_slope == 'Flat':
        risk_score += 8
        risk_factors.append("Flat ST segment")
    
    # Cap the risk score
    risk_score = min(risk_score, 100)
    
    return {
        'riskScore': risk_score,
        'hasHeartDisease': risk_score > 60,
        'riskFactors': risk_factors
    }

def calculate_risk_heuristic(data):
    """Fallback heuristic for risk calculation"""
    risk_score = 0
    
    # Age factor
    age = float(data.get('age', 0))
    if age > 65:
        risk_score += 15
    elif age > 50:
        risk_score += 8
    
    # Sex factor (males generally higher risk)
    if float(data.get('sex', 0)) == 1:
        risk_score += 5
    
    # Chest pain type
    cp = float(data.get('cp', 0))
    if cp == 0:
        risk_score += 20
    elif cp == 1:
        risk_score += 10
    
    # Blood pressure
    trestbps = float(data.get('trestbps', 0))
    if trestbps > 140:
        risk_score += 15
    elif trestbps > 130:
        risk_score += 8
    
    # Cholesterol
    chol = float(data.get('chol', 0))
    if chol > 240:
        risk_score += 15
    elif chol > 200:
        risk_score += 8
    
    # Other factors
    if float(data.get('fbs', 0)) == 1:
        risk_score += 10
    
    if float(data.get('exang', 0)) == 1:
        risk_score += 15
    
    if float(data.get('oldpeak', 0)) > 2:
        risk_score += 15
    elif float(data.get('oldpeak', 0)) > 1:
        risk_score += 8
    
    ca = float(data.get('ca', 0))
    if ca > 0:
        risk_score += ca * 10
    
    return min(risk_score, 100)

def generate_risk_factors(data):
    """Generate list of risk factors based on input data"""
    risk_factors = []
    
    age = float(data.get('age', 0))
    if age > 65:
        risk_factors.append("Advanced age")
    elif age > 50:
        risk_factors.append("Middle age")
    
    if float(data.get('cp', 0)) == 0:
        risk_factors.append("Typical angina symptoms")
    elif float(data.get('cp', 0)) == 1:
        risk_factors.append("Atypical chest pain")
    
    if float(data.get('trestbps', 0)) > 140:
        risk_factors.append("High blood pressure")
    
    if float(data.get('chol', 0)) > 240:
        risk_factors.append("High cholesterol")
    
    if float(data.get('fbs', 0)) == 1:
        risk_factors.append("Elevated fasting blood sugar")
    
    if float(data.get('restecg', 0)) == 1:
        risk_factors.append("ECG abnormalities")
    elif float(data.get('restecg', 0)) == 2:
        risk_factors.append("Left ventricular hypertrophy")
    
    if float(data.get('thalach', 0)) < 100:
        risk_factors.append("Low maximum heart rate")
    
    if float(data.get('exang', 0)) == 1:
        risk_factors.append("Exercise-induced chest pain")
    
    if float(data.get('oldpeak', 0)) > 2:
        risk_factors.append("Significant ST depression")
    
    if float(data.get('slope', 0)) == 2:
        risk_factors.append("Downsloping ST segment")
    
    ca = float(data.get('ca', 0))
    if ca > 0:
        risk_factors.append(f"{int(ca)} major vessel(s) with narrowing")
    
    thal = float(data.get('thal', 0))
    if thal == 1:
        risk_factors.append("Fixed perfusion defect")
    elif thal == 2:
        risk_factors.append("Reversible perfusion defect")
    
    return risk_factors

@app.route('/model-info')
def model_info():
    """Get information about the loaded model"""
    if model is None:
        return jsonify({'error': 'Model not loaded'})
    
    try:
        model_type = type(model).__name__
        has_proba = hasattr(model, 'predict_proba')
        
        # Try to get feature names if available
        feature_names = []
        if hasattr(model, 'feature_names_in_'):
            feature_names = model.feature_names_in_.tolist()
        
        return jsonify({
            'model_type': model_type,
            'has_probability': has_proba,
            'feature_names': feature_names,
            'status': 'loaded'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting Heart Health Predictor Server...")
    print("Model status:", "Loaded" if model else "Not loaded")
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
