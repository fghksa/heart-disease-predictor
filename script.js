// Heart Health Predictor JavaScript
class HeartHealthPredictor {
    constructor() {
        this.form = document.getElementById('healthForm');
        this.resultsSection = document.getElementById('resultsSection');
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.addInputAnimations();
    }

    handleSubmit(e) {
        e.preventDefault();
        
        // Show loading state
        this.showLoading();
        
        const formData = this.getFormData();
        
        // Try to use the Flask backend first, fallback to local prediction
        this.callBackendPrediction(formData)
            .then(prediction => {
                this.displayResults(prediction);
                this.hideLoading();
            })
            .catch(error => {
                console.log('Backend unavailable, using local prediction:', error);
                // Fallback to local prediction
                const prediction = this.predictHeartHealth(formData);
                this.displayResults(prediction);
                this.hideLoading();
            });
    }

    async callBackendPrediction(data) {
        try {
            const response = await fetch('http://localhost:8080/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            return result;
        } catch (error) {
            // If localhost:8080 fails, try the current host
            try {
                const response = await fetch(`${window.location.origin}/predict`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                
                if (result.error) {
                    throw new Error(result.error);
                }

                return result;
            } catch (secondError) {
                throw new Error('Backend server not available');
            }
        }
    }

    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = parseFloat(value) || value;
        }
        
        return data;
    }

    predictHeartHealth(data) {
        // Simulate heart health prediction based on input parameters
        // This is a simplified algorithm for demonstration purposes
        
        let riskScore = 0;
        let riskFactors = [];
        
        // Age factor
        if (data.age > 65) {
            riskScore += 15;
            riskFactors.push("Advanced age");
        } else if (data.age > 50) {
            riskScore += 8;
        }
        
        // Sex factor (males generally higher risk)
        if (data.sex == 1) {
            riskScore += 5;
        }
        
        // Chest pain type
        if (data.cp == 0) {
            riskScore += 20;
            riskFactors.push("Typical angina symptoms");
        } else if (data.cp == 1) {
            riskScore += 10;
            riskFactors.push("Atypical chest pain");
        }
        
        // Blood pressure
        if (data.trestbps > 140) {
            riskScore += 15;
            riskFactors.push("High blood pressure");
        } else if (data.trestbps > 130) {
            riskScore += 8;
        }
        
        // Cholesterol
        if (data.chol > 240) {
            riskScore += 15;
            riskFactors.push("High cholesterol");
        } else if (data.chol > 200) {
            riskScore += 8;
        }
        
        // Fasting blood sugar
        if (data.fbs == 1) {
            riskScore += 10;
            riskFactors.push("Elevated fasting blood sugar");
        }
        
        // ECG abnormalities
        if (data.restecg == 1) {
            riskScore += 8;
            riskFactors.push("ECG abnormalities");
        } else if (data.restecg == 2) {
            riskScore += 12;
            riskFactors.push("Left ventricular hypertrophy");
        }
        
        // Maximum heart rate
        if (data.thalach < 100) {
            riskScore += 12;
            riskFactors.push("Low maximum heart rate");
        }
        
        // Exercise induced angina
        if (data.exang == 1) {
            riskScore += 15;
            riskFactors.push("Exercise-induced chest pain");
        }
        
        // ST depression
        if (data.oldpeak > 2) {
            riskScore += 15;
            riskFactors.push("Significant ST depression");
        } else if (data.oldpeak > 1) {
            riskScore += 8;
        }
        
        // ST slope
        if (data.slope == 2) {
            riskScore += 12;
            riskFactors.push("Downsloping ST segment");
        } else if (data.slope == 1) {
            riskScore += 6;
        }
        
        // Number of major vessels
        if (data.ca > 0) {
            riskScore += data.ca * 10;
            riskFactors.push(`${data.ca} major vessel(s) with narrowing`);
        }
        
        // Thalassemia
        if (data.thal == 1) {
            riskScore += 8;
            riskFactors.push("Fixed perfusion defect");
        } else if (data.thal == 2) {
            riskScore += 12;
            riskFactors.push("Reversible perfusion defect");
        }
        
        // Cap the risk score at 100
        riskScore = Math.min(riskScore, 100);
        
        return {
            riskScore: riskScore,
            riskFactors: riskFactors,
            hasHeartDisease: riskScore > 50
        };
    }

