import { useEffect, useState } from 'react';
import {
  StyleSheet, Text, View, TextInput,
  FlatList, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { supabase } from '../../lib/supabase';
import { colors } from '../../constants/theme';

type Category = {
  id: string;
  name: string;
  slug: string;
};

type Item = {
  id: string;
  name: string;
  brand: string | null;
  categories: { name: string }[] | null;
};

export default function Search() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [results, setResults] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);

  useEffect(() => {
    supabase
      .from('categories')
      .select('*')
      .then(({ data }) => setCategories(data ?? []));
  }, []);

  // Load first 50 items when a category is selected (and no search query)
  useEffect(() => {
    if (!selectedCategory || query.trim()) return;

    setLoading(true);
    supabase
      .from('items')
      .select('id, name, brand, categories(name)')
      .eq('category_id', selectedCategory.id)
      .order('name')
      .limit(50)
      .then(({ data }) => {
        setResults((data as Item[]) ?? []);
        setLoading(false);
      });
  }, [selectedCategory]);

  // Debounced search — scoped to category if one is selected
  useEffect(() => {
    if (!query.trim()) {
      if (!selectedCategory) setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      let q = supabase
        .from('items')
        .select('id, name, brand, categories(name)')
        .ilike('name', `%${query}%`)
        .limit(30);

      if (selectedCategory) {
        q = q.eq('category_id', selectedCategory.id);
      }

      const { data } = await q;
      setResults((data as Item[]) ?? []);
      setLoading(false);
    }, 400);

    return () => clearTimeout(timer);
  }, [query, selectedCategory]);

  const handleSelectCategory = (cat: Category) => {
    setSelectedCategory(cat);
    setQuery('');
    setResults([]);
  };

  const handleClearCategory = () => {
    setSelectedCategory(null);
    setQuery('');
    setResults([]);
  };

  const showCategories = !selectedCategory && !query.trim();

  return (
    <View style={styles.container}>
      {/* Category filter pill */}
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

      {showCategories ? (
        <>
          <Text style={styles.sectionLabel}>Browse by Category</Text>
          <FlatList
            data={categories}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.categoryCard}
                onPress={() => handleSelectCategory(item)}
              >
                <Text style={styles.categoryName}>{item.name}</Text>
              </TouchableOpacity>
            )}
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
          data={results}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.resultRow}
              onPress={() => router.push(`/item/${item.id}`)}
            >
              <Text style={styles.resultName}>{item.name}</Text>
              <Text style={styles.resultMeta}>
                {item.brand ?? ''}
                {item.brand && item.categories?.[0]?.name ? '  ·  ' : ''}
                {item.categories?.[0]?.name ?? ''}
              </Text>
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingTop: 16,
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  filterPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.accentDark,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  filterPillText: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '600',
    marginRight: 8,
  },
  filterClear: {
    padding: 2,
  },
  filterClearText: {
    color: colors.text,
    fontSize: 12,
  },
  searchInput: {
    marginHorizontal: 16,
    backgroundColor: colors.surface,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  sectionLabel: {
    color: colors.subtext,
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
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryName: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
  list: { paddingHorizontal: 16 },
  resultRow: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  resultName: { color: colors.text, fontSize: 15, fontWeight: '500' },
  resultMeta: { color: colors.subtext, fontSize: 13, marginTop: 3 },
  spinner: { marginTop: 40 },
  empty: { alignItems: 'center', marginTop: 60, paddingHorizontal: 32 },
  emptyText: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 8 },
  emptySubtext: { color: colors.subtext, fontSize: 14, textAlign: 'center' },
  footerHint: { color: colors.subtext, fontSize: 12, textAlign: 'center', padding: 16 },
});
