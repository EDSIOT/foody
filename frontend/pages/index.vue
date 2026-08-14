

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1>Foody</h1>
    <p class="text-stone-500 mb-6">Tendances culinaires par région, mises à jour quotidiennement</p>

    <div v-if="pending">Chargement...</div>
    <div v-else-if="error">Erreur: {{ error.message }}</div>
    <RegionExplorer v-else :top3-by-region="data" />
  </div>
</template>

<style>
h1 {
  font-family: Limelight, sans-serif;
  font-size: 3rem;
  color: #e07856 ;
;
}

h2 {
  font-family: Italianno, sans-serif;
  font-size: 2.5rem;
  color: #e07856 ;
;
}
</style>

<script setup>
const { getTop3PerRegion } = useApi()
const { data, pending, error } = await useAsyncData('top3-regions', () => getTop3PerRegion(7))
</script>