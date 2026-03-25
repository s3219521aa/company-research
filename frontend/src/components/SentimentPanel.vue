<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="count">共 {{ data.item_count }} 条相关讨论</div>
      <div v-if="data.items.length === 0" class="empty">暂无网络舆情数据</div>
      <div v-for="(item, i) in data.items" :key="i" class="sentiment-item">
        <div class="item-header">
          <span class="source">{{ item.source }}</span>
          <span class="date">{{ item.date }}</span>
        </div>
        <a class="title" :href="item.url" target="_blank" rel="noopener">{{ item.title }}</a>
        <p class="snippet" v-if="item.snippet">{{ item.snippet }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({ data: Object })
</script>

<style scoped>
.tab-panel { padding: 20px 0; }
.loading, .empty { color: #888; text-align: center; padding: 40px; }
.count { color: #888; font-size: 13px; margin-bottom: 16px; }
.sentiment-item { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.item-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.source { background: #e8f5ee; color: #2a8a50; font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.date { color: #aaa; font-size: 12px; margin-left: auto; }
.title { font-size: 14px; font-weight: 500; color: #4a7cf0; text-decoration: none; display: block; margin-bottom: 6px; }
.title:hover { text-decoration: underline; }
.snippet { color: #666; font-size: 13px; line-height: 1.6; }
</style>
