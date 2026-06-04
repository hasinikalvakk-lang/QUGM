import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class QUGMDataEngine:
    @staticmethod
    def generate_synthetic_dataset(num_samples=1000):
        """Generates physiological data with weighted clinical risk levels."""
        base_time = datetime.now()
        data = []
        
        for i in range(num_samples):
            age = np.random.randint(20, 80)
            bmi = np.random.uniform(18.5, 35.0)
            
            # --- RISK LEVEL LOGIC ---
            # Randomly assign a risk profile to each data point to create realistic clusters
            # 70% Normal, 15% High (Hyper), 15% Low (Hypo)
            profile = np.random.choice(['normal', 'high', 'low'], p=[0.7, 0.15, 0.15])
            
            if profile == 'high':
                sbp = np.random.randint(140, 180)  # Higher BP
                base_glucose = np.random.uniform(150, 250)
                noise_range = 15
            elif profile == 'low':
                sbp = np.random.randint(90, 115)   # Lower BP
                base_glucose = np.random.uniform(50, 68)
                noise_range = 5
            else:
                sbp = np.random.randint(115, 135)  # Normal BP
                base_glucose = np.random.uniform(80, 120)
                noise_range = 10

            # Simulate PPG physics: Amplitude drops with age and higher blood pressure
            # stiffness factor = (age * 0.002) + (sbp * 0.001)
            ppg_amp = round(np.random.uniform(0.6, 0.9) - ((age * 0.002) + (sbp * 0.001)), 3)
            
            # Final Glucose calculation incorporating physiological factors + profile bias
            glucose = round(base_glucose + (bmi * 0.3) + np.random.normal(0, noise_range), 2)
            
            data.append({
                "timestamp": (base_time + timedelta(seconds=i*10)).strftime("%H:%M:%S"),
                "ppg_amplitude": float(max(0.1, ppg_amp)), # Ensure amplitude doesn't go negative
                "systolic_bp": int(sbp),
                "age": int(age),
                "bmi": float(round(bmi, 1)),
                "glucose_value": float(glucose),
                "risk_level": profile.capitalize()
            })
            
        return pd.DataFrame(data)

    @staticmethod
    def get_statistics(df):
        """Standardizes all types and handles categorical intervals for JSON."""
        # Fix for the 'Interval' TypeError in JSON serialization
        age_bins = pd.cut(df['age'], bins=[0, 30, 50, 100], labels=["Young", "Middle", "Senior"])
        avg_gluc_age = df.groupby(age_bins, observed=False)['glucose_value'].mean().to_dict()
        
        # Calculate summary and handle potential NaN values
        desc = df['glucose_value'].describe().to_dict()
        
        return {
            "summary": {k: float(v) if not pd.isna(v) else 0.0 for k, v in desc.items()},
            "correlation": float(df['ppg_amplitude'].corr(df['glucose_value'])) if len(df) > 1 else 0.0,
            "categories": {
                "Low (<70)": int((df['glucose_value'] < 70).sum()),
                "Normal (70-140)": int(((df['glucose_value'] >= 70) & (df['glucose_value'] <= 140)).sum()),
                "High (>140)": int((df['glucose_value'] > 140).sum())
            },
            # Convert keys to string to avoid Interval object error
            "avg_by_age": {str(k): round(float(v), 2) if not pd.isna(v) else 0.0 for k, v in avg_gluc_age.items()}
        }