const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function search(name) {
  const res = await fetch(`${BASE}/api/search?name=${encodeURIComponent(name)}`)
  if (!res.ok) throw new Error('搜索失败')
  return res.json()
}

export async function research(creditCode, companyName) {
  const res = await fetch(`${BASE}/api/company/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credit_code: creditCode, company_name: companyName }),
  })
  if (!res.ok) throw new Error('发起爬取失败')
  return res.json()
}

export async function pollTask(taskId) {
  const res = await fetch(`${BASE}/api/task/${taskId}`)
  if (!res.ok) throw new Error('查询任务状态失败')
  return res.json()
}

export async function getCompany(creditCode) {
  const res = await fetch(`${BASE}/api/company/${creditCode}`)
  if (!res.ok) throw new Error('获取公司数据失败')
  return res.json()
}
