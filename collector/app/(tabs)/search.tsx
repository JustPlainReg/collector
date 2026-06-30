import { useEffect, useState } from 'react';
import {
  StyleSheet, Text, View, TextInput,
  FlatList, TouchableOpacity, ActivityIndicator, Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { supabase } from '../../lib/supabase';
import { useTheme } from '../../context/theme';
import { useCurrency } from '../../context/currency';
import type { ColorScheme } from '../../constants/theme';

type Category = {
  id: string;
  name: string;
  slug: string;
};

type Item = {
  id: string;
  name: string;
  brand: string | null;
  image_url: string | null;
  categories: { name: string }[] | null;
};

type SortOption = 'name_asc' | 'name_desc' | 'price_asc' | 'price_desc';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'name_asc', label: 'A–Z' },
  { value: 'name_desc', label: 'Z–A' },
  { value: 'price_asc', label: '$ Low' },
  { value: 'price_desc', label: '$ High' },
];

const CATEGORY_EMOJI: Record<string, string> = {
  'pokemon-cards': '🃏',
  'sports-cards': '⚾',
  'sneakers': '👟',
  'video-games': '🎮',
  'figures-toys': '🤖',
  'comics': '📚',
};

export default function Search() {
  const router = useRouter();
  const { colors } = useTheme();
  const { formatPrice } = useCurrency();
  const styles = makeStyles(colors);

  const [query, setQuery] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [results, setResults] = useState<Item[]>([]);
  const [priceMap, setPriceMap] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('name_asc');

  useEffect(() => {
    supabase
      .from('categories')
      .select('*')
      .then(({ data }) => setCategories(data ?? []));
  }, []);

  useEffect(() => {
    if (!selectedCategory || query.trim()) return;

    setLoading(true);
    supabase
      .from('items')
      .select('id, name, brand, image_url, categories(name)')
      .eq('category_id', selectedCategory.id)
      .order('name')
      .limit(50)
      .then(async ({ data }) => {
        const items = (data as Item[]) ?? [];
        setResults(items);
        await fetchPrices(items);
        setLoading(false);
      });
  }, [selectedCategory]);

  useEffect(() => {
    if (!query.trim()) {
      if (!selectedCategory) setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);

      const words = query.trim().split(/\s+/).filter((w) => w.length > 0);
      let q = supabase
        .from('items')
        .select('id, name, brand, image_url, categories(name)');

      for (const word of words) {
        q = q.ilike('name', `%${word}%`);
      }

      if (selectedCategory) {
        q = q.eq('category_id', selectedCategory.id);
      }

      const { data } = await q.limit(30);
      const items = (data as Item[]) ?? [];
      setResults(items);
      await fetchPrices(items);
      setLoading(false);
    }, 400);

    return () => clearTimeout(timer);
  }, [query, selectedCategory]);

  async function fetchPrices(items: Item[]) {
    if (items.length === 0) { setPriceMap({}); return; }
    const ids = items.map((i) => i.id);
    const { data } = await supabase
      .from('current_prices')
      .select('item_id, est_value')
      .in('item_id', ids);
    const map: Record<string, number> = {};
    (data ?? []).forEach((p: any) => {
      if (!map[p.item_id]) map[p.item_id] = Number(p.est_value);
    });
    setPriceMap(map);
  }

  const handleSelectCategory = (cat: Category) => {
    setSelectedCategory(cat);
    setQuery('');
    setResults([]);
    setPriceMap({});
  };

  const handleClearCategory = () => {
    setSelectedCategory(null);
    setQuery('');
    setResults([]);
    setPriceMap({});
  };

  const sortedResults = [...results].sort((a, b) => {
    if (sortBy === 'name_asc') return a.name.localeCompare(b.name);
    if (sortBy === 'name_desc') return b.name.localeCompare(a.name);
    if (sortBy === 'price_asc') return (priceMap[a.id] ?? 0) - (priceMap[b.id] ?? 0);
    if (sortBy === 'price_desc') return (priceMap[b.id] ?? 0) - (priceMap[a.id] ?? 0);
    return 0;
  });

  const showCategories = !selectedCategory && !query.trim();
  const showResults = !showCategories && !loading && results.length > 0;

  const categoryData = categories.length % 2 !== 0
    ? [...categories, { id: '__spacer__', name: '', slug: '' }]
    : categories;

  return (
    <View style={styles.container}>
      {selectedCategory && (
        <View style={styles.filterRow}>
          <View style={styles.filterPill}>
            <Text style={styles.filterPillText}>{selectedCategory.name}</Text>
            <TouchableOpacity onPress={handleClearCategory} style={styles.filterClear}>
              <Text style={styles.filterClearText}>✕</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <TextInput
        style={styles.searchInput}
        placeholder={selectedCategory ? `Search ${selectedCategory.name}...` : 'Search collectibles...'}
        placeholderTextColor={colors.subtext}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
        clearButtonMode="while-editing"
      />

      {showResults && (
        <View style={styles.sortRow}>
          {SORT_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.value}
              style={[styles.sortPill, sortBy === opt.value && styles.sortPillActive]}
              onPress={() => setSortBy(opt.value)}
            >
              <Text style={[styles.sortPillText, sortBy === opt.value && styles.sortPillTextActive]}>
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {showCategories ? (
        <>
          <Text style={styles.sectionLabel}>Browse by Category</Text>
          <FlatList
            data={categoryData}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => {
              if (item.id === '__spacer__') {
                return <View style={[styles.categoryCard, styles.categoryCardSpacer]} />;
              }
              const emoji = CATEGORY_EMOJI[item.slug] ?? '📦';
              return (
                <TouchableOpacity
                  style={styles.categoryCard}
                  onPress={() => handleSelectCategory(item)}
                >
                  <Text style={styles.categoryEmoji}>{emoji}</Text>
                  <Text style={styles.categoryName}>{item.name}</Text>
                </TouchableOpacity>
              );
            }}
            numColumns={2}
            columnWrapperStyle={styles.row}
            contentContainerStyle={styles.grid}
          />
        </>
      ) : loading ? (
        <ActivityIndicator color={colors.accent} style={styles.spinner} />
      ) : results.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No results</Text>
          <Text style={styles.emptySubtext}>
            {query.trim()
              ? `Nothing matched "${query}"${selectedCategory ? ` in ${selectedCategory.name}` : ''}.`
              : 'No items in this category yet.'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={sortedResults}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.resultRow}
              onPress={() => router.push(`/item/${item.id}`)}
            >
              {item.image_url ? (
                <Image source={{ uri: item.image_url }} style={styles.resultImage} resizeMode="cover" />
              ) : (
                <View style={styles.resultImagePlaceholder} />
              )}
              <View style={styles.resultInfo}>
                <Text style={styles.resultName} numberOfLines={2}>{item.name}</Text>
                <Text style={styles.resultMeta}>
                  {item.brand ?? ''}
                  {item.brand && item.categories?.[0]?.name ? '  ·  ' : ''}
                  {item.categories?.[0]?.name ?? ''}
                </Text>
              </View>
              {priceMap[item.id] != null && (
                <Text style={styles.resultPrice}>{formatPrice(priceMap[item.id])}</Text>
              )}
            </TouchableOpacity>
          )}
          contentContainerStyle={styles.list}
          ListFooterComponent={
            results.length >= 30 ? (
              <Text style={styles.footerHint}>Showing top {results.length} results — refine your search to narrow down</Text>
            ) : null
          }
        />
      )}
    </View>
  );
}

