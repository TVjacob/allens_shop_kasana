import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './main.css'

// 🟣 Vuetify imports
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// 🟣 Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
})

// 🟢 Create Vue app
const app = createApp(App)

// 🧩 Use plugins
app.use(router)
app.use(createPinia())
app.use(vuetify) // ✅ Make Vuetify available everywhere

// 🚀 Mount
app.mount('#app')
