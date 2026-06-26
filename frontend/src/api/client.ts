import axios from 'axios'

// Dev: empty baseURL → Vite proxy handles /api/* and /health
// Prod: set VITE_API_BASE_URL to the backend origin
const baseURL = (import.meta.env.PROD ? import.meta.env.VITE_API_BASE_URL as string | undefined : '') || ''

const client = axios.create({ baseURL })

const ERROR_MESSAGES: Record<number, string> = {
  404: '点位不存在或暂不支持该点位',
  422: '请求参数不合法，请修正后重试',
  503: '后端依赖暂不可用',
}

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const status: number | undefined = err.response?.status
    // Special 503 for amap
    if (status === 503) {
      const detail: string = err.response?.data?.detail ?? ''
      if (detail.toLowerCase().includes('amap') || detail.toLowerCase().includes('key')) {
        err.userMessage = '高德服务未配置，请联系管理员'
      } else {
        err.userMessage = ERROR_MESSAGES[503]
      }
    } else if (status && ERROR_MESSAGES[status]) {
      err.userMessage = ERROR_MESSAGES[status]
    }
    return Promise.reject(err)
  },
)

export default client
