import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import CompanyDetail from '../views/CompanyDetail.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/company/:creditCode', component: CompanyDetail, props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
