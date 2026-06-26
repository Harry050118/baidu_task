import { createRouter, createWebHistory } from 'vue-router'
import CommandMap from '../views/CommandMap.vue'
import PointDetail from '../views/PointDetail.vue'
import DataStatus from '../views/DataStatus.vue'
import LocationReview from '../views/LocationReview.vue'
import AssessmentList from '../views/AssessmentList.vue'

const routes = [
  { path: '/', component: CommandMap },
  { path: '/points/:stationCode', component: PointDetail },
  { path: '/data-status', component: DataStatus },
  { path: '/locations', component: LocationReview },
  { path: '/assessments', component: AssessmentList },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
