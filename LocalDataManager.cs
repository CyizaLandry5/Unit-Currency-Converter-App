using System.Collections.Generic;
using UnityEngine;

public class LocalDataManager : MonoBehaviour
{
    public TextAsset exchangeRatesFile;
    
    public Dictionary<string, float> LoadLocalRates()
    {
        if (exchangeRatesFile != null)
        {
            ExchangeRateData data = JsonUtility.FromJson<ExchangeRateData>(exchangeRatesFile.text);
            return data.rates;
        }
        
        // Return default rates if file not found
        return GetDefaultRates();
    }
    
    Dictionary<string, float> GetDefaultRates()
    {
        return new Dictionary<string, float>
        {
            {"USD_EUR", 0.92f},
            {"USD_GBP", 0.79f},
            {"USD_JPY", 148.50f},
            {"USD_INR", 83.12f},
            {"EUR_USD", 1.09f},
            {"EUR_GBP", 0.86f},
            {"GBP_USD", 1.27f},
            {"GBP_EUR", 1.16f}
        };
    }
}

[System.Serializable]
public class ExchangeRateData
{
    public Dictionary<string, float> rates;
    public string last_updated;
}