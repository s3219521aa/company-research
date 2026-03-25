<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="summary">
        <div class="stat" :class="data.lawsuit_count > 0 ? 'warn' : 'ok'">
          <div class="num">{{ data.lawsuit_count }}</div><div class="desc">诉讼案件</div>
        </div>
        <div class="stat" :class="data.enforcement_count > 0 ? 'bad' : 'ok'">
          <div class="num">{{ data.enforcement_count }}</div><div class="desc">被执行</div>
        </div>
        <div class="stat" :class="data.dishonest_count > 0 ? 'bad' : 'ok'">
          <div class="num">{{ data.dishonest_count }}</div><div class="desc">失信记录</div>
        </div>
      </div>
      <div v-if="data.items.length === 0" class="empty">暂无法律风险记录</div>
      <div v-for="item in data.items" :key="item.title" class="item">
        <span class="tag" :class="item.type">{{ typeLabel(item.type) }}</span>
        <span class="title">{{ item.title }}</span>
        <span class="meta">{{ item.date }} {{ item.court }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({ data: Object })
function typeLabel(t) { return { lawsuit: '诉讼', enforcement: '被执行', dishonest: '失信' }[t] || t }
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading, .empty { color: #888; text-align: center; padding: 40px; }
.summary { display: flex; gap: 12px; margin-bottom: 20px; }
.stat { flex: 1; background: #fff; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.num { font-size: 28px; font-weight: 700; }
.desc { color: #888; font-size: 12px; margin-top: 4px; }
.ok .num { color: #2a8a50; }
.warn .num { color: #f0a030; }
.bad .num { color: #e05050; }
.item { background: #fff; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.lawsuit { background: #fff3e0; color: #e65100; }
.enforcement { background: #fce4ec; color: #c62828; }
.dishonest { background: #fce4ec; color: #c62828; }
.title { flex: 1; font-size: 13px; }
.meta { color: #aaa; font-size: 12px; white-space: nowrap; }
</style>
