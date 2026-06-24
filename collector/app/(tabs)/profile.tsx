import { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { useAuth } from '../../context/auth';
import { useTheme, ThemePreference } from '../../context/theme';
import type { ColorScheme } from '../../constants/theme';

export default function Profile() {
  const { session, signOut } = useAuth();
  const { colors, preference, setPreference } = useTheme();
  const styles = makeStyles(colors);
  const [signingOut, setSigningOut] = useState(false);

  const handleSignOut = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          setSigningOut(true);
          await signOut();
        },
      },
    ]);
  };

  const email = session?.user?.email ?? '';
  const joinedDate = session?.user?.created_at
    ? new Date(session.user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : null;

  const themeOptions: { value: ThemePreference; label: string }[] = [
    { value: 'system', label: 'System' },
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Avatar + email */}
      <View style={styles.avatarSection}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{email.charAt(0).toUpperCase()}</Text>
        </View>
        <Text style={styles.email}>{email}</Text>
        {joinedDate && <Text style={styles.joined}>Member since {joinedDate}</Text>}
      </View>

      {/* Appearance section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>APPEARANCE</Text>
        <View style={styles.card}>
          <View style={styles.themeRow}>
            <Text style={styles.rowLabel}>Theme</Text>
            <View style={styles.themeToggle}>
              {themeOptions.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[styles.themePill, preference === opt.value && styles.themePillActive]}
                  onPress={() => setPreference(opt.value)}
                >
                  <Text style={[styles.themePillText, preference === opt.value && styles.themePillTextActive]}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>
      </View>

      {/* Account section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ACCOUNT</Text>
        <View style={styles.card}>
          <Row label="Email" value={email} colors={colors} last />
        </View>
      </View>

      {/* About section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ABOUT</Text>
        <View style={styles.card}>
          <Row label="App" value="Collector" colors={colors} />
          <Row label="Version" value="1.0.1" colors={colors} last />
        </View>
      </View>

      {/* Sign out */}
      <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut} disabled={signingOut}>
        <Text style={styles.signOutText}>{signingOut ? 'Signing out...' : 'Sign Out'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function Row({ label, value, colors, last }: { label: string; value: string; colors: ColorScheme; last?: boolean }) {
  return (
    <View style={[{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14 }, !last && { borderBottomWidth: 1, borderBottomColor: colors.border }]}>
      <Text style={{ color: colors.subtext, fontSize: 14 }}>{label}</Text>
      <Text style={{ color: colors.text, fontSize: 14, fontWeight: '500', flexShrink: 1, textAlign: 'right', marginLeft: 16 }}>{value}</Text>
    </View>
  );
}

function makeStyles(c: ColorScheme) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: c.background },
    content: { padding: 16, paddingBottom: 48 },
    avatarSection: { alignItems: 'center', paddingVertical: 32 },
    avatar: {
      width: 72,
      height: 72,
      borderRadius: 36,
      backgroundColor: c.accent,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: 12,
    },
    avatarText: { color: c.background, fontSize: 28, fontWeight: 'bold' },
    email: { color: c.text, fontSize: 16, fontWeight: '600', marginBottom: 4 },
    joined: { color: c.subtext, fontSize: 13 },
    section: { marginBottom: 24 },
    sectionTitle: { color: c.subtext, fontSize: 11, fontWeight: '600', letterSpacing: 1, marginBottom: 8 },
    card: { backgroundColor: c.surface, borderRadius: 12, borderWidth: 1, borderColor: c.border },
    themeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: 14,
    },
    rowLabel: { color: c.subtext, fontSize: 14 },
    themeToggle: { flexDirection: 'row', gap: 6 },
    themePill: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: c.border,
      backgroundColor: c.background,
    },
    themePillActive: { backgroundColor: c.accent, borderColor: c.accent },
    themePillText: { color: c.subtext, fontSize: 13, fontWeight: '600' },
    themePillTextActive: { color: '#ffffff' },
    signOutButton: {
      backgroundColor: c.surface,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: c.negative,
      padding: 16,
      alignItems: 'center',
      marginTop: 8,
    },
    signOutText: { color: c.negative, fontSize: 16, fontWeight: '600' },
  });
}
