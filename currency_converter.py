import requests
import json
from datetime import datetime
import sqlite3
from typing import Optional, Dict, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import sys

class CurrencyConverter:
    def __init__(self, api_key: str = None):
        """
        Initialize the currency converter.
        If no API key provided, uses free API with limitations.
        """
        self.api_key = api_key
        self.base_url = "https://api.exchangerate-api.com/v4/latest/"
        self.rates = {}
        self.last_update = None
        self.initialize_database()
        self.load_cached_rates()
    
    def initialize_database(self):
        """Initialize SQLite database for storing rates and history."""
        self.conn = sqlite3.connect('currency_converter.db')
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency_pair TEXT UNIQUE,
                rate REAL,
                last_updated TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                from_currency TEXT,
                to_currency TEXT,
                result REAL,
                conversion_date TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def load_cached_rates(self):
        """Load cached exchange rates from database."""
        self.cursor.execute("SELECT currency_pair, rate FROM exchange_rates")
        rows = self.cursor.fetchall()
        self.rates = {row[0]: row[1] for row in rows}
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate between two currencies.
        Returns rate or None if not available.
        """
        # If same currency
        if from_currency == to_currency:
            return 1.0
        
        # Check cache first
        pair = f"{from_currency}_{to_currency}"
        if pair in self.rates:
            return self.rates[pair]
        
        # Try to get from API
        rate = self.fetch_rate_from_api(from_currency, to_currency)
        if rate:
            self.cache_rate(pair, rate)
            return rate
        
        # Try reverse rate
        reverse_pair = f"{to_currency}_{from_currency}"
        if reverse_pair in self.rates:
            return 1 / self.rates[reverse_pair]
        
        # Try through USD
        if from_currency != "USD" and to_currency != "USD":
            usd_from = self.get_exchange_rate(from_currency, "USD")
            usd_to = self.get_exchange_rate("USD", to_currency)
            if usd_from and usd_to:
                rate = usd_from * usd_to
                self.cache_rate(pair, rate)
                return rate
        
        return None
    
    def fetch_rate_from_api(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Fetch exchange rate from API.
        Uses free API (no key needed for basic usage).
        """
        try:
            if self.api_key:
                # If you have a paid API key
                url = f"{self.base_url}{from_currency}?api_key={self.api_key}"
            else:
                # Free API (limited requests)
                url = f"{self.base_url}{from_currency}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if to_currency in data.get('rates', {}):
                rate = data['rates'][to_currency]
                self.last_update = datetime.now()
                
                # Cache all rates from this response
                for curr, curr_rate in data['rates'].items():
                    pair = f"{from_currency}_{curr}"
                    self.cache_rate(pair, curr_rate)
                
                return rate
        
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
        
        return None
    
    def cache_rate(self, currency_pair: str, rate: float):
        """Cache exchange rate in database."""
        self.rates[currency_pair] = rate
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO exchange_rates 
            (currency_pair, rate, last_updated) 
            VALUES (?, ?, ?)
        ''', (currency_pair, rate, datetime.now()))
        
        self.conn.commit()
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Convert amount from one currency to another."""
        rate = self.get_exchange_rate(from_currency, to_currency)
        
        if rate is None:
            return None
        
        result = amount * rate
        
        # Save to history
        self.save_conversion_history(amount, from_currency, to_currency, result)
        
        return result
    
    def save_conversion_history(self, amount: float, from_currency: str, 
                               to_currency: str, result: float):
        """Save conversion to history database."""
        self.cursor.execute('''
            INSERT INTO conversion_history 
            (amount, from_currency, to_currency, result, conversion_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (amount, from_currency, to_currency, result, datetime.now()))
        
        self.conn.commit()
    
    def get_conversion_history(self, limit: int = 10):
        """Get recent conversion history."""
        self.cursor.execute('''
            SELECT amount, from_currency, to_currency, result, conversion_date
            FROM conversion_history
            ORDER BY conversion_date DESC
            LIMIT ?
        ''', (limit,))
        
        return self.cursor.fetchall()
    
    def get_supported_currencies(self):
        """Get list of supported currencies."""
        # Common currencies - you can expand this list
        currencies = [
            "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY",
            "INR", "SGD", "MYR", "IDR", "KRW", "THB", "VND", "PHP",
            "BRL", "RUB", "ZAR", "AED", "MXN", "TRY", "NZD", "HKD"
        ]
        return currencies
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()


