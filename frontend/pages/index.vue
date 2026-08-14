import './index.css'

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1>Foody</h1>
    <p class="text-stone-500 mb-6">Tendances culinaires par région, mises à jour quotidiennement</p>

    <div v-if="pending">Chargement...</div>
    <div v-else-if="error">Erreur: {{ error.message }}</div>
    <RegionExplorer v-else :top3-by-region="data" />
  </div>
</template>

<script setup>
const { getTop3PerRegion } = useApi()
const { data, pending, error } = await useAsyncData('top3-regions', () => getTop3PerRegion(7))
</script>