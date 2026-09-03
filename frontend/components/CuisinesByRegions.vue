<template>
  <div class="bg-white rounded-xl border border-stone-200 shadow-sm">

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
        <div v-if="expandedRegion === region.name" class="relative justify-center items-center p-6">
          <div class="relative w-full h-[400px]">
            <svg
              :viewBox="`0 0 ${outerSize} ${outerSize}`"
              class="w-full max-w-2xl h-auto"
              preserveAspectRatio="xMidYMid meet"
            >
              <!-- Anneau des proportions -->
              <g :transform="`translate(${outerSize / 2}, ${outerSize / 2})`">
                <path
                  v-for="(seg, i) in ringSegments"
                  :key="seg.cuisine_name"
                  :d="seg.path"
                  :fill="getColor(seg.cuisine_name)"
                  :fill-opacity="expandedRegion === region.name ? 1 : 0"
                  class="transition-opacity duration-300 ease-in"
                  stroke="#fcf6ee"
                  stroke-width="25"
                />
              </g>

              <!-- Labels de l'anneau -->
              <g v-if="expandedRegion === region.name" :transform="`translate(${outerSize / 2}, ${outerSize / 2})`">
                <text
                  v-for="seg in ringSegments"
                  :key="`label-${seg.cuisine_name}`"
                  :x="seg.labelPos[0]"
                  :y="seg.labelPos[1]"
                  text-anchor="left"
                  dominant-baseline="middle"
                  class="text-[1.5rem] font-medium fill-stone-700 pointer-events-none"
                >
                  {{seg.cuisine_name}} {{ seg.percent }}%
                </text>
              </g>
            </svg>
          </div>
  <!-- Affichage regions -->  
  <div
    v-for="(region, i) in filteredRegions"
      :key="region.name"
      class="absolute flex items-center gap-3 z-10"
      :style="{ 
        left: `calc(50% + ${Math.cos((i / filteredRegions.length) * 2 * Math.PI - Math.PI / 2) * 400}px)`,
        top: `calc(50% + ${Math.sin((i / filteredRegions.length) * 2 * Math.PI - Math.PI / 2) * 400}px)`,
        transform: `translate(-50%, -50%)`
      }"
      @mouseenter="hoveredRegion = region.name"
      @mouseleave="hoveredRegion = null"
    >
      <div
        class="flex flex-row items-center gap-1 transition-transform duration-200"
        :style="{transform: `rotate(${getRegionRotation(i, filteredRegions.length)}deg)`}">
        <span 
          class="text-sm text-stone-600 truncate shrink-0 text-center px-2 bg-white rounded-full mx-3"
          :style="{ transform: i > filteredRegions.length / 2 ? 'rotate(180deg)': ''}"
        >
          {{ region.name }}
        </span>
      </div>
    </div>

  <!-- Affichage des images des cuisines et leur position dans la region -->
  <div
    v-for="(cuisine, i) in region.cuisines"
    :key="cuisine.cuisine_name"
    class="absolute flex items-center gap-3 z-10"
    :style="{ 
      left: `calc(50% + ${Math.cos((i / region.cuisines.length) * 2 * Math.PI - Math.PI / 2) * 200}px)`,
      top: `calc(50% + ${Math.sin((i / region.cuisines.length) * 2 * Math.PI - Math.PI / 2) * 200}px)`,
      transform: `translate(-50%, -50%)`
    }"
    @mouseenter="hoveredCuisine = cuisine.cuisine_name"
    @mouseleave="hoveredCuisine = null"
  >
    <div
      class="flex flex-row items-center gap-1 transition-transform duration-200"
      :style="{transform: `rotate(${getCuisineRotation(i, region.cuisines.length)}deg)`}">
      <img
        :src="getSvg(cuisine.cuisine_name)"
        alt=""
        :width="getImageSize(cuisine.interest_score)"
      />
      <span 
        class="text-sm text-stone-600 truncate shrink-0 text-center px-2 bg-white rounded-full mx-3"
        :style="{ transform: i > region.cuisines.length / 2 ? 'rotate(180deg)': ''}"
      >
        {{ i+1 }}
      </span>
    </div>


  </div>
      <!-- Nom de la région au centre --> 
    <span 
      class="absolute inset-0 flex items-center 
      justify-center text-lg font-semibold 
      text-stone-700"
    >
      {{ hoveredCuisine ?? expandedRegion }}
    </span>
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
const expandedRegion = ref('Île-de-France') // Par défaut, on ouvre la région de Ile-de-France
const rawData = ref({})
const hoveredCuisine = ref(null)

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

const getCirclePosition = (index, total, centerX, centerY, radius) => {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2

  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle)
  }
}

function getCuisineRotation(i, total) {
  const angle = (i / total) * 360 - 90
  return angle
}

function getRegionRotation(i, total) {
  const angle = (i / total) * 360 - 90
  const isLeft = angle > 90
  return isLeft ? angle :  angle
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