/**
 * 动议类型：内置定义与解析规则。
 *
 * 约定：委员会表的 motion_types 保存的是**完整列表**（内置 + 自定义）。
 * 因此只要存储非空，就以存储内容为准——被删除的内置类型不会自动回来。
 * 仅当从未配置（存储为空）时，才回退到内置默认，保证新委员会可用。
 */
export const BUILTIN_TYPES = [
  { name: '有主持核心磋商', key: 'moderated_caucus', need_speakers_list: true, need_unit_duration: true, need_total_duration: true, default_unit_duration: 60, default_total_duration: 300 },
  { name: '自由辩论', key: 'unmoderated_caucus', need_speakers_list: true, need_unit_duration: true, need_total_duration: true, default_unit_duration: 60, default_total_duration: 300 },
  { name: '自由磋商', key: 'free_caucus', need_speakers_list: false, need_unit_duration: false, need_total_duration: true, default_unit_duration: 0, default_total_duration: 600 },
]

/** 内置类型的中文名 -> 后端固定 type key，用于提交动议时定位内置类型 */
export const BUILTIN_KEY_BY_LABEL = {
  有主持核心磋商: 'moderated_caucus',
  自由辩论: 'unmoderated_caucus',
  自由磋商: 'free_caucus',
}

const BUILTIN_NAMES = new Set(BUILTIN_TYPES.map(t => t.name))

export function isBuiltinName(name) {
  return BUILTIN_NAMES.has(name)
}

/** 内置默认（去掉仅供前端使用的 key 字段） */
export function defaultMotionTypes() {
  return BUILTIN_TYPES.map(({ key, ...rest }) => ({ ...rest, is_builtin: true }))
}

/**
 * 解析委员会存储的动议类型。
 *
 * - 已配置过（configured=true）：完全以存储内容为准，**允许为空**，
 *   这样删掉全部内置类型也不会被重新加回来。
 * - 从未配置：回退内置默认，保证新委员会开箱可用。
 *
 * @param {Array} stored 委员会表里的 motion_types
 * @param {boolean} configured 委员会是否配置过动议类型
 */
export function resolveMotionTypes(stored, configured) {
  const list = Array.isArray(stored) ? stored : []
  if (!configured && list.length === 0) {
    return defaultMotionTypes()
  }
  return list.map(t => ({ ...t, is_builtin: isBuiltinName(t.name) }))
}

/** 保存前剥离前端专用字段（key 仅表示内置类型的后端 type，不入库） */
export function toStoredMotionTypes(list) {
  return list.map(({ is_builtin, key, ...rest }) => rest)
}

/**
 * 把动议类型拆成下拉框的两组选项。
 * 被删除的内置类型不在 list 中，因此不会出现在选项里。
 */
export function splitMotionTypeOptions(list) {
  return {
    builtinOptions: list
      .filter(m => BUILTIN_KEY_BY_LABEL[m.name])
      .map(m => ({ label: m.name, value: BUILTIN_KEY_BY_LABEL[m.name] })),
    customOptions: list.filter(m => !BUILTIN_KEY_BY_LABEL[m.name]),
  }
}
