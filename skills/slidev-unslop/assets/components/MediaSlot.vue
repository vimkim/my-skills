<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  src: string
  filename: string
  label: string
  hint: string
  height?: string
}>()

const hasError = ref(false)
</script>

<template>
  <div class="demo-slot" :style="{ height: props.height || '100%' }">
    <img
      v-if="!hasError"
      :src="props.src"
      :alt="props.label"
      data-optional-media="true"
      @error="hasError = true"
    />
    <div v-if="hasError" class="relative z-1 px-4">
      <span class="demo-slot-badge">{{ props.filename }}</span>
      <div class="demo-slot-title text-sm font-semibold">{{ props.label }}</div>
      <div class="demo-slot-hint mt-1 text-xs font-mono leading-relaxed">{{ props.hint }}</div>
    </div>
  </div>
</template>
