<template>
  <div class="flex flex-col md:flex-row gap-4">
    <!-- Carte SVG statique -->
    <div class="relative flex-1 bg-white rounded-xl border border-stone-200 p-4">
      <svg
        ref="svgRef"
        :viewBox="`0 0 ${width} ${height}`"
        class="w-full h-auto"
        preserveAspectRatio="xMidYMid meet"
      >
        <path
          v-for="feature in features"
          :key="feature.properties.nom"
          :d="pathGenerator(feature)"
          :fill="getTopCuisineColor(feature.properties.nom)"
          :fill-opacity="hoveredRegion === feature.properties.nom ? 1 : 0.8"
          stroke="#fff"
          stroke-width="1.5"
          class="cursor-pointer transition-all duration-150"
          @mouseenter="hoveredRegion = feature.properties.nom; selectedRegion = feature.properties.nom"
          @mouseleave="hoveredRegion = null"
          @click="selectedRegion = feature.properties.nom"
        />
      </svg>
    </div>

    <!-- Panneau latéral -->
    <div class="w-full md:w-80 shrink-0">
      <div class="bg-white rounded-xl border border-stone-200 shadow-sm p-5 sticky top-4 min-h-[300px]">
        <div v-if="!selectedRegion" class="text-stone-400 text-sm flex flex-col items-center justify-center h-full py-16 text-center">
          <span class="text-3xl mb-2">🗺️</span>
          Survolez ou cliquez sur une région pour voir ses tendances culinaires
        </div>

        <div v-else>
          <p class="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-1">Région</p>
          <h2 class="text-xl font-bold text-stone-800 mb-4">{{ selectedRegion }}</h2>

          <div v-if="!selectedTop3 || selectedTop3.length === 0" class="text-stone-400 text-sm">
            Pas de donnée disponible pour cette région
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="item in selectedTop3"
              :key="item.cuisine_name"
              class="flex items-center gap-3 p-3 rounded-lg"
              :style="{ backgroundColor: getColor(item.cuisine_name) + '15' }"
            >
              <span
                class="flex items-center justify-center w-7 h-7 rounded-full text-white text-sm font-bold shrink-0"
                :style="{ backgroundColor: getColor(item.cuisine_name) }"
              >
                {{ item.rank }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="font-medium text-stone-800 truncate">{{ item.cuisine_name }}</p>
                <p class="text-xs text-stone-500">score {{ item.interest_score.toFixed(1) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  top3ByRegion: {
    type: Object,
    default: () => ({})
  }
})

const width = 700
const height = 700

const features = ref([])
const hoveredRegion = ref(null)
const selectedRegion = ref(null)

const CUISINE_COLORS = {
  'Pizza': '#e07856',
  'Sushi': '#4a7c8c',
  'Kebab': '#c9a227',
  'Hamburger': '#a4443c',
  'Taco': '#6b8e4e',
  'restaurant italien': '#d1495b',
  'restaurant chinois': '#e8a33d',
  'restaurant mexicain': '#3d8361',
  'restaurant indien': '#f2994a',
  'bar': '#5c6b73',
  'café': '#8d6a4a',
}
const FALLBACK_COLOR = '#e5e5e5'
const getColor = (cuisine) => CUISINE_COLORS[cuisine] || FALLBACK_COLOR

const normalizeName = (str) =>
  str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()

const dataByRegionNormalized = computed(() => {
  const map = {}
  for (const [region, top3] of Object.entries(props.top3ByRegion)) {
    map[normalizeName(region)] = { originalName: region, top3 }
  }
  return map
})

const selectedTop3 = computed(() => {
  if (!selectedRegion.value) return null
  const match = dataByRegionNormalized.value[normalizeName(selectedRegion.value)]
  return match ? match.top3 : null
})

const getTopCuisineColor = (regionName) => {
  const match = dataByRegionNormalized.value[normalizeName(regionName)]
  const top1 = match?.top3?.find(i => i.rank === 1)
  return top1 ? getColor(top1.cuisine_name) : FALLBACK_COLOR
}

// Projection adaptée à la France métropolitaine, centrée et mise à l'échelle du viewBox
const projection = d3.geoConicConformal()
  .center([2.454071, 46.279229]) // centre approximatif de la France
  .scale(3200)
  .translate([width / 2, height / 2])

const pathGenerator = computed(() => d3.geoPath().projection(projection))

onMounted(async () => {
  const response = await fetch('/geo/regions.geojson')
  const geojson = await response.json()
  features.value = geojson.features
})
</script>
