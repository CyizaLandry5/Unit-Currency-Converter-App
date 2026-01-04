import sys
import argparse
from currency_converter import CurrencyConverter

def main():
    parser = argparse.ArgumentParser(description="Currency Converter CLI")
    parser.add_argument("amount", type=float, help="Amount to convert")
    parser.add_argument("from_currency", help="Source currency code (e.g., USD)")
    parser.add_argument("to_currency", help="Target currency code (e.g., EUR)")
    parser.add_argument("--api-key", help="API key for exchange rate service")
    parser.add_argument("--list-currencies", action="store_true", 
                       help="List all supported currencies")
    parser.add_argument("--history", type=int, nargs="?", const=10,
                       help="Show conversion history (optional: number of records)")
    
    args = parser.parse_args()
    
    converter = CurrencyConverter(api_key=args.api_key)
    
    if args.list_currencies:
        print("\nSupported Currencies:")
        print("-" * 30)
        for currency in converter.get_supported_currencies():
            print(currency)
        return
    
    if args.history:
        history = converter.get_conversion_history(limit=args.history)
        if not history:
            print("No conversion history found.")
        else:
            print("\nConversion History:")
            print("-" * 60)
            for record in history:
                amount, from_curr, to_curr, result, date = record
                print(f"{date}: {amount:.2f} {from_curr} → {result:.2f} {to_curr}")
        return
    
    # Perform conversion
    try:
        result = converter.convert(args.amount, args.from_currency, args.to_currency)
        
        if result is not None:
            print(f"\n{args.amount:.2f} {args.from_currency} = {result:.2f} {args.to_currency}")
            
            # Show rate
            rate = converter.get_exchange_rate(args.from_currency, args.to_currency)
            if rate:
                print(f"Exchange Rate: 1 {args.from_currency} = {rate:.4f} {args.to_currency}")
        else:
            print(f"Error: Could not convert {args.from_currency} to {args.to_currency}")
            print("Please check currency codes and try again.")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()