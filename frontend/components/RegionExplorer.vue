<template>
  <div class="relative bg-white rounded-xl border border-stone-200 p-6 flex-column align-center justify-center">
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
          :fill-opacity="selectedRegion ? 1 : 0"
          class="transition-opacity duration-300 ease-in"
          stroke="#fcf6ee"
          stroke-width="25"
        />
      </g>

      <!-- Labels de l'anneau -->
      <g v-if="selectedRegion" :transform="`translate(${outerSize / 2}, ${outerSize / 2})`">
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

      <!-- Carte, centrée dans le même repère -->
      <g :transform="`translate(${mapOffset}, ${mapOffset})`">
        <path
          v-for="feature in features"
          :key="feature.properties.nom"
          :d="pathGenerator(feature)"
          :fill="getTopCuisineColor(feature.properties.nom)"
          :fill-opacity="hoveredRegion === feature.properties.nom ? 1 : 0.85"
          stroke="#fff"
          :stroke-width="hoveredRegion === feature.properties.nom ? 2.5 : 1"
          :class="[
            'cursor-pointer transition-all duration-150 origin-center',
            hoveredRegion === feature.properties.nom ? 'scale-105' : 'scale-100'
          ]"
          :style="{ transformBox: 'fill-box' }"
          @mouseenter="hoveredRegion = feature.properties.nom; selectedRegion = feature.properties.nom"
          @mouseleave="hoveredRegion = null"
          @click="selectedRegion = feature.properties.nom"
        />
      </g>

      
      
    </svg>
    <!-- Nom de la région survolé -->
    <Transition name="region" mode="out-in">
  <h2
    :key="selectedRegion"
    :x="outerSize / 2"
    :y="outerSize - 24"
    text-anchor="middle"
  >
    {{ selectedRegion }}
  </h2>
  </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as d3 from 'd3'

const mapSize = 900       // taille interne de la carte
const ringThickness = 30  // épaisseur de l'anneau
const ringGap = 20        // espace entre la carte et l'anneau
const outerSize = mapSize + 2 * (ringThickness + ringGap)
const mapOffset = ringThickness + ringGap


const props = defineProps({
  top3ByRegion: {
    type: Object,
    default: () => ({})
  }
})



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
  'crêperie': '#f2c94c',
  'barbecue': '#4d2f0e',
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

const activeTop3 = computed(() => {
  const region = selectedRegion.value
  if (!region) return []
  const match = dataByRegionNormalized.value[normalizeName(region)]
  return match ? match.top3 : []
})

const getTopCuisineColor = (regionName) => {
  const match = dataByRegionNormalized.value[normalizeName(regionName)]
  const top1 = match?.top3?.find(i => i.rank === 1)
  return top1 ? getColor(top1.cuisine_name) : FALLBACK_COLOR
}

// --- Génération de l'anneau (d3.pie + d3.arc) ---
const ringOuterRadius = mapSize / 2 + ringGap + ringThickness
const ringInnerRadius = mapSize / 2 + ringGap

const pieGenerator = d3.pie()
  .value(d => d.interest_score)
  .sort(null)

const arcGenerator = d3.arc()
  .innerRadius(ringInnerRadius)
  .outerRadius(ringOuterRadius)

const labelArc = d3.arc()
  .innerRadius((ringInnerRadius + ringOuterRadius) / 2)
  .outerRadius((ringInnerRadius + ringOuterRadius) / 2)

const ringSegments = computed(() => {
  const data = activeTop3.value.length > 0
    ? activeTop3.value
    : [{ cuisine_name: null, interest_score: 1, rank: 1 }] // anneau neutre si rien survolé

  const total = data.reduce((sum, d) => sum + d.interest_score, 0)
  const arcs = pieGenerator(data)

  return arcs.map(a => ({
    cuisine_name: a.data.cuisine_name,
    path: arcGenerator(a),
    labelPos: labelArc.centroid(a),
    percent: total > 0 ? Math.round((a.data.interest_score / total) * 100) : 0,
  }))
})

// Projection adaptée à la France métropolitaine, centrée et mise à l'échelle du viewBox
const projection = d3.geoConicConformal()
  .center([2.454071, 46.279229]) // centre approximatif de la France
  .scale(3200)
  .translate([mapSize / 2, mapSize / 2])

const pathGenerator = computed(() => d3.geoPath().projection(projection))

onMounted(async () => {
  const response = await fetch('/geo/regions.geojson')
  const geojson = await response.json()
  features.value = geojson.features
})
</script>
