<template>
  <div class="chat-item" :class="{'resp-item': type === 'AI'}">
    <div :class="{'resp': type === 'AI', 'question': type === 'human'}" class="item-content">
      {{text}}
    </div>
  </div>
</template>

<script>
export default {
  name: "ChatItem.vue",
  props: {
    text: String,
    type: String // AI or human
  }
}
</script>

<style scoped>
.chat-item {
  max-width: 80%;
}

.question {
  background: var(--nice-c-header-1);
  color: var(--vt-c-white-soft);
  text-align: left;
}

.resp-item {
  float: right;
}

.resp {
  background: var(--nice-c-header-2);
  color: var(--vt-c-white-soft);
  text-align: right;
}

.item-content {
  display: inline-block;
  margin: 5px;
  padding: 5px 20px;
  border-radius: var(--border-radius);
  box-shadow: rgba(0, 0, 0, 0.45) 0 25px 20px -25px;
}
</style>