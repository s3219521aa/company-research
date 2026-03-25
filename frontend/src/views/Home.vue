<template>
  <div class="home">
    <div class="hero">
      <h1>公司调研平台</h1>
      <p class="subtitle">了解你要去的公司，做出更明智的选择</p>
      <div class="search-box">
        <input
          v-model="query"
          placeholder="输入公司名称，如：字节跳动"
          @keyup.enter="doSearch"
        />
        <button @click="doSearch" :disabled="loading">
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
    </div>

    <div class="results" v-if="results.length > 0">
      <div
        v-for="r in results"
        :key="r.credit_code"
        class="result-item"
        @click="goToCompany(r)"
      >
        <div class="result-name">{{ r.name }}</div>
        <div class="result-meta">
          {{ r.province }} · {{ r.registered_capital }} · {{ r.status }}
        </div>
      </div>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { search } from '../api/company.js'

const router = useRouter()
const query = ref('')
const results = ref([])
const loading = ref(false)
const error = ref('')

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = ''
  results.value = []
  try {
    const data = await search(query.value.trim())
    results.value = data.results
    if (results.value.length === 0) error.value = '未找到相关公司'
  } catch (e) {
    error.value = '搜索失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goToCompany(company) {
  router.push({
    path: `/company/${company.credit_code}`,
    query: { name: company.name },
  })
}
</script>

<style scoped>
.home { min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 80px 24px 40px; }
.hero { text-align: center; max-width: 600px; width: 100%; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.subtitle { color: #888; margin-bottom: 32px; }
.search-box { display: flex; gap: 8px; background: #fff; border-radius: 10px; padding: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.search-box input { flex: 1; border: none; outline: none; font-size: 15px; padding: 8px 12px; }
.search-box button { background: #4a7cf0; color: #fff; border: none; border-radius: 8px; padding: 8px 20px; font-size: 14px; cursor: pointer; white-space: nowrap; }
.search-box button:disabled { opacity: 0.6; cursor: not-allowed; }
.results { margin-top: 32px; width: 100%; max-width: 600px; }
.result-item { background: #fff; border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,0.06); transition: box-shadow 0.2s; }
.result-item:hover { box-shadow: 0 4px 16px rgba(74,124,240,0.15); }
.result-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
.result-meta { color: #888; font-size: 13px; }
.error { margin-top: 24px; color: #e05050; }
</style>
