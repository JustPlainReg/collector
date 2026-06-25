import { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { AuthProvider, useAuth } from '../context/auth';
import { ThemeProvider, useTheme } from '../context/theme';
import { CurrencyProvider } from '../context/currency';
import { useNotifications } from '../hooks/useNotifications';

function RootLayoutNav() {
  const { session, loading } = useAuth();
  const { colors } = useTheme();
  useNotifications();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!session && !inAuthGroup) {
      router.replace('/(auth)/sign-in');
    } else if (session && inAuthGroup) {
      router.replace('/(tabs)');
    }
  }, [session, loading, segments]);

  return (
    <Stack>
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen
        name="item/[id]"
        options={{
          title: 'Item Detail',
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerShadowVisible: false,
        }}
      />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <CurrencyProvider>
        <AuthProvider>
          <RootLayoutNav />
        </AuthProvider>
      </CurrencyProvider>
    </ThemeProvider>
  );
}
