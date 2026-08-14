<template>
  <div class="flex flex-col md:flex-row gap-4">
    <!-- Carte -->
    <div class="relative flex-1">
      <div ref="mapContainer" class="w-full h-[600px] rounded-xl overflow-hidden border border-stone-200" />
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
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  top3ByRegion: {
    type: Object,
    default: () => ({})
    // format : { "Île-de-France": [{cuisine_name, interest_score, rank}, ...], ... }
  }
})

const mapContainer = ref(null)
const selectedRegion = ref(null)
let map = null
let geoLayer = null

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
const FALLBACK_COLOR = '#9b9b9b'
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

const styleFeature = (feature) => {
  const regionName = feature.properties.nom
  return {
    fillColor: getTopCuisineColor(regionName),
    weight: 1.5,
    color: '#fff',
    fillOpacity: 0.75,
  }
}

const onEachFeature = (feature, layer) => {
  const regionName = feature.properties.nom

  layer.on({
    mouseover: (e) => {
      e.target.setStyle({ fillOpacity: 0.9, weight: 2.5 })
      selectedRegion.value = regionName
    },
    mouseout: (e) => {
      e.target.setStyle({ fillOpacity: 0.75, weight: 1.5 })
    },
    click: (e) => {
      selectedRegion.value = regionName
      map.fitBounds(e.target.getBounds(), { maxZoom: 7 })
    },
  })
}

const renderMap = async () => {
  const L = await import('leaflet')
  if (geoLayer) geoLayer.remove()

  const response = await fetch('/geo/old_regions.geojson')
  const geojson = await response.json()

  geoLayer = L.default.geoJSON(geojson, {
    style: styleFeature,
    onEachFeature: onEachFeature,
  }).addTo(map)
}

onMounted(async () => {
  const L = await import('leaflet')
  map = L.default.map(mapContainer.value).setView([46.6, 2.3], 5.5)

  L.default.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19,
  }).addTo(map)

  await renderMap()
})

onBeforeUnmount(() => {
  if (map) map.remove()
})
</script>