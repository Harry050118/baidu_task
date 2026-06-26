# 地图安全接入说明

## 当前状态

`MapWorkspace.vue` 使用 SVG 散点占位适配器（`PlaceholderAdapter`）。  
无真实地图 SDK 接入，无任何密钥。

## 接入真实地图（如高德 JS API）

1. 在后端统一管理 Key，或通过安全代理加载 JS SDK URL（不得在前端硬编码 `key=` 参数）。
2. 实现 `MapAdapter` 接口（`src/map/adapter.ts`），创建独立适配器文件。
3. 在 `MapWorkspace.vue` 中按条件切换适配器。
4. **禁止**在此目录或任何前端文件中硬编码高德 Key（Web Service Key 或 JS API Key）。
