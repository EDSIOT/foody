

<template>
  <div class="p-6 max-w-6xl mx-auto space-y-12">
    <div>
      <h1>Foody</h1>
      <p class="text-stone-500">Tendances culinaires selon les recherches google, mises à jour quotidiennement</p>
    </div>

    <!-- Section 1 : carte plate, top 3 par région -->
    <section>
      <h2 class="font-display text-xl font-semibold text-stone-800 mb-4">
        Top 3 des cuisines par région
      </h2>
      <div v-if="pendingTop3">Chargement...</div>
      <div v-else-if="errorTop3">Erreur: {{ errorTop3.message }}</div>
      <RegionExplorer v-else :top3-by-region="top3Data" />
    </section>

    <!-- Séparateur visuel -->
    <hr class="border-stone-200" />

    <!-- Section 2 : carte en colonnes 3D, par cuisine sélectionnée -->
    <section>
      <h2 class="font-display text-xl font-semibold text-stone-800 mb-4">
        Popularité d'une cuisine par région
      </h2>
      <CuisinePopularityMap />
    </section>
  </div>
</template>

<script setup>
const { getTop3PerRegion } = useApi()
const { data: top3Data, pending: pendingTop3, error: errorTop3 } = await useAsyncData(
  'top3-regions',
  () => getTop3PerRegion(7)
)
</script>

<style scoped>
  div {
    background-color: #fcf6ee;
  }
</style>
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
    padding: 0;
    margin-top: -1rem;
    color: #e07856 ;
  ;
  }
</style>

