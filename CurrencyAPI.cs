using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class CurrencyAPI : MonoBehaviour
{
    public static CurrencyAPI Instance;
    
    private const string API_KEY = "API-HANO: // Get free key from exchangerate-api.com cant post mine for security"; 
    private const string BASE_URL = "https://api.exchangerate-api.com/v4/latest/";
    
    private Dictionary<string, float> cachedRates = new Dictionary<string, float>();
    private DateTime lastUpdateTime;
    
    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }
    
    public IEnumerator<object> GetExchangeRates(string baseCurrency, Action<Dictionary<string, float>> callback)
    {
        // Check cache (update every 30 minutes)
        if (cachedRates.Count > 0 && (DateTime.Now - lastUpdateTime).TotalMinutes < 30)
        {
            callback?.Invoke(cachedRates);
            yield break;
        }
        
        string url = BASE_URL + baseCurrency;
        
        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();
            
            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                ProcessAPIResponse(webRequest.downloadHandler.text, baseCurrency, callback);
            }
            else
            {
                Debug.LogError($"Error fetching exchange rates: {webRequest.error}");
                callback?.Invoke(null);
            }
        }
    }
    
    void ProcessAPIResponse(string jsonResponse, string baseCurrency, Action<Dictionary<string, float>> callback)
    {
        try
        {
            var response = JsonUtility.FromJson<ExchangeRateResponse>(jsonResponse);
            
            if (response != null && response.rates != null)
            {
                cachedRates.Clear();
                
                // Store all rates with base currency prefix
                foreach (var rate in response.rates)
                {
                    string key = $"{baseCurrency}_{rate.Key}";
                    cachedRates[key] = rate.Value;
                }
                
                lastUpdateTime = DateTime.Now;
                callback?.Invoke(cachedRates);
            }
            else
            {
                callback?.Invoke(null);
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error processing API response: {e.Message}");
            callback?.Invoke(null);
        }
    }
    
    // For testing without API
    public Dictionary<string, float> GetMockRates()
    {
        return new Dictionary<string, float>
        {
            {"USD_EUR", 0.85f},
            {"USD_GBP", 0.73f},
            {"USD_JPY", 110.5f},
            {"USD_AUD", 1.35f},
            {"EUR_USD", 1.18f},
            {"EUR_GBP", 0.86f},
            {"GBP_USD", 1.37f},
            {"GBP_EUR", 1.16f}
        };
    }
}

[System.Serializable]
public class ExchangeRateResponse
{
    public string result;
    public string documentation;
    public string terms_of_use;
    public long time_last_update_unix;
    public string time_last_update_utc;
    public long time_next_update_unix;
    public string time_next_update_utc;
    public string base_code;
    public Dictionary<string, float> rates;
}

// Helper class for dictionary serialization
[System.Serializable]
public class RateDictionary : ISerializationCallbackReceiver
{
    [SerializeField]
    private List<string> keys = new List<string>();
    
    [SerializeField]
    private List<float> values = new List<float>();
    
    private Dictionary<string, float> dictionary = new Dictionary<string, float>();
    
    public Dictionary<string, float> Dictionary => dictionary;
    
    public void OnBeforeSerialize()
    {
        keys.Clear();
        values.Clear();
        
        foreach (var kvp in dictionary)
        {
            keys.Add(kvp.Key);
            values.Add(kvp.Value);
        }
    }
    
    public void OnAfterDeserialize()
    {
        dictionary.Clear();
        
        for (int i = 0; i < keys.Count && i < values.Count; i++)
        {
            dictionary[keys[i]] = values[i];
        }
    }
}