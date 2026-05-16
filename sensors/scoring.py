import numpy as np
import math

#https://indoor.lbl.gov/publications/effect-temperature-task-performance
def temperatureScore(temperature, optimal=22.0):
    """Productivity function based on temperature in Celsius."""
    return (
        0.0000623 * temperature**3
        - 0.0058274 * temperature**2
        + 0.1647524 * temperature
        - 0.4685328
    ) * 100

#https://www.sciencedirect.com/science/article/abs/pii/S0272494413001060?via%3Dihub
#https://journals.sagepub.com/doi/10.1177/096032719002200201
def lightScore(lux, optimal=500):
    return 100 * np.log(lux + 1) / np.log(optimal)

#https://pubmed.ncbi.nlm.nih.gov/15330775/
def humidityScore(humidity):
    """
    Returns a multiplicative comfort factor between 0 and 1 based on relative humidity.
    
    rh: relative humidity in percent (0–100).
    
    Model assumptions (comfort / productivity-oriented):
      - Optimal around 45% RH  -> factor ≈ 1.00
      - Mild penalty at 30% or 60% RH -> factor ≈ 0.95
      - Larger penalty at 20% or 70% RH -> factor ≈ 0.80
      - Strong penalty at 10% or 80% RH -> factor ≈ 0.55
    """
    rh = max(0.0, min(100.0, humidity))
    
    # Quadratic penalty centered at 45% RH
    k = 0.000222  # tuned so 30% and 60% give ~0.95
    factor = 1.0 - k * (rh - 45.0) ** 2
    factor = factor * 100
    return factor

#https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research
def noiseScore(dB, threshold=0.02):
    """
    Convert A-weighted sound level in dBA to a 0–100 'noise productivity' score.

    Based on:
      Srinivasan et al. (2023), npj Digital Medicine:
      - Physiological wellbeing is optimal at 50 dBA.
      - For levels < 50 dBA, a 10 dBA increase -> +5.4% wellbeing.
      - For levels > 50 dBA, a 10 dBA increase -> -1.9% wellbeing.

    We interpret wellbeing % as a proxy for 'noise-related productivity % of optimum'.
    """
    # Safety clamp for insane inputs
    db = float(dB)
    if db < 0:
        db = 0.0
    if db > 120:
        db = 120.0

    if db <= 50.0:
        # 5.4% loss in wellbeing per 10 dB below 50
        score = 100.0 - 5.4 * ((50.0 - db) / 10.0)
    else:
        # 1.9% loss in wellbeing per 10 dB above 50
        score = 100.0 - 1.9 * ((db - 50.0) / 10.0)

    return score

def totalScore(temp_score, light_score, humidity_score, noise_score):
    """Combine individual scores into a total score."""
    weights = {
        "temperature": 0.25,
        "light": 0.25,
        "humidity": 0.25,
        "noise": 0.25,
    }
    total = (
        temp_score * weights["temperature"] +
        light_score * weights["light"] +
        humidity_score * weights["humidity"] +
        noise_score * weights["noise"]
    )
    return total

def calculateScores(readings):
    """Calculate scores for temperature, light, and humidity."""
    tempRead = readings["temperature_c"]
    lightRead = readings["light_lux"]
    humidRead = readings["humidity_pct"]
    noiseRead = readings["noise_db"]
    
    temp_score = temperatureScore(tempRead)
    light_score = lightScore(lightRead)
    humidity_score = humidityScore(humidRead)
    noise_score = noiseScore(noiseRead)
    total_score = totalScore(temp_score, light_score, humidity_score, noise_score)

    def round_safe(v):
        try:
            # convert to float then round to nearest whole number
            return int(round(float(v)))
        except Exception:
            return None

    return {
        "temperature_score": round_safe(temp_score),
        "light_score": round_safe(light_score),
        "humidity_score": round_safe(humidity_score),
        "noise_score": round_safe(noise_score),
        "total_score": round_safe(total_score),
    }
    

    