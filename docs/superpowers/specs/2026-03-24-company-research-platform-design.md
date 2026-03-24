# 公司调研平台 设计文档

**日期：** 2026-03-24
**项目：** compan_search_ai
**目标用户：** 中国大陆求职者，希望在面试前调研目标公司

---

## 1. 产品概述

一个面向中国大陆求职者的公司调研平台，帮助应聘者了解目标公司的工商信息、法律风险、员工评价和网络舆情，从而判断一家公司是否值得加入。

---

## 2. 核心功能模块

| 模块 | 数据来源 | 说明 |
|------|----------|------|
| 工商信息 | 国家企业信用信息公示系统 | 注册资本、法人、经营范围、成立日期、经营状态 |
| 法律风险 | 裁判文书网、执行信息公开网 | 诉讼案件、被执行人记录、失信记录 |
| 员工评价 | 脉脉、牛客网、BOSS直聘 | 薪资、工作环境、面试体验、匿名评价 |
| 舆情风评 | 知乎、微博 | 新闻报道、社交媒体讨论、负面舆情 |

**不在范围内：** 招聘信息（应聘者已知）、用户账号系统（MVP 阶段）、综合评分算法（详情页不展示评分字段）

---

## 3. 技术架构

### 整体方案
轻量单体架构，MVP 阶段用 asyncio 后台任务处理爬取，预留 Celery 迁移接口。

### 技术栈
- **后端：** Python + FastAPI
- **前端：** Vue 3
- **数据库：** SQLite（缓存爬取结果，24小时有效期）
- **爬虫：** Playwright（处理 JS 渲染页面）+ requests
- **部署：** docker-compose 一键启动（注意：Playwright 在 Docker 中需 Chromium 依赖，镜像体积较大，使用 `mcr.microsoft.com/playwright/python` 基础镜像）
- **跨域：** FastAPI 配置 CORS，允许 Vue 开发服务器（localhost:5173）及生产域名访问

### 查询流程

**命中缓存：**
```
用户搜索 → 检查 SQLite 缓存 → 命中（< 24h）→ 直接返回结果
```

**未命中缓存（实时爬取）：**
```
用户搜索 → 未命中缓存 → 创建爬取任务（返回 task_id，写入 SQLite）
→ 四个爬虫并行执行 → 前端每 3 秒轮询状态
→ 各模块完成后逐步显示 → 全部完成后更新缓存记录
```

### 搜索 → 爬取的关键流程
1. `GET /api/search?name=xxx` 调用工商信息爬虫做模糊名称匹配，返回候选公司列表（含统一社会信用代码）
2. 用户选择目标公司后，前端以**统一社会信用代码**为 key 发起 `POST /api/company/research`
3. 后续所有模块爬取均以统一社会信用代码为唯一标识，缓存 key 也使用该代码

---

## 4. API 设计

### `GET /api/search?name=xxx`
搜索公司（模糊匹配），返回候选列表。

**响应：**
```json
{
  "results": [
    {
      "credit_code": "91110108551385082J",
      "name": "字节跳动科技有限公司",
      "legal_person": "张一鸣",
      "registered_capital": "50000万元",
      "province": "北京市",
      "status": "存续"
    }
  ]
}
```

---

### `POST /api/company/research`
发起爬取任务，返回 task_id。

**请求体：**
```json
{
  "credit_code": "91110108551385082J",
  "company_name": "字节跳动科技有限公司"
}
```

**响应：**
```json
{
  "task_id": "uuid-xxxx",
  "cached": false
}
```

若 `cached: true`，前端直接跳转到 `GET /api/company/{credit_code}`，无需轮询。

---

### `GET /api/task/{task_id}`
轮询任务状态及已完成模块数据。

**响应：**
```json
{
  "task_id": "uuid-xxxx",
  "overall_status": "scraping",
  "modules": {
    "business": {
      "status": "done",
      "data": { ... }
    },
    "legal": {
      "status": "scraping",
      "data": null
    },
    "reviews": {
      "status": "pending",
      "data": null
    },
    "sentiment": {
      "status": "error",
      "error": "目标网站返回 403，跳过",
      "data": null
    }
  }
}
```

`overall_status` 规则：所有模块 `done` 或 `error` → `done`；任意一个 `scraping` → `scraping`；任务刚创建 → `pending`。

---

### `GET /api/company/{credit_code}`
直接读取缓存的完整结果。结构与 `GET /api/task/{task_id}` 的 `modules` 字段相同，`overall_status` 固定为 `done`。

**各模块 `data` 字段示例：**

```json
{
  "overall_status": "done",
  "modules": {
    "business": {
      "status": "done",
      "data": {
        "credit_code": "91110108551385082J",
        "name": "字节跳动科技有限公司",
        "legal_person": "张一鸣",
        "registered_capital": "50000万元",
        "established_date": "2012-03-09",
        "status": "存续",
        "province": "北京市",
        "address": "北京市海淀区...",
        "business_scope": "互联网信息服务..."
      }
    },
    "legal": {
      "status": "done",
      "data": {
        "lawsuit_count": 3,
        "enforcement_count": 0,
        "dishonest_count": 0,
        "items": [
          { "type": "lawsuit", "title": "劳动合同纠纷", "date": "2023-05-12", "court": "海淀区法院", "result": "调解" }
        ]
      }
    },
    "reviews": {
      "status": "done",
      "data": {
        "source_count": 12,
        "items": [
          { "source": "牛客网", "content": "氛围不错，加班较多", "date": "2024-01", "rating": 4 }
        ]
      }
    },
    "sentiment": {
      "status": "error",
      "error": "目标网站返回 403，跳过",
      "data": null
    }
  }
}
```