class CurrencyConverterGUI:
    def __init__(self, converter: CurrencyConverter):
        self.converter = converter
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Currency Converter")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Currency Converter",
            font=("Arial", 20, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        title_label.pack(pady=20)
        
        # Amount frame
        amount_frame = tk.Frame(self.root, bg="#f0f0f0")
        amount_frame.pack(pady=10)
        
        tk.Label(
            amount_frame,
            text="Amount:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=5)
        
        self.amount_var = tk.StringVar(value="1.00")
        self.amount_entry = tk.Entry(
            amount_frame,
            textvariable=self.amount_var,
            font=("Arial", 12),
            width=15,
            justify="right"
        )
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Currency selection frame
        currency_frame = tk.Frame(self.root, bg="#f0f0f0")
        currency_frame.pack(pady=20)
        
        # From currency
        from_frame = tk.Frame(currency_frame, bg="#f0f0f0")
        from_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            from_frame,
            text="From:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack()
        
        self.from_currency = ttk.Combobox(
            from_frame,
            values=self.converter.get_supported_currencies(),
            state="readonly",
            width=10,
            font=("Arial", 12)
        )
        self.from_currency.set("USD")
        self.from_currency.pack(pady=5)
        
        # To currency
        to_frame = tk.Frame(currency_frame, bg="#f0f0f0")
        to_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            to_frame,
            text="To:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack()
        
        self.to_currency = ttk.Combobox(
            to_frame,
            values=self.converter.get_supported_currencies(),
            state="readonly",
            width=10,
            font=("Arial", 12)
        )
        self.to_currency.set("EUR")
        self.to_currency.pack(pady=5)
        
        # Swap button
        swap_btn = tk.Button(
            currency_frame,
            text="↔",
            font=("Arial", 12, "bold"),
            command=self.swap_currencies,
            bg="#4CAF50",
            fg="white",
            padx=10
        )
        swap_btn.pack(side=tk.LEFT, padx=10)
        
        # Convert button
        convert_btn = tk.Button(
            self.root,
            text="Convert",
            font=("Arial", 14, "bold"),
            command=self.perform_conversion,
            bg="#2196F3",
            fg="white",
            padx=30,
            pady=10
        )
        convert_btn.pack(pady=20)
        
        # Result display
        self.result_var = tk.StringVar(value="Result will appear here")
        result_label = tk.Label(
            self.root,
            textvariable=self.result_var,
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        result_label.pack(pady=10)
        
        # Last update label
        self.update_var = tk.StringVar(value="")
        update_label = tk.Label(
            self.root,
            textvariable=self.update_var,
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        update_label.pack()
        
        # History button
        history_btn = tk.Button(
            self.root,
            text="View History",
            font=("Arial", 10),
            command=self.show_history,
            bg="#FF9800",
            fg="white"
        )
        history_btn.pack(pady=10)
        
        # Bind events
        self.amount_entry.bind("<KeyRelease>", lambda e: self.perform_conversion())
        self.from_currency.bind("<<ComboboxSelected>>", lambda e: self.perform_conversion())
        self.to_currency.bind("<<ComboboxSelected>>", lambda e: self.perform_conversion())
        
        # Initial conversion
        self.perform_conversion()
    
    def perform_conversion(self):
        """Perform currency conversion and update display."""
        try:
            amount = float(self.amount_var.get())
            from_curr = self.from_currency.get()
            to_curr = self.to_currency.get()
            
            if not from_curr or not to_curr:
                return
            
            result = self.converter.convert(amount, from_curr, to_curr)
            
            if result is not None:
                self.result_var.set(f"{amount:.2f} {from_curr} = {result:.2f} {to_curr}")
                
                # Update last update time
                if self.converter.last_update:
                    update_time = self.converter.last_update.strftime("%Y-%m-%d %H:%M:%S")
                    self.update_var.set(f"Last updated: {update_time}")
                else:
                    self.update_var.set("Using cached rates")
            else:
                self.result_var.set("Error: Could not get exchange rate")
                self.update_var.set("")
        
        except ValueError:
            self.result_var.set("Error: Invalid amount")
            self.update_var.set("")
    
    def swap_currencies(self):
        """Swap the from and to currencies."""
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        self.from_currency.set(to_curr)
        self.to_currency.set(from_curr)
        self.perform_conversion()
    
    def show_history(self):
        """Show conversion history in a new window."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Conversion History")
        history_window.geometry("500x400")
        
        # Title
        tk.Label(
            history_window,
            text="Recent Conversions",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Text widget for history
        history_text = tk.Text(history_window, height=15, width=60)
        history_text.pack(padx=10, pady=10)
        
        # Get history
        history = self.converter.get_conversion_history(limit=20)
        
        if not history:
            history_text.insert(tk.END, "No conversion history found.")
        else:
            for record in history:
                amount, from_curr, to_curr, result, date = record
                history_text.insert(
                    tk.END,
                    f"{date}: {amount:.2f} {from_curr} → {result:.2f} {to_curr}\n"
                )
        
        history_text.config(state=tk.DISABLED)
        
        # Close button
        tk.Button(
            history_window,
            text="Close",
            command=history_window.destroy
        ).pack(pady=10)
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main function to run the currency converter."""
    print("Starting Currency Converter...")
    
    
    API_KEY = None  
    
    try:
        converter = CurrencyConverter(api_key=API_KEY)
        app = CurrencyConverterGUI(converter)
        app.run()
    
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()