<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <div v-else class="grid">
      <div class="card"><div class="label">法定代表人</div><div class="val">{{ data.legal_person || '—' }}</div></div>
      <div class="card"><div class="label">成立日期</div><div class="val">{{ data.established_date || '—' }}</div></div>
      <div class="card"><div class="label">注册资本</div><div class="val">{{ data.registered_capital || '—' }}</div></div>
      <div class="card"><div class="label">经营状态</div><div class="val" :class="data.status === '存续' ? 'green' : ''">{{ data.status || '—' }}</div></div>
      <div class="card full"><div class="label">注册地址</div><div class="val">{{ data.address || '—' }}</div></div>
      <div class="card full"><div class="label">经营范围</div><div class="val">{{ data.business_scope || '—' }}</div></div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: Object })
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading { color: #888; text-align: center; padding: 40px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.card { background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card.full { grid-column: 1 / -1; }
.label { color: #aaa; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.val { color: #1a1a2e; font-weight: 500; font-size: 14px; line-height: 1.5; }
.green { color: #2a8a50; }
</style>
