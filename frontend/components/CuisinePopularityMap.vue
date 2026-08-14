<template>
  <div class="flex flex-col md:flex-row gap-4">
    <!-- Carte en colonnes -->
    <div class="relative flex-1 bg-gradient-to-b from-stone-50 to-stone-100 rounded-xl border border-stone-200 p-4">
      <svg
        :viewBox="`0 0 ${width} ${height}`"
        class="w-full h-auto"
        preserveAspectRatio="xMidYMid meet"
      >
        <g v-for="col in sortedColumns" :key="col.name">
          <!-- Murs (faces latérales visibles) -->
          <path
            v-for="(wall, i) in col.walls"
            :key="`${col.name}-wall-${i}`"
            :d="wall"
            :fill="hoveredRegion === col.name ? '#e07856' : col.color"
            
            stroke="none"
          />
          <!-- Toit (face du dessus) -->
          <path
            :d="col.topPath"
            :fill="hoveredRegion === col.name ? '#e07856' : col.color"
            :fill-opacity="hoveredRegion === col.name ? 1 : 0.9"
            stroke="#fff"
            stroke-width="1.2"
            class="cursor-pointer transition-all duration-150"
            @mouseenter="hoveredRegion = col.name; selectedRegion = col.name"
            @mouseleave="hoveredRegion = null"
            @click="selectedRegion = col.name"
          />
        </g>
      </svg>
    </div>

    <!-- Panneau latéral -->
    <div class="w-full md:w-80 shrink-0 space-y-4">
      <div class="bg-white rounded-xl border border-stone-200 shadow-sm p-5">
        <label class="text-xs font-semibold text-stone-400 uppercase tracking-wide block mb-2">
          Type de cuisine
        </label>
        <select
          v-model="selectedCuisine"
          class="w-full border border-stone-300 rounded-lg px-3 py-2 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-stone-400"
        >
          <option v-for="c in cuisinesList" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div class="bg-white rounded-xl border border-stone-200 shadow-sm p-5 min-h-[200px]">
        <div v-if="!selectedRegion" class="text-stone-400 text-sm flex flex-col items-center justify-center h-full py-12 text-center">
          Survolez une colonne pour voir le détail
        </div>
        <div v-else>
          <p class="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-1">Région</p>
          <h2>{{ selectedRegion }}</h2>
          <p class="text-sm text-stone-500">{{ selectedCuisine }}</p>
          <p class="text-3xl font-bold mt-2" :style="{ color: getColor(selectedCuisine) }">
            {{ (regionScores[selectedRegion] ?? 0).toFixed(1) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as d3 from 'd3'

const width = 700
const height = 700

const features = ref([])
const cuisinesList = ref([])
const regionScores = ref({})
const selectedCuisine = ref(null)
const hoveredRegion = ref(null)
const selectedRegion = ref(null)

const { getCuisinesList, getRegionScoresForCuisine } = useApi()

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
const FALLBACK_COLOR = '#a3a3a3'
const getColor = (cuisine) => CUISINE_COLORS[cuisine] || FALLBACK_COLOR

const normalizeName = (str) =>
  str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()

const projection = d3.geoConicConformal()
  .center([2.454071, 46.279229])
  .scale(3200)
  .translate([width / 2, height / 2])

// --- Paramètres de déformation du plan (vue oblique sud-ouest) ---
const SKEW_X = -0.4           // cisaillement horizontal : + = penche vers la droite en descendant
const VERTICAL_SQUISH = 0.4 // compression verticale du plan, pour l'aplatir façon "vu de haut, incliné"
const MAX_HEIGHT_PX = 100    // hauteur max d'une colonne pour un score de 100

function shearPoint([x, y]) {
  const cx = width / 2
  const cy = height / 2
  const dx = x - cx
  const dy = y - cy
  const sx = dx + SKEW_X * dy
  const sy = dy * VERTICAL_SQUISH
  return [cx + sx, cy + sy]
}

function getRings(geometry) {
  if (geometry.type === 'Polygon') return geometry.coordinates
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flat()
  return []
}

function projectRing(ring) {
  return ring.map(([lon, lat]) => shearPoint(projection([lon, lat])))
}

function ringToPath(points) {
  if (!points.length) return ''
  const [first, ...rest] = points
  return `M ${first[0]},${first[1]} ` + rest.map(p => `L ${p[0]},${p[1]}`).join(' ') + ' Z'
}

function buildColumn(feature, score, color) {
  const heightPx = (score / 100) * MAX_HEIGHT_PX

  const rings = getRings(feature.geometry)
  const mainRing = rings.reduce((a, b) => (a.length > b.length ? a : b), rings[0] || [])
  const base = projectRing(mainRing)               // plan déformé
  const top = base.map(([x, y]) => [x, y - heightPx]) // montée strictement verticale

  const cx = base.reduce((s, p) => s + p[0], 0) / base.length
  const cy = base.reduce((s, p) => s + p[1], 0) / base.length

  const walls = []
  for (let i = 0; i < base.length - 1; i++) {
    const p1 = base[i], p2 = base[i + 1]
    const midX = (p1[0] + p2[0]) / 2
    const midY = (p1[1] + p2[1]) / 2
    const nx = midX - cx
    const ny = midY - cy
    const norm = Math.sqrt(nx * nx + ny * ny) || 1

    // Mur visible si son orientation "regarde vers le bas de l'écran" (face au spectateur)
    if (ny / norm > 0.1) {
      const t1 = top[i], t2 = top[i + 1]
      walls.push(`M ${p1[0]},${p1[1]} L ${p2[0]},${p2[1]} L ${t2[0]},${t2[1]} L ${t1[0]},${t1[1]} Z`)
    }
  }

  return {
    name: feature.properties.nom,
    topPath: ringToPath(top),
    walls,
    color,
    depthKey: cy,
  }
}

const columns = computed(() => {
  return features.value.map(f => {
    const name = f.properties.nom
    const match = Object.entries(regionScores.value).find(
      ([region]) => normalizeName(region) === normalizeName(name)
    )
    const score = match ? match[1] : 0
    return buildColumn(f, score, getColor(selectedCuisine.value))
  })
})

const sortedColumns = computed(() =>
  [...columns.value].sort((a, b) => a.depthKey - b.depthKey)
)

async function loadRegionData() {
  if (!selectedCuisine.value) return
  regionScores.value = await getRegionScoresForCuisine(selectedCuisine.value)
}

onMounted(async () => {
  const response = await fetch('/geo/regions.geojson')
  const geojson = await response.json()
  features.value = geojson.features

  cuisinesList.value = await getCuisinesList()
  selectedCuisine.value = cuisinesList.value[0] || null
  await loadRegionData()
})

watch(selectedCuisine, loadRegionData)
</script>