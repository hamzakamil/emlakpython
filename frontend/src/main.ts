// Uygulama giriş noktası — Pinia + Vue Router bağlanır.
// Kurallar: docs/proje-kurallari/00-TEKNOLOJI-STACK.md (Vue 3 + TS + Pinia + Tailwind)
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const uygulama = createApp(App)

// Sıra önemli: router guard'ları auth store'a erişir → Pinia önce kurulmalı.
uygulama.use(createPinia())
uygulama.use(router)

uygulama.mount('#app')
