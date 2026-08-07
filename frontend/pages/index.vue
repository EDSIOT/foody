<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Foody — Tendances culinaires par ville</h1>

    <div v-if="pending">Chargement...</div>
    <div v-else-if="error">Erreur: {{ error.message }}</div>
    <div v-else>
      <table class="w-full border-collapse">
        <thead>
          <tr class="border-b">
            <th class="text-left p-2">Ville</th>
            <th class="text-left p-2">Cuisine dominante</th>
            <th class="text-left p-2">Score</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item.city_name" class="border-b">
            <td class="p-2">{{ item.city_name }}</td>
            <td class="p-2">{{ item.cuisine_name }}</td>
            <td class="p-2">{{ item.interest_score.toFixed(1) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
const { getTopCuisines } = useApi()
const { data, pending, error } = await useAsyncData('top-cuisines', () => getTopCuisines(7))
</script>