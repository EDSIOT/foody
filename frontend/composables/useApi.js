export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  const getTopCuisines = async (days = 7) => {
    return await $fetch(`${base}/cuisines/top`, { params: { days } })
  }

  const getCities = async () => {
    return await $fetch(`${base}/cities`)
  }

  const getCuisineHistory = async (city, cuisine, days = 7) => {
    return await $fetch(`${base}/cuisines`, { params: { city, cuisine, days } })
  }

  return { getTopCuisines, getCities, getCuisineHistory }
}

const getTop3PerRegion = async (days = 7) => {
  return await $fetch(`${base}/regions/top3`, { params: { days } })
}

return { getTopCuisines, getCities, getCuisineHistory, getTop3PerRegion }