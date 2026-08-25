<template>
  <div class="bg-white rounded-xl border border-stone-200 shadow-sm">
    <!-- Barre de recherche -->
    <div class="p-4 border-b border-stone-100">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher une région..."
        class="w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
      />
    </div>

    <!-- Liste des régions -->
    <div class="divide-y divide-stone-100 max-h-[700px] overflow-y-auto">
      <div v-for="region in filteredRegions" :key="region.name">
        <!-- En-tête région (cliquable) -->
        <button
          @click="toggleRegion(region.name)"
          class="w-full flex items-center justify-between px-5 py-3 hover:bg-stone-50 transition-colors text-left"
        >
          <div class="flex items-center gap-3">
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: getColor(region.cuisines[0]?.cuisine_name) }"
            />
            <span class="font-medium text-stone-800">{{ region.name }}</span>
            <span class="text-xs text-stone-400">{{ region.cuisines.length }} cuisines</span>
          </div>
          <svg
            class="w-4 h-4 text-stone-400 transition-transform duration-200"
            :class="{ 'rotate-180': expandedRegion === region.name }"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Détail déplié -->
        <div v-if="expandedRegion === region.name" class="px-5 pb-4 space-y-2">
          <div
            v-for="cuisine in region.cuisines"
            :key="cuisine.cuisine_name"
            class="flex items-center gap-3"
          >
            <!-- Affichage de l'image de la cuisine et son nom -->
            <img
              :src="getSvg(cuisine.cuisine_name)"
              alt=""
              :width=" getImageSize(cuisine.interest_score) "/>
            <span class="text-sm text-stone-600 w-40 truncate shrink-0">
              {{ cuisine.cuisine_name }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="filteredRegions.length === 0" class="p-8 text-center text-stone-400 text-sm">
        Aucune région trouvée
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const searchQuery = ref('')
const expandedRegion = ref(null)
const rawData = ref({})

const { getAllCuisinesPerRegion } = useApi()

const CUISINE_COLORS = {
  'Pizza': '#e07856',
  'Sushi': '#4a7c8c',
  'Kebab': '#c9a227',
  'Hamburger': '#a4443c',
  'Taco': '#6b8e4e',
  'restaurant vegetarien': '#d1495b',
  'restaurant chinois': '#e8a33d',
  'bar': '#5c6b73',
  'café': '#8d6a4a',
  'glace': '#DD5F89',
}
const FALLBACK_COLOR = '#a3a3a3'
const getColor = (cuisine) => CUISINE_COLORS[cuisine] || FALLBACK_COLOR

const CUISINE_SVG = {
  'Pizza': '/cuisines/pizza.svg',
  'Sushi': '/cuisines/food-sushi-roll.svg',
  'Kebab': '/cuisines/food-taco.svg',
  'Hamburger': '/cuisines/food-burger.svg',
  'Taco': '/cuisines/food-taco.svg',
  'restaurant vegetarien': '/cuisines/food2-avocado.svg',
  'restaurant chinois': '/cuisines/food-chopsticks-bowl.svg',
  'bar': '/cuisines/food-taco.svg',
  'café': '/cuisines/food-coffee-cup.svg',
  'glace': '/cuisines/food-ice-cream.svg',
  'crêperie': '/cuisines/food2-pancakes.svg',
}

const FALLBACK_SVG = '/cuisines/food2-steak.svg'

const getSvg = (cuisine) => CUISINE_SVG[cuisine] || FALLBACK_SVG

const getImageSize = (score) => {
  const minSize = 30
  const maxSize = 100

  return minSize + (score / 50) * (maxSize - minSize)
}

const regions = computed(() => {
  return Object.entries(rawData.value)
    .map(([name, cuisines]) => ({ name, cuisines }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const filteredRegions = computed(() => {
  if (!searchQuery.value.trim()) return regions.value
  const q = searchQuery.value.toLowerCase()
  return regions.value.filter(r => r.name.toLowerCase().includes(q))
})

function toggleRegion(name) {
  expandedRegion.value = expandedRegion.value === name ? null : name
}

onMounted(async () => {
  rawData.value = await getAllCuisinesPerRegion(7)
  // Ouvre la première région par défaut pour montrer que ça fonctionne
  if (regions.value.length > 0) {
    expandedRegion.value = regions.value[0].name
  }
})
</script>