function makeStyles(c: ColorScheme) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: c.background, paddingTop: 16 },
    filterRow: { flexDirection: 'row', paddingHorizontal: 16, marginBottom: 10 },
    filterPill: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: c.accentDark,
      borderRadius: 20,
      paddingHorizontal: 12,
      paddingVertical: 6,
    },
    filterPillText: { color: c.text, fontSize: 13, fontWeight: '600', marginRight: 8 },
    filterClear: { padding: 2 },
    filterClearText: { color: c.text, fontSize: 12 },
    searchInput: {
      marginHorizontal: 16,
      backgroundColor: c.surface,
      color: c.text,
      borderWidth: 1,
      borderColor: c.border,
      borderRadius: 8,
      padding: 12,
      fontSize: 16,
      marginBottom: 12,
    },
    sortRow: {
      flexDirection: 'row',
      gap: 8,
      paddingHorizontal: 16,
      marginBottom: 12,
    },
    sortPill: {
      paddingHorizontal: 14,
      paddingVertical: 6,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: c.border,
      backgroundColor: c.surface,
    },
    sortPillActive: { backgroundColor: c.accent, borderColor: c.accent },
    sortPillText: { color: c.subtext, fontSize: 13, fontWeight: '600' },
    sortPillTextActive: { color: '#ffffff' },
    sectionLabel: {
      color: c.subtext,
      fontSize: 12,
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: 1,
      marginHorizontal: 16,
      marginBottom: 12,
    },
    grid: { paddingHorizontal: 16 },
    row: { justifyContent: 'space-between', marginBottom: 12 },
    categoryCard: {
      flex: 0.48,
      backgroundColor: c.surface,
      borderWidth: 1,
      borderColor: c.border,
      borderRadius: 10,
      padding: 20,
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 90,
    },
    categoryCardSpacer: {
      backgroundColor: 'transparent',
      borderColor: 'transparent',
    },
    categoryEmoji: { fontSize: 28, marginBottom: 8 },
    categoryName: { color: c.text, fontSize: 14, fontWeight: '600', textAlign: 'center' },
    list: { paddingHorizontal: 16 },
    resultRow: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: c.border,
      gap: 12,
    },
    resultImage: {
      width: 52,
      height: 52,
      borderRadius: 8,
      backgroundColor: c.surface,
    },
    resultImagePlaceholder: {
      width: 52,
      height: 52,
      borderRadius: 8,
      backgroundColor: c.surface,
      borderWidth: 1,
      borderColor: c.border,
    },
    resultInfo: { flex: 1 },
    resultName: { color: c.text, fontSize: 15, fontWeight: '500', marginBottom: 3 },
    resultMeta: { color: c.subtext, fontSize: 13 },
    resultPrice: { color: c.text, fontSize: 14, fontWeight: '700' },
    spinner: { marginTop: 40 },
    empty: { alignItems: 'center', marginTop: 60, paddingHorizontal: 32 },
    emptyText: { color: c.text, fontSize: 16, fontWeight: '600', marginBottom: 8 },
    emptySubtext: { color: c.subtext, fontSize: 14, textAlign: 'center' },
    footerHint: { color: c.subtext, fontSize: 12, textAlign: 'center', padding: 16 },
  });
}
