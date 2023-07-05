<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import IconNice from "@/components/icons/IconNice.vue";
</script>

<template>
  <div class="wrapper">
    <div class="title">
      <img src="./assets/nhs-logo.jpg" class="nhs-logo">
      <icon-nice class="nice-logo"></icon-nice> <span class="title-text"> - LLM Q & A</span>
    </div>
<!--    <nav>-->
<!--      <RouterLink to="/">Home</RouterLink>-->
<!--    </nav>-->
  </div>
  <RouterView/>
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

.wrapper {
  background: var(--color-background-mute);
}

.title {
  display: inline-block;
  padding-left: 10px;
}

.title-text {
  color: var(--color-text);
}

.nhs-logo {
  height: 45px;
  vertical-align: middle;
}

.nice-logo {
  height: 30px;
  margin: 19px;
  vertical-align: middle;
}

</style>
