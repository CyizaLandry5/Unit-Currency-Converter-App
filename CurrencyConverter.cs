using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CurrencyConverter : MonoBehaviour
{
    [Header("UI References")]
    public InputField amountInput;
    public Dropdown fromCurrencyDropdown;
    public Dropdown toCurrencyDropdown;
    public Text resultText;
    public Button convertButton;
    public Button swapButton;
    public Text lastUpdatedText;

    [Header("Settings")]
    public string defaultFromCurrency = "USD";
    public string defaultToCurrency = "EUR";

    private Dictionary<string, float> exchangeRates = new Dictionary<string, float>();
    private List<string> currencyCodes = new List<string>
    {
        "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", 
        "INR", "SGD", "MYR", "IDR", "KRW", "THB", "VND", "PHP"
    };

    void Start()
    {
        InitializeDropdowns();
        LoadSavedRates();
        SetupButtonListeners();
        
        // Set default values
        SetDefaultCurrencies();
        
        // Try to update rates on start
        StartCoroutine(CurrencyAPI.Instance.GetExchangeRates("USD", (rates) => {
            if (rates != null)
            {
                UpdateExchangeRates(rates);
                UpdateLastUpdatedTime();
            }
        }));
    }

    void InitializeDropdowns()
    {
        // Clear existing options
        fromCurrencyDropdown.ClearOptions();
        toCurrencyDropdown.ClearOptions();

        // Add currency options
        fromCurrencyDropdown.AddOptions(currencyCodes);
        toCurrencyDropdown.AddOptions(currencyCodes);
    }

    void SetupButtonListeners()
    {
        convertButton.onClick.AddListener(ConvertCurrency);
        swapButton.onClick.AddListener(SwapCurrencies);
        
        // Add real-time conversion on input change
        amountInput.onValueChanged.AddListener(delegate { ConvertCurrency(); });
        fromCurrencyDropdown.onValueChanged.AddListener(delegate { ConvertCurrency(); });
        toCurrencyDropdown.onValueChanged.AddListener(delegate { ConvertCurrency(); });
    }

    void SetDefaultCurrencies()
    {
        int fromIndex = currencyCodes.IndexOf(defaultFromCurrency);
        int toIndex = currencyCodes.IndexOf(defaultToCurrency);
        
        if (fromIndex >= 0) fromCurrencyDropdown.value = fromIndex;
        if (toIndex >= 0) toCurrencyDropdown.value = toIndex;
    }

    public void ConvertCurrency()
    {
        if (!float.TryParse(amountInput.text, out float amount) || amount <= 0)
        {
            resultText.text = "Please enter a valid amount";
            resultText.color = Color.red;
            return;
        }

        string fromCurrency = currencyCodes[fromCurrencyDropdown.value];
        string toCurrency = currencyCodes[toCurrencyDropdown.value];

        // If same currency selected
        if (fromCurrency == toCurrency)
        {
            resultText.text = $"{amount:N2} {fromCurrency} = {amount:N2} {toCurrency}";
            resultText.color = Color.green;
            return;
        }

        float convertedAmount = Convert(amount, fromCurrency, toCurrency);
        
        if (convertedAmount >= 0)
        {
            resultText.text = $"{amount:N2} {fromCurrency} = {convertedAmount:N2} {toCurrency}";
            resultText.color = Color.green;
            
            // Save conversion history
            SaveConversionHistory(amount, fromCurrency, convertedAmount, toCurrency);
        }
        else
        {
            resultText.text = "Conversion failed. Please check internet connection.";
            resultText.color = Color.red;
        }
    }

    float Convert(float amount, string fromCurrency, string toCurrency)
    {
        // If we have the direct rate
        string rateKey = $"{fromCurrency}_{toCurrency}";
        if (exchangeRates.ContainsKey(rateKey))
        {
            return amount * exchangeRates[rateKey];
        }

        // Convert through USD if available
        if (exchangeRates.ContainsKey($"{fromCurrency}_USD") && exchangeRates.ContainsKey($"USD_{toCurrency}"))
        {
            float amountInUSD = amount * exchangeRates[$"{fromCurrency}_USD"];
            return amountInUSD * exchangeRates[$"USD_{toCurrency}"];
        }

        return -1;
    }

    public void SwapCurrencies()
    {
        int temp = fromCurrencyDropdown.value;
        fromCurrencyDropdown.value = toCurrencyDropdown.value;
        toCurrencyDropdown.value = temp;
        
        ConvertCurrency();
    }

    void UpdateExchangeRates(Dictionary<string, float> newRates)
    {
        exchangeRates = newRates;
        PlayerPrefs.SetString("ExchangeRates_LastUpdate", DateTime.Now.ToString());
        SaveRatesToPlayerPrefs();
    }

    void LoadSavedRates()
    {
        if (PlayerPrefs.HasKey("ExchangeRates"))
        {
            string savedRates = PlayerPrefs.GetString("ExchangeRates");
            var ratesDict = JsonUtility.FromJson<SerializableDictionary>(savedRates);
            
            if (ratesDict != null)
            {
                exchangeRates = ratesDict.ToDictionary();
            }
        }
    }

    void SaveRatesToPlayerPrefs()
    {
        SerializableDictionary serializableDict = new SerializableDictionary(exchangeRates);
        string json = JsonUtility.ToJson(serializableDict);
        PlayerPrefs.SetString("ExchangeRates", json);
        PlayerPrefs.Save();
    }

    void UpdateLastUpdatedTime()
    {
        if (PlayerPrefs.HasKey("ExchangeRates_LastUpdate"))
        {
            string lastUpdate = PlayerPrefs.GetString("ExchangeRates_LastUpdate");
            lastUpdatedText.text = $"Last updated: {lastUpdate}";
        }
    }

    void SaveConversionHistory(float amount, string fromCurrency, float convertedAmount, string toCurrency)
    {
        string history = $"{DateTime.Now:HH:mm} - {amount} {fromCurrency} → {convertedAmount} {toCurrency}";
        
        // Load existing history
        List<string> historyList = new List<string>();
        if (PlayerPrefs.HasKey("ConversionHistory"))
        {
            string savedHistory = PlayerPrefs.GetString("ConversionHistory");
            var savedList = JsonUtility.FromJson<StringList>(savedHistory);
            if (savedList != null) historyList = savedList.items;
        }
        
        // Add new entry (keep only last 10)
        historyList.Insert(0, history);
        if (historyList.Count > 10) historyList.RemoveAt(historyList.Count - 1);
        
        // Save
        StringList listWrapper = new StringList { items = historyList };
        string json = JsonUtility.ToJson(listWrapper);
        PlayerPrefs.SetString("ConversionHistory", json);
    }
}

[System.Serializable]
public class SerializableDictionary
{
    [System.Serializable]
    public class RateEntry
    {
        public string key;
        public float value;
    }
    
    public List<RateEntry> entries = new List<RateEntry>();
    
    public SerializableDictionary() { }
    
    public SerializableDictionary(Dictionary<string, float> dictionary)
    {
        foreach (var kvp in dictionary)
        {
            entries.Add(new RateEntry { key = kvp.Key, value = kvp.Value });
        }
    }
    
    public Dictionary<string, float> ToDictionary()
    {
        Dictionary<string, float> dict = new Dictionary<string, float>();
        foreach (var entry in entries)
        {
            dict[entry.key] = entry.value;
        }
        return dict;
    }
}

[System.Serializable]
public class StringList
{
    public List<string> items = new List<string>();
}