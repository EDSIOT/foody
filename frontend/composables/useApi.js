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

  const getTop3PerRegion = async (days = 7) => {
    return await $fetch(`${base}/regions/top3`, { params: { days } })
  }

/*  const getCuisinesList = async () => {
    return await $fetch(`${base}/cuisines/list`)
  } */
    const getCuisinesList = async () => {
  const response = await fetch(`${base}/cuisines/list`)

  console.log('STATUS:', response.status)
  console.log('CONTENT-TYPE:', response.headers.get('content-type'))

  const text = await response.text()

  console.log('RAW RESPONSE:', text)

  return JSON.parse(text)
}

  const getRegionScoresForCuisine = async (cuisine, days = 7) => {
    return await $fetch(`${base}/regions/by-cuisine`, { params: { cuisine, days } })
  }

  return { getTopCuisines, getCities, getCuisineHistory, getTop3PerRegion, getCuisinesList, getRegionScoresForCuisine }
}
