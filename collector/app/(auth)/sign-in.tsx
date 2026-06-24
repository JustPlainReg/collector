import { useState } from 'react';
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Link } from 'expo-router';
import { useAuth } from '../../context/auth';
import { useTheme } from '../../context/theme';
import type { ColorScheme } from '../../constants/theme';

export default function SignIn() {
  const { signIn } = useAuth();
  const { colors } = useTheme();
  const styles = makeStyles(colors);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSignIn = async () => {
    setError(null);
    setLoading(true);
    const { error } = await signIn(email, password);
    if (error) setError(error);
    setLoading(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Collector</Text>
      <Text style={styles.subtitle}>Sign in to your account</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        placeholderTextColor={colors.subtext}
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor={colors.subtext}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      {error && <Text style={styles.error}>{error}</Text>}

      <TouchableOpacity style={styles.button} onPress={handleSignIn} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? 'Signing in...' : 'Sign In'}</Text>
      </TouchableOpacity>

      <Link href="/(auth)/forgot-password" style={styles.forgotLink}>
        Forgot password?
      </Link>

      <Link href="/(auth)/sign-up" style={styles.link}>
        Don't have an account? Sign up
      </Link>
    </View>
  );
}

function makeStyles(c: ColorScheme) {
  return StyleSheet.create({
    container: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: c.background, padding: 24 },
    title: { fontSize: 36, fontWeight: 'bold', color: c.accent, marginBottom: 8 },
    subtitle: { fontSize: 14, color: c.subtext, marginBottom: 32 },
    input: {
      width: '100%',
      backgroundColor: c.surface,
      color: c.text,
      borderWidth: 1,
      borderColor: c.border,
      borderRadius: 8,
      padding: 14,
      marginBottom: 12,
      fontSize: 16,
    },
    button: { width: '100%', backgroundColor: c.accent, borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 8 },
    buttonText: { color: c.background, fontSize: 16, fontWeight: '700' },
    error: { color: c.negative, fontSize: 14, marginBottom: 8 },
    forgotLink: { color: c.subtext, marginTop: 12, fontSize: 14, alignSelf: 'flex-end' },
    link: { color: c.accent, marginTop: 24, fontSize: 14 },
  });
}
