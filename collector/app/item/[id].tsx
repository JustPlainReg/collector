import { useEffect, useState } from 'react';
import {
  StyleSheet, Text, View, ScrollView, TouchableOpacity,
  ActivityIndicator, Dimensions, Modal, TextInput, Alert, Image,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { LineChart } from 'react-native-chart-kit';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../context/auth';
import { colors } from '../../constants/theme';

const SCREEN_WIDTH = Dimensions.get('window').width;

type Item = {
  id: string;
  name: string;
  brand: string | null;
  image_url: string | null;
  categories: { name: string } | null;
};

type Variant = {
  id: string;
  variant_type: string;
  variant_value: string;
  grader: string | null;
};

type PricePoint = {
  sold_price: number;
  sold_at: string;
};

type PriceSummary = {
  est_value: number;
  num_sales: number;
  price_low: number;
  price_high: number;
};

function variantLabel(v: Variant): string {
  return v.grader ? `${v.grader} ${v.variant_value}` : v.variant_value;
}

export default function ItemDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { session } = useAuth();

  const [item, setItem] = useState<Item | null>(null);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);
  const [summary, setSummary] = useState<PriceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [priceLoading, setPriceLoading] = useState(false);

  const [alreadyOwned, setAlreadyOwned] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [purchasePrice, setPurchasePrice] = useState('');
  const [adding, setAdding] = useState(false);

  // Load item + variants once
  useEffect(() => {
    async function load() {
      const [itemRes, variantRes] = await Promise.all([
        supabase
          .from('items')
          .select('id, name, brand, image_url, categories(name)')
          .eq('id', id)
          .single(),
        supabase
          .from('item_variants')
          .select('id, variant_type, variant_value, grader')
          .eq('item_id', id)
          .order('variant_type')
          .order('variant_value'),
      ]);

      setItem(itemRes.data as unknown as Item);
      setVariants(variantRes.data ?? []);
      setLoading(false);
    }
    load();
  }, [id]);

  // Reload prices + ownership whenever variant selection changes
  useEffect(() => {
    if (loading) return;
    loadPrices();
    checkOwnership();
  }, [selectedVariant, loading]);

  async function checkOwnership() {
    if (!session) return;
    let q = supabase
      .from('portfolio_items')
      .select('id')
      .eq('user_id', session.user.id)
      .eq('item_id', id);
    if (selectedVariant) q = q.eq('variant_id', selectedVariant.id);
    else q = q.is('variant_id', null);
    const { data } = await q.limit(1);
    setAlreadyOwned((data ?? []).length > 0);
  }

  async function loadPrices() {
    setPriceLoading(true);

    let historyQuery = supabase
      .from('price_history')
      .select('sold_price, sold_at')
      .eq('item_id', id)
      .order('sold_at', { ascending: true })
      .limit(30);

    let summaryQuery = supabase
      .from('current_prices')
      .select('*')
      .eq('item_id', id);

    if (selectedVariant) {
      historyQuery = historyQuery.eq('variant_id', selectedVariant.id);
      summaryQuery = summaryQuery.eq('variant_id', selectedVariant.id);
    }

    const [historyRes, summaryRes] = await Promise.all([historyQuery, summaryQuery]);

    setPriceHistory(historyRes.data ?? []);

    const rows = summaryRes.data ?? [];
    if (rows.length > 0) {
      const totalSales = rows.reduce((s: number, r: any) => s + Number(r.num_sales), 0);
      const allLow = Math.min(...rows.map((r: any) => Number(r.price_low)));
      const allHigh = Math.max(...rows.map((r: any) => Number(r.price_high)));
      const avgValue = rows.reduce((s: number, r: any) => s + Number(r.est_value), 0) / rows.length;
      setSummary({ est_value: avgValue, num_sales: totalSales, price_low: allLow, price_high: allHigh });
    } else {
      setSummary(null);
    }

    setPriceLoading(false);
  }

  const handleAddToPortfolio = async () => {
    if (!session) return;
    setAdding(true);

    const { error } = await supabase.from('portfolio_items').insert({
      user_id: session.user.id,
      item_id: id,
      variant_id: selectedVariant?.id ?? null,
      purchase_price: purchasePrice ? parseFloat(purchasePrice) : null,
      purchase_date: new Date().toISOString().split('T')[0],
    });

    setAdding(false);
    setModalVisible(false);
    setPurchasePrice('');

    if (error) {
      Alert.alert('Error', error.message);
    } else {
      const label = selectedVariant ? ` (${variantLabel(selectedVariant)})` : '';
      Alert.alert('Added!', `${item?.name}${label} added to your portfolio.`);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  if (!item) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Item not found</Text>
      </View>
    );
  }

  const chartData = priceHistory.map((p) => p.sold_price);
  const uniqueDates = new Set(priceHistory.map((p) => p.sold_at.slice(0, 10)));
  const hasRealHistory = uniqueDates.size > 1;
  const step = Math.ceil(Math.max(priceHistory.length, 1) / 6);
  const chartLabels = priceHistory
    .filter((_, i) => i % step === 0)
    .map((_, i) => new Date(priceHistory[i * step].sold_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

  return (
    <>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          {item.image_url && (
            <Image source={{ uri: item.image_url }} style={styles.itemImage} resizeMode="contain" />
          )}
          <Text style={styles.category}>{(item.categories as any)?.name ?? ''}</Text>
          <Text style={styles.name}>{item.name}</Text>
          {item.brand && <Text style={styles.brand}>{item.brand}</Text>}
        </View>

        {/* Variant Selector */}
        {variants.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.variantRow}
          >
            <TouchableOpacity
              style={[styles.variantPill, !selectedVariant && styles.variantPillActive]}
              onPress={() => setSelectedVariant(null)}
            >
              <Text style={[styles.variantPillText, !selectedVariant && styles.variantPillTextActive]}>
                All
              </Text>
            </TouchableOpacity>
            {variants.map((v) => {
              const active = selectedVariant?.id === v.id;
              return (
                <TouchableOpacity
                  key={v.id}
                  style={[styles.variantPill, active && styles.variantPillActive]}
                  onPress={() => setSelectedVariant(v)}
                >
                  <Text style={[styles.variantPillText, active && styles.variantPillTextActive]}>
                    {variantLabel(v)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        )}

        {/* Price Summary */}
        {priceLoading ? (
          <View style={styles.summaryCard}>
            <ActivityIndicator color={colors.accent} />
          </View>
        ) : summary ? (
          <View style={styles.summaryCard}>
            <View style={styles.summaryMain}>
              <Text style={styles.estLabel}>EST. VALUE</Text>
              <Text style={styles.estValue}>${Number(summary.est_value).toLocaleString(undefined, { maximumFractionDigits: 0 })}</Text>
            </View>
            <View style={styles.summaryStats}>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>SALES</Text>
                <Text style={styles.statValue}>{summary.num_sales}</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>LOW</Text>
                <Text style={styles.statValue}>${Number(summary.price_low).toLocaleString(undefined, { maximumFractionDigits: 0 })}</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>HIGH</Text>
                <Text style={styles.statValue}>${Number(summary.price_high).toLocaleString(undefined, { maximumFractionDigits: 0 })}</Text>
              </View>
            </View>
          </View>
        ) : (
          <View style={styles.summaryCard}>
            <Text style={styles.noData}>No recent sales data available</Text>
          </View>
        )}

        {/* Price Chart */}
        {chartData.length > 1 && hasRealHistory && (
          <View style={styles.chartSection}>
            <Text style={styles.sectionTitle}>Price History</Text>
            <LineChart
              data={{ labels: chartLabels, datasets: [{ data: chartData }] }}
              width={SCREEN_WIDTH - 32}
              height={200}
              chartConfig={{
                backgroundColor: colors.surface,
                backgroundGradientFrom: colors.surface,
                backgroundGradientTo: colors.surface,
                decimalPlaces: 0,
                color: () => colors.accent,
                labelColor: () => colors.subtext,
                propsForDots: { r: '3', fill: colors.accent },
                propsForBackgroundLines: { stroke: colors.border },
              }}
              bezier
              style={styles.chart}
              withInnerLines={true}
              withOuterLines={false}
            />
          </View>
        )}

        <TouchableOpacity style={[styles.addButton, alreadyOwned && styles.addButtonOwned]} onPress={() => setModalVisible(true)}>
          <Text style={styles.addButtonText}>
            {alreadyOwned
              ? `✓ In Portfolio · Add Another${selectedVariant ? ` ${variantLabel(selectedVariant)}` : ''}`
              : `+ Add${selectedVariant ? ` ${variantLabel(selectedVariant)}` : ''} to Portfolio`}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Add to Portfolio Modal */}
      <Modal visible={modalVisible} transparent animationType="slide" onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <Text style={styles.modalTitle}>Add to Portfolio</Text>
            <Text style={styles.modalSubtitle}>
              {item.name}{selectedVariant ? ` · ${variantLabel(selectedVariant)}` : ''}
            </Text>

            <Text style={styles.inputLabel}>Purchase Price (optional)</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. 1800"
              placeholderTextColor={colors.subtext}
              value={purchasePrice}
              onChangeText={setPurchasePrice}
              keyboardType="decimal-pad"
            />

            <TouchableOpacity style={styles.confirmButton} onPress={handleAddToPortfolio} disabled={adding}>
              <Text style={styles.confirmButtonText}>{adding ? 'Adding...' : 'Add to Portfolio'}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.cancelButton} onPress={() => setModalVisible(false)}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 16, paddingBottom: 40 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  errorText: { color: colors.subtext, fontSize: 16 },
  header: { marginBottom: 20, alignItems: 'center' },
  itemImage: { width: 220, height: 300, marginBottom: 16 },
  category: { color: colors.accent, fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 },
  name: { color: colors.text, fontSize: 22, fontWeight: 'bold', marginBottom: 4, textAlign: 'center' },
  brand: { color: colors.subtext, fontSize: 14 },
  variantRow: { flexDirection: 'row', gap: 8, paddingBottom: 16 },
  variantPill: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  variantPillActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  variantPillText: { color: colors.subtext, fontSize: 13, fontWeight: '600' },
  variantPillTextActive: { color: colors.background },
  summaryCard: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 16, marginBottom: 24, minHeight: 80, justifyContent: 'center' },
  summaryMain: { marginBottom: 16 },
  estLabel: { color: colors.subtext, fontSize: 11, fontWeight: '600', letterSpacing: 1, marginBottom: 4 },
  estValue: { color: colors.accent, fontSize: 36, fontWeight: 'bold' },
  summaryStats: { flexDirection: 'row', justifyContent: 'space-between' },
  stat: { alignItems: 'center' },
  statLabel: { color: colors.subtext, fontSize: 11, fontWeight: '600', letterSpacing: 1, marginBottom: 4 },
  statValue: { color: colors.text, fontSize: 16, fontWeight: '600' },
  noData: { color: colors.subtext, fontSize: 14, textAlign: 'center', paddingVertical: 8 },
  chartSection: { marginBottom: 24 },
  sectionTitle: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 12 },
  chart: { borderRadius: 12 },
  addButton: { backgroundColor: colors.accent, borderRadius: 10, padding: 16, alignItems: 'center' },
  addButtonOwned: { backgroundColor: colors.accentDark },
  addButtonText: { color: colors.background, fontSize: 16, fontWeight: '700' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalSheet: { backgroundColor: colors.surface, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 24, paddingBottom: 40 },
  modalTitle: { color: colors.text, fontSize: 20, fontWeight: 'bold', marginBottom: 4 },
  modalSubtitle: { color: colors.subtext, fontSize: 14, marginBottom: 24 },
  inputLabel: { color: colors.subtext, fontSize: 12, fontWeight: '600', letterSpacing: 1, marginBottom: 8 },
  modalInput: { backgroundColor: colors.background, color: colors.text, borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 14, fontSize: 16, marginBottom: 16 },
  confirmButton: { backgroundColor: colors.accent, borderRadius: 10, padding: 16, alignItems: 'center', marginBottom: 12 },
  confirmButtonText: { color: colors.background, fontSize: 16, fontWeight: '700' },
  cancelButton: { alignItems: 'center', padding: 12 },
  cancelButtonText: { color: colors.subtext, fontSize: 15 },
});
