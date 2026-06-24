import { createContext, useContext, useEffect, useState } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { darkColors, lightColors, ColorScheme } from '../constants/theme';

export type ThemePreference = 'light' | 'dark' | 'system';

type ThemeContextType = {
  colors: ColorScheme;
  preference: ThemePreference;
  setPreference: (p: ThemePreference) => void;
  isDark: boolean;
};

const ThemeContext = createContext<ThemeContextType>({
  colors: darkColors,
  preference: 'system',
  setPreference: () => {},
  isDark: true,
});

const STORAGE_KEY = 'theme_preference';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useColorScheme();
  const [preference, setPreferenceState] = useState<ThemePreference>('system');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((val) => {
      if (val === 'light' || val === 'dark' || val === 'system') {
        setPreferenceState(val);
      }
    });
  }, []);

  const setPreference = (p: ThemePreference) => {
    setPreferenceState(p);
    AsyncStorage.setItem(STORAGE_KEY, p);
  };

  const effectiveScheme = preference === 'system' ? (systemScheme ?? 'dark') : preference;
  const isDark = effectiveScheme === 'dark';
  const colors = isDark ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ colors, preference, setPreference, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