**前端停止轮询条件：** `overall_status === 'done'`（所有模块均已完成或失败），或累计轮询超过 120 秒。

---

## 5. 错误处理策略

- **单个爬虫失败不阻断整体：** 某模块爬取失败时，该模块状态置为 `error`，附带简短错误说明，其余模块继续执行。
- **前端展示：** 失败模块在 Tab 内显示"数据获取失败，可能因目标网站限制"，不显示空白或崩溃。
- **重试：** 每个爬虫失败后最多自动重试 2 次（间隔 3 秒），之后标记为 `error`。
- **任务进程崩溃：** 任务状态持久化在 SQLite，进程重启后 `scraping` 状态的任务不会自动恢复。前端轮询超过 120 秒未完成时，提示用户"爬取超时，请重新搜索"。

---

## 6. 爬虫策略

目标平台中部分（脉脉、微博）存在反爬机制：

- **请求间隔：** 每次请求前随机延迟 1~3 秒
- **User-Agent：** 随机轮换常见浏览器 UA
- **Playwright 使用：** 针对 JS 渲染页面（BOSS直聘、知乎）使用 Playwright headless browser
- **Cookie/Session：** MVP 阶段不处理登录态；需要登录的内容（如脉脉付费内容）标记为不可用
- **失败处理：** 按第 5 节策略处理，不因反爬失败导致整体任务挂起

---

## 7. 数据库 Schema（SQLite）

```sql
-- 公司缓存主表
CREATE TABLE company_cache (
    credit_code     TEXT PRIMARY KEY,
    company_name    TEXT NOT NULL,
    created_at      INTEGER NOT NULL,  -- Unix timestamp
    expires_at      INTEGER NOT NULL   -- created_at + 86400
);

-- 各模块数据（独立存储，支持部分更新）
CREATE TABLE module_data (
    credit_code  TEXT NOT NULL,
    module       TEXT NOT NULL,  -- 'business' | 'legal' | 'reviews' | 'sentiment'
    status       TEXT NOT NULL,  -- 'done' | 'error'
    data_json    TEXT,           -- JSON string，error 时为 null
    error_msg    TEXT,           -- 仅 error 时有值
    updated_at   INTEGER NOT NULL,
    PRIMARY KEY (credit_code, module)
);
-- 注意：module_data 仅在模块达到最终状态（done/error）时写入。
-- pending 和 scraping 是 tasks.py 管理的内存瞬态，不写入此表。

-- 任务状态表（持久化，进程重启可查）
CREATE TABLE tasks (
    task_id      TEXT PRIMARY KEY,
    credit_code  TEXT NOT NULL,
    created_at   INTEGER NOT NULL,
    status       TEXT NOT NULL   -- 'pending' | 'scraping' | 'done' | 'error'
);
```

---

## 8. 项目目录结构

```
compan_search_ai/
├── backend/
│   ├── main.py          # FastAPI 入口，路由注册，CORS 配置
│   ├── tasks.py         # 任务调度，asyncio 后台任务
│   ├── cache.py         # SQLite 缓存读写（24h TTL）
│   ├── models.py        # Pydantic 数据模型
│   └── scrapers/
│       ├── base.py      # 爬虫基类（重试、延迟、UA 轮换）
│       ├── business.py  # 工商信息（国家企信网）
│       ├── legal.py     # 法律风险（裁判文书网、执行信息公开网）
│       ├── reviews.py   # 员工评价（脉脉/牛客/BOSS直聘）
│       └── sentiment.py # 舆情风评（知乎/微博）
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── Home.vue              # 搜索首页
│       │   └── CompanyDetail.vue     # 公司详情页（Tab 容器 + 轮询逻辑）
│       ├── components/
│       │   ├── BusinessInfo.vue      # 工商信息 Tab
│       │   ├── LegalRisk.vue         # 法律风险 Tab
│       │   ├── EmployeeReviews.vue   # 员工评价 Tab
│       │   └── SentimentPanel.vue    # 舆情风评 Tab
│       └── api/
│           └── company.js            # 接口封装（search、research、pollTask）
├── docker-compose.yml
└── requirements.txt
```

---

## 9. 前端页面

### 搜索首页
- 简洁搜索框，支持模糊搜索
- 浅色风格，白色背景，蓝色主色调（#4a7cf0）
- 搜索结果以列表形式展示候选公司，用户点击选择

### 公司详情页
- 公司基本信息头部（名称、行业、注册资本）—— MVP 不展示综合评分
- Tab 导航：工商信息 / 法律风险 / 员工评价 / 舆情风评
- 各模块独立加载：完成前显示 loading 状态，失败显示错误提示
- 轮询超过 120 秒未完成时提示用户重试

---

## 10. 关键设计决策

### 为什么选择实时爬取而非预建数据库
用户按需查询时才发起爬取，避免维护庞大数据库，适合 MVP 阶段验证可行性。

### 为什么选择 asyncio 而非 Celery（MVP）
减少基础设施复杂度（不需要 Redis），单进程内用 `asyncio.create_task` 并行运行四个爬虫。后续扩展时只需替换调度层。

### 缓存策略
- 缓存有效期 24 小时（公司信息变化频率低）
- 以统一社会信用代码为缓存 key（全局唯一）
- 各模块数据独立存储，支持部分更新

---

## 11. MVP 边界（不在范围内）

- 用户账号/登录系统
- 公司综合评分（详情页不展示该字段）
- 移动端 App
- 付费 API 接入
- 数据历史追踪
- 需要登录态的爬虫内容（脉脉付费内容等）
