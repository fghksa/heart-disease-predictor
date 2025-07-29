#!/usr/bin/env python3
import pickle
import sys

print("Python version:", sys.version)
print("Testing model loading...")

try:
    # Try different loading methods
    with open('model.pkl', 'rb') as f:
        # Check first few bytes
        first_bytes = f.read(10)
        print("First 10 bytes:", first_bytes)
        
        # Reset file pointer
        f.seek(0)
        
        # Try loading with different protocols
        try:
            model = pickle.load(f)
            print("✅ Model loaded successfully!")
            print("Model type:", type(model))
            print("Model attributes:", dir(model)[:5])
            
            # Test prediction with dummy data
            import numpy as np
            dummy_data = np.array([[50, 1, 0, 120, 200, 0, 0, 150, 0, 1.0, 1]]).reshape(1, -1)
            prediction = model.predict(dummy_data)
            print("Test prediction:", prediction)
            
        except Exception as e:
            print("❌ Error loading model:", str(e))
            print("Error type:", type(e))
            
except Exception as e:
    print("❌ Error opening file:", str(e))
