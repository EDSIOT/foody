<template>
  <div class="flex flex-col md:flex-row gap-4">
  <div class="relative flex-1 bg-gradient-to-b from-stone-50 to-stone-100 rounded-xl border border-stone-200 p-4">
    <svg
      :viewBox="`0 0 ${width} ${height}`"
      class="w-full h-auto"
      preserveAspectRatio="xMidYMid meet"
    >
      <!-- Murs -->
      <g v-for="col in sortedColumns" :key="col.name">
        <path
          v-for="(wall, i) in col.walls.path"
          :key="`${col.name}-wall-${i}`"
          :d="wall"
          :fill="
            d3.interpolateRgb(
              d3.color(col.color).darker(1.5),
              col.color
            )(col.walls.dot[i])
          "
          fill-opacity="0.85"
          stroke="none"
        />
        </g>
        <!-- Regions -->
        <g v-for="col in sortedColumns" :key="col.name">
        <path
          :d="col.topPath"
          :fill="hoveredRegion === col.name ? d3.color(col.color).darker(-0.5) : col.color"
          stroke="#fff"
          stroke-width="1.2"
          class="cursor-pointer transition-all duration-150"
          @mouseenter="hoveredRegion = col.name; selectedRegion = col.name"
          @mouseleave="hoveredRegion = null"
          @click="selectedRegion = col.name"
        />
      </g>

      <!-- DEBUG: flèche représentant CAMERA_DIR -->
      <g v-if="showCameraDebug">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 9 3, 0 6" fill="red" />
          </marker>
        </defs>
        <line
          :x1="width / 2"
          :y1="height / 2"
          :x2="width / 2 + CAMERA_DIR.x * 150"
          :y2="height / 2 + CAMERA_DIR.y * 150"
          stroke="red"
          stroke-width="3"
          marker-end="url(#arrowhead)"
        />
        <circle :cx="width / 2" :cy="height / 2" r="5" fill="red" />
        <text
          :x="width / 2 + CAMERA_DIR.x * 150 + 10"
          :y="height / 2 + CAMERA_DIR.y * 150"
          fill="red"
          font-size="14"
          font-weight="bold"
        >
          CAMERA_DIR ({{ CAMERA_DIR.x.toFixed(2) }}, {{ CAMERA_DIR.y.toFixed(2) }})
        </text>
      </g>
    </svg>

    <button
      @click="showCameraDebug = !showCameraDebug"
      class="absolute top-2 right-2 text-xs bg-white border border-stone-300 rounded px-2 py-1 shadow-sm hover:bg-stone-50"
    >
      {{ showCameraDebug ? 'Masquer' : 'Afficher' }} CAMERA_DIR
    </button>
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

const showCameraDebug = ref(true) // affiche le vecteur CAMERA_DIR pour debug
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

// Projection adaptée à la France métropolitaine, centrée et mise à l'échelle du viewBox
const projection = d3.geoConicConformal()
  .center([2.454071, 46.279229]) // centre approximatif de la France
  .scale(3200)
  .translate([width / 2, height / 2])
// centre approximatif de chaque région : [lon, lat] = d3.geoCentroid(feature)

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

// Direction de la caméra dérivée automatiquement de la déformation du plan.
// Le sol "s'éloigne" vers (SKEW_X, VERTICAL_SQUISH) ; la caméra regarde depuis l'opposé.
const CAMERA_DIR = (() => {
  const cx = -SKEW_X
  const cy = VERTICAL_SQUISH
  const norm = Math.sqrt(cx * cx + cy * cy) || 1
  return { x: cx / norm, y: cy / norm }
})()

