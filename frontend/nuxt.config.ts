// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'https://foody-u1fl.onrender.com'
    }
  },
  modules: ['@nuxtjs/tailwindcss','@nuxt/fonts'],
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true }
})