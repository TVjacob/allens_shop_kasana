<template>
    <div>
      <canvas ref="chart"></canvas>
    </div>
  </template>
  
  <script>
  import { onMounted, ref, watch } from 'vue';
  import { Chart, registerables } from 'chart.js';
  
  Chart.register(...registerables);
  
  export default {
    props: {
      chartData: { type: Object, required: true },
      chartOptions: { type: Object, default: () => ({ responsive: true }) },
    },
    setup(props) {
      const chart = ref(null);
      let chartInstance = null;
  
      onMounted(() => {
        chartInstance = new Chart(chart.value, {
          type: 'line',
          data: props.chartData,
          options: props.chartOptions,
        });
      });
  
      watch(() => props.chartData, (newData) => {
        chartInstance.data = newData;
        chartInstance.update();
      });
  
      return { chart };
    },
  };
  </script>
  