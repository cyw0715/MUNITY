/**
 * 文件类型：内置定义与解析规则。
 *
 * 与动议类型同一套约定：委员会表的 document_types 保存**完整列表**（内置 + 自定义），
 * document_types_configured 区分「从未配置」与「配置后删空」。
 *
 * 每种类型的四项配置：
 * - endorsement: 'required' 强制联署 / 'optional' 可选联署 / 'none' 不需要联署
 * - need_secrecy: 是否选择密级
 * - need_departments: 是否选择涉及部门
 */
export const ENDORSEMENT_REQUIRED = 'required'
export const ENDORSEMENT_OPTIONAL = 'optional'
export const ENDORSEMENT_NONE = 'none'

export const ENDORSEMENT_LABELS = {
  required: '强制联署',
  optional: '可选联署',
  none: '不需要联署',
}

export const BUILTIN_DOCUMENT_TYPES = [
  { name: '声明', key: 'declaration', endorsement: ENDORSEMENT_OPTIONAL, need_secrecy: false, need_departments: false },
  { name: '备忘录', key: 'memorandum', endorsement: ENDORSEMENT_OPTIONAL, need_secrecy: false, need_departments: false },
  { name: '协定', key: 'agreement', endorsement: ENDORSEMENT_REQUIRED, need_secrecy: true, need_departments: false },
]

const BUILTIN_KEY_BY_NAME = Object.fromEntries(BUILTIN_DOCUMENT_TYPES.map(t => [t.name, t.key]))

export function isBuiltinDocTypeName(name) {
  return name in BUILTIN_KEY_BY_NAME
}

export function builtinKeyOf(name) {
  return BUILTIN_KEY_BY_NAME[name]
}

function normalize(t) {
  const e = { ...(t || {}) }
  if (![ENDORSEMENT_REQUIRED, ENDORSEMENT_OPTIONAL, ENDORSEMENT_NONE].includes(e.endorsement)) {
    e.endorsement = ENDORSEMENT_NONE
  }
  e.need_secrecy = !!e.need_secrecy
  e.need_departments = !!e.need_departments
  return e
}

export function defaultDocumentTypes() {
  return BUILTIN_DOCUMENT_TYPES.map(t => ({ ...t }))
}

/**
 * 解析委员会存储的文件类型。
 * 已配置（或已有存储内容）时以存储为准——允许为空，删掉的内置类型不会回弹；
 * 从未配置时回退内置默认，保证新委员会开箱可用。
 */
export function resolveDocumentTypes(stored, configured) {
  const list = Array.isArray(stored) ? stored : []
  if (!configured && list.length === 0) {
    return defaultDocumentTypes()
  }
  return list.map(normalize)
}

/** 保存前剥离前端专用字段（key 仅用于标识内置类型，不入库） */
export function toStoredDocumentTypes(list) {
  return list.map(({ key, ...rest }) => ({ ...rest }))
}

/** 提交文件时的 value：内置用 key，自定义用名称 */
export function docTypeValue(t) {
  return t.key || t.name
}

/** 按 value 查类型配置 */
export function findDocType(list, value) {
  if (!value) return null
  return list.find(t => docTypeValue(t) === value || t.name === value) || null
}
