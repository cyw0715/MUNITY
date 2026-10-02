// 文件下载展示名工具。
//
// 服务端的存储名是 `{32位uuid}_{原始文件名}`（uuid 前缀用于防重名与路径攻击），
// 下载时应当还原成原始名 —— 与后端 utils/security.py 的 original_display_name 保持一致。
// 浏览器用 <a download="..."> 保存文件时会忽略响应头里的 Content-Disposition，
// 所以还原必须在设置 a.download 之前由前端完成。
const STORED_PREFIX_RE = /^[0-9a-f]{32}_(.+)$/

export function displayFileName(storedName) {
  const matched = STORED_PREFIX_RE.exec(storedName || '')
  return matched ? matched[1] : storedName
}
