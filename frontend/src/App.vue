<script setup>

import { computed, ref ,nextTick} from 'vue'
import * as echarts from 'echarts'

let question=ref(``)
let answer=ref(``)
const sql=ref(``)
const result=ref([])

const loading = ref(false)
const errorMessage = ref('')
const hasSearched = ref(false)

const chartRef = ref(null)
let chartInstance = null

const chartConfig = ref(null)

const columns=computed(()=>{
  if(result.value.length===0){
    return []
  }
  return Object.keys(result.value[0])
})

const chartFields = computed(() => {
  if (result.value.length === 0) {
    return null
  }

  const firstRow = result.value[0]
  const fields = Object.keys(firstRow)

  const xField = fields.find(field => {
    const value = firstRow[field]

    return Number.isNaN(Number(value))
  })

  const yField = fields.find(field => {
    const value = firstRow[field]

    return (
      value !== null &&
      value !== '' &&
      !Number.isNaN(Number(value))
    )
  })

  if (!xField || !yField) {
    return null
  }

  return {
    xField,
    yField
  }
})

function disposeChart(){
   if (chartInstance) {
    chartInstance.dispose()
    chartInstance=null
  }
}

function renderChart() {
  if (
    !chartRef.value ||
    !chartConfig.value ||
    result.value.length === 0
  ) {
    return
  }
  const config = chartConfig.value

  const xData = result.value.map(
    row => row[config.x_field]
  )

  const yData = result.value.map(
    row => Number(row[config.y_field])
  )
  disposeChart()

  chartInstance = echarts.init(chartRef.value)

  chartInstance.setOption({
    title: {
      text: config.title || ''
    },
    tooltip: {
      trigger: 'axis'
    },

    xAxis: {
      type: 'category',
      data: xData,
      name: config.xField,
      axisLabel: {
        interval: 0,
        rotate: xData.length > 5 ? 45 : 0
      }
    },

    yAxis: {
      type: 'value',
      name: config.yField
    },

    series: [
      {
        name: config.yField,
        type: config.type,
        data: yData,

        label: {
          show: true,
          position: 'top'
        }
      }
    ]
  })
}
async function analyze(){
  if(!question.value.trim()){
    return
  }
  loading.value=true
  errorMessage.value = ''
  hasSearched.value = true

  answer.value = ''
  sql.value = ''
  result.value = []
  disposeChart()
  chartConfig.value = null

  try{
    const response=await fetch('http://127.0.0.1:8000/ask',{
      method:'POST',
      headers:{
        'Content-Type':'application/json'
      },
      body:JSON.stringify(
        {
          question:question.value
        }
      )
    })
    if(!response.ok){
      throw new Error('后端请求失败')
    }
    const data=await response.json()

    answer.value=data.answer
    sql.value=data.sql
    result.value=data.result
    chartConfig.value = data.chart

    await nextTick()

    if (chartConfig.value) {
      renderChart()
    }
  }
  catch(error){
    console.error(error)
    errorMessage.value = '查询失败，请稍后重试'
  }finally{
      loading.value=false
  }
}
</script>

<template>
  <div class="data-agent">
    <div class="page-header">
      <h1>DataAgent 智能数据分析助手</h1>
      <p class="page-subtitle">自然语言驱动的数据分析平台</p>
    </div>

    <div class="card query-card">
      <h2>数据查询</h2>
      <div class="query-controls">
        <input class="question-input" v-model="question" placeholder="请输入你的问题">
        <button
          class="analyze-button"
          @click="analyze"
          :disabled="loading || !question.trim()"
        >
          {{ loading?'分析中...':'开始分析' }}
        </button>
      </div>
      <p v-if="loading" class="loading-message">正在分析，请稍候</p>
    </div>

    <p v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </p>

    <div v-if="answer" class="card">
      <h2>AI 分析结论</h2>
      <p class="answer-content">{{ answer }}</p>
    </div>

    <div v-if="chartConfig" class="card">
      <h2>数据可视化</h2>
      <div class="chart-scroll">
        <div ref="chartRef" class="chart"></div>
      </div>
    </div>

    <div v-if="result.length>0" class="card">
      <h2>查询结果</h2>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th v-for="column in columns" :key="column">
                {{ column }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in result" :key="row">
              <td v-for="column in columns" :key="column">
                {{ row[column] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p
      v-if="
        hasSearched &&
        !loading &&
        !errorMessage &&
        result.length === 0
      "
      class="empty-message"
    >
      暂无查询结果
    </p>

    <div v-if="sql" class="card">
      <h2>SQL</h2>
      <p class="sql-code">{{ sql }}</p>
    </div>
  </div>
</template>
