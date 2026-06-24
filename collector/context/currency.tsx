import { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type Currency = 'USD' | 'EUR' | 'GBP';

type Rates = Record<Currency, number>;

type CurrencyContextType = {
  currency: Currency;
  setCurrency: (c: Currency) => void;
  formatPrice: (amount: number | null | undefined) => string;
};

const SYMBOLS: Record<Currency, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
};

const STORAGE_KEY = 'currency_preference';

const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'USD',
  setCurrency: () => {},
  formatPrice: (n) => (n != null ? `$${n.toLocaleString()}` : '—'),
});

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [currency, setCurrencyState] = useState<Currency>('USD');
  const [rates, setRates] = useState<Rates>({ USD: 1, EUR: 1, GBP: 1 });

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((val) => {
      if (val === 'USD' || val === 'EUR' || val === 'GBP') {
        setCurrencyState(val);
      }
    });

    fetch('https://open.er-api.com/v6/latest/USD')
      .then((r) => r.json())
      .then((data) => {
        if (data?.rates) {
          setRates({
            USD: 1,
            EUR: data.rates.EUR ?? 1,
            GBP: data.rates.GBP ?? 1,
          });
        }
      })
      .catch(() => {});
  }, []);

  const setCurrency = (c: Currency) => {
    setCurrencyState(c);
    AsyncStorage.setItem(STORAGE_KEY, c);
  };

  const formatPrice = (amount: number | null | undefined): string => {
    if (amount == null) return '—';
    const converted = amount * rates[currency];
    const symbol = SYMBOLS[currency];
    return `${symbol}${converted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, formatPrice }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  return useContext(CurrencyContext);
}
