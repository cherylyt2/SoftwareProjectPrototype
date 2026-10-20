import { createApp } from 'vue'
import { Quasar } from 'quasar'
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'
import './app.css'
import App from './AppRoot.vue'

createApp(App).use(Quasar).mount('#app')
