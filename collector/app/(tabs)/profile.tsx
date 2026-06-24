import { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { useAuth } from '../../context/auth';
import { colors } from '../../constants/theme';

export default function Profile() {
  const { session, signOut } = useAuth();
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

      {/* Account section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ACCOUNT</Text>
        <View style={styles.card}>
          <Row label="Email" value={email} />
        </View>
      </View>

      {/* About section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ABOUT</Text>
        <View style={styles.card}>
          <Row label="App" value="Collector" />
          <Row label="Version" value="1.0.1" last />
        </View>
      </View>

      {/* Sign out */}
      <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut} disabled={signingOut}>
        <Text style={styles.signOutText}>{signingOut ? 'Signing out...' : 'Sign Out'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function Row({ label, value, last }: { label: string; value: string; last?: boolean }) {
  return (
    <View style={[styles.row, !last && styles.rowBorder]}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 16, paddingBottom: 48 },
  avatarSection: { alignItems: 'center', paddingVertical: 32 },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarText: { color: colors.background, fontSize: 28, fontWeight: 'bold' },
  email: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 4 },
  joined: { color: colors.subtext, fontSize: 13 },
  section: { marginBottom: 24 },
  sectionTitle: { color: colors.subtext, fontSize: 11, fontWeight: '600', letterSpacing: 1, marginBottom: 8 },
  card: { backgroundColor: colors.surface, borderRadius: 12, borderWidth: 1, borderColor: colors.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
  rowLabel: { color: colors.subtext, fontSize: 14 },
  rowValue: { color: colors.text, fontSize: 14, fontWeight: '500', flexShrink: 1, textAlign: 'right', marginLeft: 16 },
  signOutButton: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.negative,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  signOutText: { color: colors.negative, fontSize: 16, fontWeight: '600' },
});