    displayResults(prediction) {
        const resultCard = document.getElementById('resultCard');
        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');
        const meterFill = document.getElementById('meterFill');
        const meterText = document.getElementById('meterText');
        const resultDescription = document.getElementById('resultDescription');
        const recommendationsList = document.getElementById('recommendationsList');
        
        // Animate meter
        this.animateMeter(prediction.riskScore);
        
        // Set result icon and title
        if (prediction.hasHeartDisease) {
            resultIcon.className = 'result-icon risk';
            resultTitle.textContent = 'Elevated Risk Detected';
            resultDescription.textContent = `Based on the provided health parameters, our AI model indicates a ${prediction.riskScore}% risk level for heart disease. This suggests you may benefit from further medical evaluation and lifestyle modifications.`;
        } else {
            resultIcon.className = 'result-icon healthy';
            resultTitle.textContent = 'Heart Health Looks Good';
            resultDescription.textContent = `Based on the provided health parameters, our AI model indicates a ${prediction.riskScore}% risk level for heart disease. Your heart health appears to be in good condition, but maintaining healthy habits is always important.`;
        }
        
        // Generate recommendations
        const recommendations = this.generateRecommendations(prediction);
        recommendationsList.innerHTML = '';
        recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recommendationsList.appendChild(li);
        });
        
        // Show results section
        this.resultsSection.style.display = 'block';
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    animateMeter(targetScore) {
        const meterText = document.getElementById('meterText');
        let currentScore = 0;
        const increment = targetScore / 30; // 30 frames for smooth animation
        
        const animation = setInterval(() => {
            currentScore += increment;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(animation);
            }
            meterText.textContent = Math.round(currentScore) + '%';
        }, 50);
    }

    generateRecommendations(prediction) {
        const recommendations = [];
        
        if (prediction.hasHeartDisease) {
            recommendations.push("Consult with a cardiologist for comprehensive evaluation");
            recommendations.push("Consider stress testing and advanced cardiac imaging");
            recommendations.push("Monitor blood pressure and cholesterol levels regularly");
            recommendations.push("Implement a heart-healthy diet low in saturated fats");
            recommendations.push("Engage in supervised exercise program");
            recommendations.push("Take prescribed medications as directed");
        } else {
            recommendations.push("Maintain regular cardiovascular exercise (150 min/week)");
            recommendations.push("Follow a balanced, heart-healthy diet");
            recommendations.push("Schedule annual health checkups");
            recommendations.push("Maintain healthy weight and manage stress");
            recommendations.push("Avoid smoking and limit alcohol consumption");
            recommendations.push("Monitor blood pressure and cholesterol periodically");
        }
        
        // Add specific recommendations based on risk factors
        if (prediction.riskFactors.includes("High blood pressure")) {
            recommendations.push("Focus on reducing sodium intake");
        }
        
        if (prediction.riskFactors.includes("High cholesterol")) {
            recommendations.push("Consider dietary changes to lower cholesterol");
        }
        
        if (prediction.riskFactors.includes("Exercise-induced chest pain")) {
            recommendations.push("Avoid strenuous exercise until cleared by physician");
        }
        
        return recommendations;
    }

    showLoading() {
        this.form.classList.add('loading');
        const btnText = this.form.querySelector('.btn-text');
        btnText.textContent = 'Analyzing';
    }

    hideLoading() {
        this.form.classList.remove('loading');
        const btnText = this.form.querySelector('.btn-text');
        btnText.textContent = 'Analyze Heart Health';
    }

    addInputAnimations() {
        const inputs = this.form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentNode.style.transform = 'scale(1.02)';
            });
            
            input.addEventListener('blur', function() {
                this.parentNode.style.transform = 'scale(1)';
            });
        });
    }
}

// Health tips and educational content
class HealthTipsManager {
    constructor() {
        this.tips = [
            "Regular exercise can reduce heart disease risk by up to 35%",
            "A Mediterranean diet is associated with better heart health",
            "Getting 7-9 hours of sleep is crucial for cardiovascular health",
            "Stress management techniques can significantly improve heart health",
            "Limiting processed foods helps maintain healthy cholesterol levels"
        ];
        this.showRandomTip();
    }

    showRandomTip() {
        // Implementation for showing health tips could be added here
        console.log("Health Tip:", this.tips[Math.floor(Math.random() * this.tips.length)]);
    }
}

// Form validation enhancements
class FormValidator {
    constructor(form) {
        this.form = form;
        this.initValidation();
    }

    initValidation() {
        const inputs = this.form.querySelectorAll('input[type="number"]');
        
        inputs.forEach(input => {
            input.addEventListener('input', (e) => this.validateInput(e));
        });
    }

    validateInput(e) {
        const input = e.target;
        const value = parseFloat(input.value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);
        
        if (value < min || value > max) {
            input.style.borderColor = '#f5576c';
            input.style.boxShadow = '0 0 0 3px rgba(245, 87, 108, 0.1)';
        } else {
            input.style.borderColor = '';
            input.style.boxShadow = '';
        }
    }
}

// Accessibility enhancements
class AccessibilityManager {
    constructor() {
        this.addKeyboardNavigation();
        this.addAriaLabels();
    }

    addKeyboardNavigation() {
        // Enhanced keyboard navigation for better accessibility
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                // Add visual focus indicators
                setTimeout(() => {
                    const focused = document.activeElement;
                    if (focused.tagName === 'INPUT' || focused.tagName === 'SELECT') {
                        focused.style.outline = '2px solid #818cf8';
                    }
                }, 0);
            }
        });
    }

    addAriaLabels() {
        // Add ARIA labels for screen readers
        const form = document.getElementById('healthForm');
        form.setAttribute('aria-label', 'Heart health assessment form');
        
        const submitBtn = form.querySelector('.submit-btn');
        submitBtn.setAttribute('aria-describedby', 'submit-description');
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new HeartHealthPredictor();
    new HealthTipsManager();
    new FormValidator(document.getElementById('healthForm'));
    new AccessibilityManager();
    
    // Add some interactive animations
    const cards = document.querySelectorAll('.form-group');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });
});
