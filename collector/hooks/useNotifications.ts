import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { supabase } from '../lib/supabase';
import { useAuth } from '../context/auth';

export function useNotifications() {
  const { session } = useAuth();

  useEffect(() => {
    if (!session) return;
    register(session.user.id).catch(() => {});
  }, [session?.user.id]);
}

async function register(userId: string) {
  const { status: existing } = await Notifications.getPermissionsAsync();
  let status = existing;

  if (existing !== 'granted') {
    const { status: requested } = await Notifications.requestPermissionsAsync();
    status = requested;
  }

  if (status !== 'granted') return;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) return;

  const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });

  await supabase.from('push_tokens').upsert(
    { user_id: userId, token, updated_at: new Date().toISOString() },
    { onConflict: 'user_id' }
  );

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('price-alerts', {
      name: 'Price Alerts',
      importance: Notifications.AndroidImportance.HIGH,
    });
  }
}
