<template>
  <div class="relative">
    <div ref="mapContainer" class="w-full h-[600px] rounded-xl overflow-hidden border border-stone-200" />

    <!-- Légende -->
    <div class="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-md p-3 max-h-64 overflow-y-auto z-[1000]">
      <p class="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-2">Cuisine dominante</p>
      <div v-for="(color, cuisine) in usedColors" :key="cuisine" class="flex items-center gap-2 text-sm mb-1">
        <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: color }" />
        <span class="text-stone-700">{{ cuisine }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  places: {
    type: Array,
    default: () => []
    // format attendu : [{ city_name, cuisine_name, interest_score, lat, lng }]
  }
})

const mapContainer = ref(null)
let map = null
let markers = []

// Palette fixe par cuisine, pour une lecture cohérente d'un run à l'autre
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

const usedColors = computed(() => {
  const set = {}
  for (const p of props.places) {
    set[p.cuisine_name] = getColor(p.cuisine_name)
  }
  return set
})

const clearMarkers = () => {
  markers.forEach(m => m.remove())
  markers = []
}

const renderMarkers = async () => {
  const L = await import('leaflet')
  clearMarkers()

  for (const place of props.places) {
    if (!place.lat || !place.lng) continue

    const marker = L.default.circleMarker([place.lat, place.lng], {
      radius: 6 + (place.interest_score / 100) * 10,
      fillColor: getColor(place.cuisine_name),
      color: '#fff',
      weight: 1.5,
      fillOpacity: 0.85,
    }).addTo(map)

    marker.bindPopup(`
      <strong>${place.city_name}</strong><br/>
      ${place.cuisine_name} — score ${place.interest_score.toFixed(1)}
    `)

    markers.push(marker)
  }
}

onMounted(async () => {
  const L = await import('leaflet')

  map = L.default.map(mapContainer.value, {
    zoomControl: true,
  }).setView([46.6, 2.3], 6) // centré sur la France

  L.default.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19,
  }).addTo(map)

  await renderMarkers()
})

watch(() => props.places, renderMarkers, { deep: true })

onBeforeUnmount(() => {
  if (map) map.remove()
})
</script>