function buildColumn(feature, score, color) {
  const heightPx = (score / 100) * MAX_HEIGHT_PX

  const rings = getRings(feature.geometry)
  const mainRing = rings.reduce((a, b) => (a.length > b.length ? a : b), rings[0] || [])
  const base = projectRing(mainRing)
  const top = base.map(([x, y]) => [x, y - heightPx])

  const cx = base.reduce((s, p) => s + p[0], 0) / base.length
  const cy = base.reduce((s, p) => s + p[1], 0) / base.length

  const walls = { path: [], dot: [] }
  for (let i = 0; i < base.length - 1; i++) {
    const p1 = base[i], p2 = base[i + 1]
    const midX = (p1[0] + p2[0]) / 2
    const midY = (p1[1] + p2[1]) / 2
    const nx = midX - cx
    const ny = midY - cy
    const norm = Math.sqrt(nx * nx + ny * ny) || 1
    const dot = (nx / norm) * CAMERA_DIR.x + (ny / norm) * CAMERA_DIR.y   // produit scalaire entre la normale du mur et la direction de la caméra

    // Mur visible si son orientation fait face à la caméra i.e. si le produit scalaire est positif (angle < 90°)
    //if (dot > -0.5) { // seuil pour éviter les murs trop "de côté"
      const t1 = top[i], t2 = top[i + 1]
      walls.path.push(
         `M ${p1[0]},${p1[1]} L ${p2[0]},${p2[1]} L ${t2[0]},${t2[1]} L ${t1[0]},${t1[1]} Z`
        )
      walls.dot.push(dot)
    //}
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

const CENTRE_REGIONS = [
    { name: "Nord-Pas-de-Calais",   coords: [3.0573, 50.6292], feature:   7 }, // Lille
    { name: "Haute-Normandie",      coords: [1.0993, 49.4432], feature:   3 }, // Rouen
   { name: "Picardie",             coords: [2.2957, 49.8941], feature:   2 }, // Amiens
    { name: "Île-de-France",        coords: [2.3522, 48.8566], feature:   0 }, // Paris
  { name: "Basse-Normandie",      coords: [-0.3707, 49.1829], feature:  5 }, // Caen  
    { name: "Champagne-Ardenne",    coords: [4.3670, 48.9565], feature:   1 }, // Châlons-en-Champagne
    { name: "Lorraine",             coords: [6.1844, 49.1193], feature:   8 }, // Metz
  { name: "Alsace",               coords: [7.7479, 48.5839], feature:   9 }, // Strasbourg
  { name: "Bretagne",             coords: [-1.6778, 48.1173], feature:  12 }, // Rennes
  { name: "Pays de la Loire",     coords: [-1.5536, 47.2184], feature:  11 }, // Nantes
    { name: "Centre-Val de Loire",  coords: [1.9093, 47.9030], feature:   4 }, // Orléans
  { name: "Bourgogne",            coords: [5.0415, 47.3220], feature:   6 }, // Dijon
  { name: "Franche-Comté",        coords: [6.0241, 47.2378], feature:   10 }, // Besançon
  { name: "Poitou-Charentes",     coords: [0.3333, 46.5833], feature:   13 }, // Poitiers
  { name: "Limousin",             coords: [1.2611, 45.8336], feature:   16 }, // Limoges
  { name: "Auvergne",             coords: [3.0870, 45.7772], feature:   18 }, // Clermont-Ferrand
  { name: "Rhône-Alpes",           coords: [4.8357, 45.7640], feature:  17 }, // Lyon
  { name: "Aquitaine",            coords: [-0.5792, 44.8378], feature:  14 }, // Bordeaux
  { name: "Midi-Pyrénées",        coords: [1.4442, 43.6047], feature:   15 }, // Toulouse
  { name: "Languedoc-Roussillon", coords: [3.8767, 43.6119], feature:   19 }, // Montpellier
  { name: "Provence-Alpes-Côte d’Azur", coords: [5.3698, 43.2965], feature:  20 }, // Marseille
  { name: "Corse",                coords: [8.7386, 41.9192], feature:   21 }, // Ajaccio
]

async function loadRegionData() {
  if (!selectedCuisine.value) return
  regionScores.value = await getRegionScoresForCuisine(selectedCuisine.value)
}

onMounted(async () => {
  const response = await fetch('/geo/regions_opti copy.geojson')
  const geojson = await response.json()
  features.value = geojson.features

  cuisinesList.value = await getCuisinesList()
  selectedCuisine.value = cuisinesList.value[0] || null
  await loadRegionData()
})

watch(selectedCuisine, loadRegionData)
</script>