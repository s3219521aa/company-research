<template>
  <div class="tab-panel">
    <div v-if="!data" class="loading">数据加载中...</div>
    <template v-else>
      <div class="count">共 {{ data.source_count }} 条评价</div>
      <div v-if="data.items.length === 0" class="empty">暂无员工评价数据</div>
      <div v-for="(item, i) in data.items" :key="i" class="review">
        <div class="review-header">
          <span class="source">{{ item.source }}</span>
          <span class="stars" v-if="item.rating">{{ '★'.repeat(item.rating) }}{{ '☆'.repeat(5 - item.rating) }}</span>
          <span class="date">{{ item.date }}</span>
        </div>
        <p class="content">{{ item.content }}</p>
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
.review { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.review-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.source { background: #e8f0fe; color: #4a7cf0; font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.stars { color: #f0a030; font-size: 13px; }
.date { color: #aaa; font-size: 12px; margin-left: auto; }
.content { color: #444; font-size: 14px; line-height: 1.6; }
</style>
