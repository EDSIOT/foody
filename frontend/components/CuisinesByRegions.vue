<template>
  <div class="relative bg-white rounded-xl border border-stone-200 p-6 flex-column align-center justify-center"
        style="width: 100%; height: 1000px;">
  <div>
  <!-- Affichage regions -->  
  <div
    v-for="(region, i) in regions"
      :key="region.name"
      class="absolute flex items-center gap-3 z-10"
      :style="{ 
        left: `calc(50% + ${Math.cos((i / regions.length) * 2 * Math.PI - Math.PI / 2) * 400}px)`,
        top: `calc(50% + ${Math.sin((i / regions.length) * 2 * Math.PI - Math.PI / 2) * 400}px)`,
        transform: `translate(-50%, -50%)`
      }"
      @mouseenter="expandedRegion = region.name"
    >
      <div
        class="flex flex-row items-center gap-1 transition-transform duration-200 p-3 bg-white rounded-full mx-3"
        :style="{transform: `rotate(${getRegionRotation(i, regions.length)}deg)`}">
        <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: getColor(region.cuisines[0]?.cuisine_name) }"
            />
        <span 
          class="text-sm text-stone-600 truncate shrink-0 text-center "
          :style="{ transform: i > regions.length / 2 ? 'rotate(180deg)': ''}"
        >
          {{ region.name }}
        </span>
      </div>
    </div>

  <!-- Affichage des images des cuisines et leur position dans la region selectionné -->
  <div
    v-for="(cuisine, i) in regions.find(r => r.name === expandedRegion)?.cuisines"
    :key="cuisine.cuisine_name"
    class="absolute flex items-center gap-3 z-10"
    :style="{ 
      left: `calc(50% + ${Math.cos((i / regions.find(r => r.name === expandedRegion).cuisines.length) * 2 * Math.PI - Math.PI / 2) * 200}px)`,
      top: `calc(50% + ${Math.sin((i / regions.find(r => r.name === expandedRegion).cuisines.length) * 2 * Math.PI - Math.PI / 2) * 200}px)`,
      transform: `translate(-50%, -50%)`
    }"
    @mouseenter="hoveredCuisine = cuisine.cuisine_name"
    @mouseleave="hoveredCuisine = null"
  >
    <div
      class="flex flex-row items-center gap-1 transition-transform duration-200"
      :style="{transform: `rotate(${getCuisineRotation(i, regions.find(r => r.name === expandedRegion).cuisines.length)}deg)`}">
      <img
        :src="getSvg(cuisine.cuisine_name)"
        alt=""
        :width="getImageSize(cuisine.interest_score)"
      />
      <span 
        class="text-sm text-stone-600 truncate shrink-0 text-center px-2 bg-white rounded-full mx-3"
        :style="{ transform: i > regions.find(r => r.name === expandedRegion).cuisines.length / 2 ? 'rotate(180deg)': ''}"
      >
        {{ i + 1 }}
      </span>
    </div> 
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const expandedRegion = ref('Aquitaine') // Par défaut, on ouvre la région de Ile-de-France
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