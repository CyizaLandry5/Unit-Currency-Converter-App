using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class UIManager : MonoBehaviour
{
    [Header("Panels")]
    public GameObject converterPanel;
    public GameObject historyPanel;
    public GameObject settingsPanel;

    [Header("Converter UI")]
    public Text resultText;
    public Button historyButton;
    public Button settingsButton;
    public Button updateRatesButton;

    [Header("History UI")]
    public Transform historyContent;
    public GameObject historyItemPrefab;
    public Button backFromHistoryButton;
    public Button clearHistoryButton;

    [Header("Settings UI")]
    public Dropdown baseCurrencyDropdown;
    public Toggle autoUpdateToggle;
    public Slider updateIntervalSlider;
    public Text updateIntervalText;
    public Button backFromSettingsButton;
    public Button saveSettingsButton;

    void Start()
    {
        SetupButtonListeners();
        LoadSettings();
        ShowConverterPanel();
    }

    void SetupButtonListeners()
    {
        // Navigation buttons
        historyButton.onClick.AddListener(ShowHistoryPanel);
        settingsButton.onClick.AddListener(ShowSettingsPanel);
        backFromHistoryButton.onClick.AddListener(ShowConverterPanel);
        backFromSettingsButton.onClick.AddListener(ShowConverterPanel);
        
        // History buttons
        clearHistoryButton.onClick.AddListener(ClearHistory);
        
        // Settings buttons
        saveSettingsButton.onClick.AddListener(SaveSettings);
        updateIntervalSlider.onValueChanged.AddListener(OnUpdateIntervalChanged);
        
        // Update rates button
        updateRatesButton.onClick.AddListener(UpdateExchangeRates);
    }

    public void ShowConverterPanel()
    {
        converterPanel.SetActive(true);
        historyPanel.SetActive(false);
        settingsPanel.SetActive(false);
    }

    public void ShowHistoryPanel()
    {
        converterPanel.SetActive(false);
        historyPanel.SetActive(true);
        settingsPanel.SetActive(false);
        LoadHistory();
    }

    public void ShowSettingsPanel()
    {
        converterPanel.SetActive(false);
        historyPanel.SetActive(false);
        settingsPanel.SetActive(true);
    }

    void LoadHistory()
    {
        // Clear existing items
        foreach (Transform child in historyContent)
        {
            Destroy(child.gameObject);
        }

        // Load history from PlayerPrefs
        if (PlayerPrefs.HasKey("ConversionHistory"))
        {
            string savedHistory = PlayerPrefs.GetString("ConversionHistory");
            var historyList = JsonUtility.FromJson<StringList>(savedHistory);
            
            if (historyList != null && historyList.items.Count > 0)
            {
                foreach (string historyItem in historyList.items)
                {
                    GameObject item = Instantiate(historyItemPrefab, historyContent);
                    item.GetComponentInChildren<Text>().text = historyItem;
                }
            }
            else
            {
                ShowNoHistoryMessage();
            }
        }
        else
        {
            ShowNoHistoryMessage();
        }
    }

    void ShowNoHistoryMessage()
    {
        GameObject item = Instantiate(historyItemPrefab, historyContent);
        item.GetComponentInChildren<Text>().text = "No conversion history yet";
        item.GetComponentInChildren<Text>().color = Color.gray;
    }

    void ClearHistory()
    {
        PlayerPrefs.DeleteKey("ConversionHistory");
        PlayerPrefs.Save();
        LoadHistory();
    }

    void LoadSettings()
    {
        // Load base currency
        string savedCurrency = PlayerPrefs.GetString("BaseCurrency", "USD");
        List<string> currencies = new List<string> { "USD", "EUR", "GBP", "JPY" };
        baseCurrencyDropdown.AddOptions(currencies);
        baseCurrencyDropdown.value = currencies.IndexOf(savedCurrency);
        
        // Load auto-update setting
        autoUpdateToggle.isOn = PlayerPrefs.GetInt("AutoUpdate", 1) == 1;
        
        // Load update interval
        float interval = PlayerPrefs.GetFloat("UpdateInterval", 30f);
        updateIntervalSlider.value = interval;
        updateIntervalText.text = $"Update every {interval} minutes";
    }

    void SaveSettings()
    {
        // Save base currency
        string selectedCurrency = baseCurrencyDropdown.options[baseCurrencyDropdown.value].text;
        PlayerPrefs.SetString("BaseCurrency", selectedCurrency);
        
        // Save auto-update
        PlayerPrefs.SetInt("AutoUpdate", autoUpdateToggle.isOn ? 1 : 0);
        
        // Save update interval
        PlayerPrefs.SetFloat("UpdateInterval", updateIntervalSlider.value);
        
        PlayerPrefs.Save();
        
        ShowConverterPanel();
    }

    void OnUpdateIntervalChanged(float value)
    {
        updateIntervalText.text = $"Update every {value} minutes";
    }

    void UpdateExchangeRates()
    {
        updateRatesButton.interactable = false;
        updateRatesButton.GetComponentInChildren<Text>().text = "Updating...";
        
        StartCoroutine(CurrencyAPI.Instance.GetExchangeRates("USD", (rates) => {
            if (rates != null)
            {
                // Update the converter with new rates
                CurrencyConverter converter = FindObjectOfType<CurrencyConverter>();
                if (converter != null)
                {
                    // You'll need to add a public method to update rates in CurrencyConverter
                    resultText.text = "Rates updated successfully!";
                    resultText.color = Color.green;
                }
            }
            else
            {
                resultText.text = "Failed to update rates";
                resultText.color = Color.red;
            }
            
            updateRatesButton.interactable = true;
            updateRatesButton.GetComponentInChildren<Text>().text = "Update Rates";
        }));
    }
}