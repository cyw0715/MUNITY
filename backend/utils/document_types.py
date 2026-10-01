"""文件类型：内置定义、委员会配置解析、显示名与校验规则。

与动议类型同一套约定：委员会表的 document_types 保存**完整列表**（内置 + 自定义），
document_types_configured 区分「从未配置」与「配置后删空」。

每种类型四项配置：
- endorsement: required 强制联署 / optional 可选联署 / none 不需要联署
- need_secrecy: 是否选择密级
- need_departments: 是否选择涉及部门
"""
from typing import Optional

ENDORSEMENT_REQUIRED = "required"
ENDORSEMENT_OPTIONAL = "optional"
ENDORSEMENT_NONE = "none"

BUILTIN_DOCUMENT_TYPES = [
    {
        "name": "声明",
        "key": "declaration",
        "endorsement": ENDORSEMENT_OPTIONAL,
        "need_secrecy": False,
        "need_departments": False,
    },
    {
        "name": "备忘录",
        "key": "memorandum",
        "endorsement": ENDORSEMENT_OPTIONAL,
        "need_secrecy": False,
        "need_departments": False,
    },
    {
        "name": "协定",
        "key": "agreement",
        "endorsement": ENDORSEMENT_REQUIRED,
        "need_secrecy": True,
        "need_departments": False,
    },
]

BUILTIN_KEY_BY_NAME = {t["name"]: t["key"] for t in BUILTIN_DOCUMENT_TYPES}
BUILTIN_NAME_BY_KEY = {t["key"]: t["name"] for t in BUILTIN_DOCUMENT_TYPES}


def _normalize(entry: dict) -> dict:
    """补齐缺失字段，保证每种类型都带完整的四项配置"""
    e = dict(entry or {})
    e.setdefault("name", "")
    if e.get("endorsement") not in (ENDORSEMENT_REQUIRED, ENDORSEMENT_OPTIONAL, ENDORSEMENT_NONE):
        e["endorsement"] = ENDORSEMENT_NONE
    e["need_secrecy"] = bool(e.get("need_secrecy", False))
    e["need_departments"] = bool(e.get("need_departments", False))
    return e


def resolve_document_types(committee) -> list:
    """该委员会实际生效的文件类型列表。

    已配置（或已有存储内容）时以存储为准——允许为空，删掉的内置类型不会回弹；
    从未配置时回退内置默认，保证新委员会开箱可用。
    """
    stored = getattr(committee, "document_types", None)
    configured = bool(getattr(committee, "document_types_configured", False))
    if isinstance(stored, list) and (configured or stored):
        return [_normalize(t) for t in stored]
    return [_normalize(t) for t in BUILTIN_DOCUMENT_TYPES]


def find_document_type(committee, doc_type: str) -> Optional[dict]:
    """按 doc_type 查配置。内置类型用 key 匹配，自定义类型用名称匹配。"""
    if not doc_type:
        return None
    for t in resolve_document_types(committee):
        key = t.get("key") or BUILTIN_KEY_BY_NAME.get(t.get("name", ""))
        if doc_type in (key, t.get("name")):
            return t
    return None


def document_type_label(committee, doc_type: str) -> str:
    """文件类型的显示名；未匹配到配置时原样返回，保证自定义类型也能展示"""
    t = find_document_type(committee, doc_type)
    if t:
        return t.get("name") or doc_type
    return BUILTIN_NAME_BY_KEY.get(doc_type, doc_type)
