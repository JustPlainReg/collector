import { useState, useCallback } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, ActivityIndicator, Alert, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useFocusEffect, useRouter } from 'expo-router';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../context/auth';
import { useTheme } from '../../context/theme';
import { useCurrency } from '../../context/currency';
import type { ColorScheme } from '../../constants/theme';

const SCREEN_WIDTH = Dimensions.get('window').width;

type Period = '1H' | '1D' | '3D' | '7D';

const PERIODS: Period[] = ['1H', '1D', '3D', '7D'];

const PERIOD_MS: Record<Period, number> = {
  '1H': 60 * 60 * 1000,
  '1D': 24 * 60 * 60 * 1000,
  '3D': 3 * 24 * 60 * 60 * 1000,
  '7D': 7 * 24 * 60 * 60 * 1000,
};

type PortfolioItem = {
  id: string;
  purchase_price: number | null;
  quantity: number;
  items: {
    id: string;
    name: string;
    brand: string | null;
    categories: { name: string }[] | null;
  };
};

type CurrentPrice = {
  item_id: string;
  est_value: number;
};

type Snapshot = {
  snapshot_at: string;
  total_value: number;
};

export default function Portfolio() {
  const { session } = useAuth();
  const { colors } = useTheme();
  const { formatPrice } = useCurrency();
  const router = useRouter();
  const styles = makeStyles(colors);

  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [currentPrices, setCurrentPrices] = useState<Record<string, number>>({});
  const [allSnapshots, setAllSnapshots] = useState<Snapshot[]>([]);
  const [period, setPeriod] = useState<Period>('1D');
  const [loading, setLoading] = useState(true);

  const loadPortfolio = useCallback(async () => {
    if (!session) return;
    setLoading(true);

    const { data: portfolio } = await supabase
      .from('portfolio_items')
      .select('id, purchase_price, quantity, items(id, name, brand, categories(name))')
      .eq('user_id', session.user.id)
      .order('added_at', { ascending: false });

    const items = (portfolio as unknown as PortfolioItem[]) ?? [];
    setPortfolioItems(items);

    if (items.length > 0) {
      const itemIds = items.map((p) => p.items.id);
      const { data: prices } = await supabase
        .from('current_prices')
        .select('item_id, est_value')
        .in('item_id', itemIds);

      const priceMap: Record<string, number> = {};
      const countMap: Record<string, number> = {};
      (prices as CurrentPrice[] ?? []).forEach((p) => {
        priceMap[p.item_id] = (priceMap[p.item_id] ?? 0) + Number(p.est_value);
        countMap[p.item_id] = (countMap[p.item_id] ?? 0) + 1;
      });
      Object.keys(priceMap).forEach((id) => {
        priceMap[id] = priceMap[id] / countMap[id];
      });
      setCurrentPrices(priceMap);
    }

    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
    const { data: snapshotData } = await supabase
      .from('portfolio_snapshots')
      .select('snapshot_at, total_value')
      .eq('user_id', session.user.id)
      .gte('snapshot_at', sevenDaysAgo)
      .order('snapshot_at', { ascending: true });

    setAllSnapshots((snapshotData ?? []) as Snapshot[]);
    setLoading(false);
  }, [session]);

  useFocusEffect(
    useCallback(() => {
      loadPortfolio();
    }, [loadPortfolio])
  );

  const totalValue = portfolioItems.reduce((sum, p) => {
    const price = currentPrices[p.items.id] ?? 0;
    return sum + price * p.quantity;
  }, 0);

  const snapshots = allSnapshots.filter(
    (s) => new Date(s.snapshot_at).getTime() >= Date.now() - PERIOD_MS[period]
  );

  const hasChart = snapshots.length >= 2;
  const chartValues = hasChart ? snapshots.map((s) => Number(s.total_value)) : [];
  const isPositive = hasChart
    ? snapshots[snapshots.length - 1].total_value >= snapshots[0].total_value
    : true;
  const changePercent = hasChart
    ? ((snapshots[snapshots.length - 1].total_value - snapshots[0].total_value) /
        Math.max(snapshots[0].total_value, 0.01)) *
      100
    : null;
  const lineColor = isPositive ? colors.positive : colors.negative;

  const handleRemove = (portfolioItemId: string, itemName: string) => {
    Alert.alert(
      'Remove from Portfolio',
      `Remove ${itemName}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            await supabase.from('portfolio_items').delete().eq('id', portfolioItemId);
            setPortfolioItems((prev) => prev.filter((p) => p.id !== portfolioItemId));
          },
        },
      ]
    );
  };

  const renderItem = ({ item }: { item: PortfolioItem }) => {
    const estValue = currentPrices[item.items.id];
    const gain = item.purchase_price && estValue ? estValue - item.purchase_price : null;

    return (
      <TouchableOpacity
        style={styles.itemRow}
        onPress={() => router.push(`/item/${item.items.id}`)}
        onLongPress={() => handleRemove(item.id, item.items.name)}
      >
        <View style={styles.itemInfo}>
          <Text style={styles.itemCategory}>{item.items.categories?.[0]?.name ?? ''}</Text>
          <Text style={styles.itemName}>{item.items.name}</Text>
          {item.items.brand && <Text style={styles.itemBrand}>{item.items.brand}</Text>}
        </View>
        <View style={styles.itemPricing}>
          <Text style={styles.itemValue}>{formatPrice(estValue)}</Text>
          {gain !== null && (
            <Text style={[styles.itemGain, { color: gain >= 0 ? colors.positive : colors.negative }]}>
              {gain >= 0 ? '+' : ''}{formatPrice(Math.abs(gain))}
            </Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroLabel}>PORTFOLIO VALUE</Text>
        <Text style={styles.heroValue}>{formatPrice(totalValue)}</Text>
        {changePercent !== null && (
          <Text style={[styles.heroChange, { color: lineColor }]}>
            {isPositive ? '▲' : '▼'} {isPositive ? '+' : ''}{changePercent.toFixed(1)}%{' '}
            <Text style={styles.heroChangePeriod}>({period.toLowerCase()})</Text>
          </Text>
        )}
      </View>

      {hasChart && (
        <LineChart
          data={{ labels: chartValues.map(() => ''), datasets: [{ data: chartValues }] }}
          width={SCREEN_WIDTH}
          height={140}
          chartConfig={{
            backgroundGradientFrom: colors.background,
            backgroundGradientTo: colors.background,
            backgroundGradientFromOpacity: 1,
            backgroundGradientToOpacity: 1,
            color: () => lineColor,
            fillShadowGradient: lineColor,
            fillShadowGradientOpacity: 0.15,
            strokeWidth: 2,
            decimalPlaces: 0,
            propsForBackgroundLines: { stroke: 'transparent' },
          }}
          bezier
          withDots={false}
          withInnerLines={false}
          withOuterLines={false}
          withVerticalLabels={false}
          withHorizontalLabels={false}
          style={styles.chart}
        />
      )}

      {allSnapshots.length >= 2 && (
        <View style={styles.periodRow}>
          {PERIODS.map((p) => (
            <TouchableOpacity
              key={p}
              style={[styles.periodBtn, period === p && styles.periodBtnActive]}
              onPress={() => setPeriod(p)}
            >
              <Text style={[styles.periodText, period === p && { color: lineColor }]}>{p}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.divider} />

      {portfolioItems.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyIcon}>📦</Text>
          <Text style={styles.emptyText}>Your portfolio is empty</Text>
          <Text style={styles.emptySubtext}>
            Search for a collectible, tap into it, and hit "Add to Portfolio" to start tracking your collection.
          </Text>
          <TouchableOpacity style={styles.emptyButton} onPress={() => router.push('/(tabs)/search')}>
            <Text style={styles.emptyButtonText}>Browse Collectibles</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={portfolioItems}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

function makeStyles(c: ColorScheme) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: c.background },
    centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: c.background },
    hero: { padding: 24, paddingTop: 32 },
    heroLabel: { color: c.subtext, fontSize: 11, fontWeight: '600', letterSpacing: 1.5, marginBottom: 6 },
    heroValue: { color: c.text, fontSize: 40, fontWeight: 'bold' },
    heroChange: { fontSize: 14, fontWeight: '600', marginTop: 6 },
    heroChangePeriod: { color: c.subtext, fontWeight: '400' },
    chart: { marginLeft: -16, marginTop: 8 },
    periodRow: {
      flexDirection: 'row',
      justifyContent: 'center',
      gap: 4,
      paddingVertical: 10,
      paddingHorizontal: 16,
    },
    periodBtn: {
      paddingHorizontal: 18,
      paddingVertical: 6,
      borderRadius: 16,
    },
    periodBtnActive: { backgroundColor: c.surface },
    periodText: { color: c.subtext, fontSize: 13, fontWeight: '600' },
    divider: { height: 1, backgroundColor: c.border },
    list: { paddingHorizontal: 16, paddingTop: 8 },
    itemRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: 14,
      borderBottomWidth: 1,
      borderBottomColor: c.border,
    },
    itemInfo: { flex: 1, marginRight: 12 },
    itemCategory: { color: c.accent, fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 3 },
    itemName: { color: c.text, fontSize: 15, fontWeight: '600', marginBottom: 2 },
    itemBrand: { color: c.subtext, fontSize: 13 },
    itemPricing: { alignItems: 'flex-end' },
    itemValue: { color: c.text, fontSize: 16, fontWeight: '700' },
    itemGain: { fontSize: 13, marginTop: 2 },
    empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 },
    emptyIcon: { fontSize: 48, marginBottom: 16 },
    emptyText: { color: c.text, fontSize: 18, fontWeight: '600', marginBottom: 8 },
    emptySubtext: { color: c.subtext, fontSize: 14, textAlign: 'center', lineHeight: 20, marginBottom: 24 },
    emptyButton: { backgroundColor: c.accent, borderRadius: 10, paddingHorizontal: 24, paddingVertical: 14 },
    emptyButtonText: { color: c.background, fontSize: 15, fontWeight: '700' },
  });
}
