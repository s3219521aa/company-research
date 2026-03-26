<template>
  <div class="detail">
    <!-- Header -->
    <div class="company-header">
      <button class="back" @click="$router.push('/')">← 返回</button>
      <div class="company-info">
        <div class="avatar">{{ (companyName || '?')[0] }}</div>
        <div>
          <h2>{{ companyName }}</h2>
          <p class="meta">统一社会信用代码：{{ creditCode }}</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="moduleStatus(tab.key) === 'error'" class="badge error">!</span>
        <span v-else-if="moduleStatus(tab.key) !== 'done'" class="badge loading">…</span>
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <div v-if="moduleStatus(activeTab) === 'error'" class="error-msg">
        数据获取失败，可能因目标网站限制
      </div>
      <template v-else>
        <BusinessInfo v-if="activeTab === 'business'" :data="moduleData('business')" />
        <LegalRisk v-if="activeTab === 'legal'" :data="moduleData('legal')" />
        <EmployeeReviews v-if="activeTab === 'reviews'" :data="moduleData('reviews')" />
        <SentimentPanel v-if="activeTab === 'sentiment'" :data="moduleData('sentiment')" />
      </template>
    </div>

    <!-- Global status -->
    <div v-if="overallStatus === 'scraping' || overallStatus === 'pending'" class="status-bar">
      <span class="dot"></span> 数据爬取中，已完成的模块实时显示...
    </div>
    <div v-if="timedOut" class="status-bar error">
      爬取超时，请<button class="retry" @click="startResearch">重新搜索</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { research, pollTask, getCompany } from '../api/company.js'
import BusinessInfo from '../components/BusinessInfo.vue'
import LegalRisk from '../components/LegalRisk.vue'
import EmployeeReviews from '../components/EmployeeReviews.vue'
import SentimentPanel from '../components/SentimentPanel.vue'

const route = useRoute()
const creditCode = route.params.creditCode
const companyName = route.query.name || creditCode

const tabs = [
  { key: 'business', label: '工商信息' },
  { key: 'legal', label: '法律风险' },
  { key: 'reviews', label: '员工评价' },
  { key: 'sentiment', label: '舆情风评' },
]
const activeTab = ref('business')
const modules = ref({})
const overallStatus = ref('pending')
const timedOut = ref(false)

let pollInterval = null
let pollStart = null

function moduleStatus(key) {
  return modules.value[key]?.status || 'pending'
}
function moduleData(key) {
  const m = modules.value[key]
  return m?.status === 'done' ? m.data : null
}

async function startResearch() {
  clearInterval(pollInterval)
  pollInterval = null
  timedOut.value = false
  overallStatus.value = 'pending'
  modules.value = {}
  pollStart = Date.now()

  try {
    const { task_id, cached } = await research(creditCode, companyName)

    if (cached) {
      const data = await getCompany(creditCode)
      modules.value = data.modules
      overallStatus.value = 'done'
      return
    }

    pollInterval = setInterval(async () => {
      if (Date.now() - pollStart > 120_000) {
        clearInterval(pollInterval)
        pollInterval = null
        timedOut.value = true
        return
      }
      try {
        const status = await pollTask(task_id)
        modules.value = status.modules
        overallStatus.value = status.overall_status
        if (status.overall_status === 'done') {
          clearInterval(pollInterval)
          pollInterval = null
        }
      } catch {
        // transient network error — keep polling
      }
    }, 3000)
  } catch {
    overallStatus.value = 'error'
    timedOut.value = true
  }
}

onMounted(startResearch)
onUnmounted(() => clearInterval(pollInterval))
</script>

<style scoped>
.detail { max-width: 800px; margin: 0 auto; padding: 24px; }
.company-header { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.back { background: none; border: none; color: #4a7cf0; cursor: pointer; font-size: 14px; margin-bottom: 16px; padding: 0; }
.company-info { display: flex; align-items: center; gap: 16px; }
.avatar { width: 50px; height: 50px; background: #e8f0fe; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #4a7cf0; font-size: 22px; font-weight: bold; flex-shrink: 0; }
h2 { font-size: 18px; margin-bottom: 4px; }
.meta { color: #888; font-size: 12px; }
.tabs { display: flex; gap: 4px; background: #fff; border-radius: 12px; padding: 8px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.tab { flex: 1; padding: 8px; border: none; background: none; cursor: pointer; border-radius: 8px; font-size: 13px; color: #888; position: relative; }
.tab.active { background: #4a7cf0; color: #fff; font-weight: 500; }
.badge { position: absolute; top: 4px; right: 4px; font-size: 10px; width: 14px; height: 14px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.badge.error { background: #e05050; color: #fff; }
.badge.loading { background: #f0a030; color: #fff; }
.tab-content { background: #fff; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); min-height: 200px; }
.error-msg { color: #e05050; text-align: center; padding: 40px; }
.status-bar { background: #fff8ed; border: 1px solid #fde8b0; border-radius: 10px; padding: 10px 16px; margin-top: 12px; font-size: 13px; color: #b07020; display: flex; align-items: center; gap: 8px; }
.status-bar.error { background: #fef0f0; border-color: #fcc; color: #c00; }
.dot { width: 8px; height: 8px; background: #f0a030; border-radius: 50%; flex-shrink: 0; }
.retry { background: none; border: none; color: #4a7cf0; cursor: pointer; text-decoration: underline; }
</style>
