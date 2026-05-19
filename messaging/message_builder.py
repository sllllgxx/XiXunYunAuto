# 这个模块统一生成消息推送的标题和正文。
# 主流程只提供结构化快照数据，不直接拼接通知文本。
from __future__ import annotations

from core.models import ExecutionSnapshot


DEFAULT_TITLES = {
    # 不同最终状态对应的默认标题统一在这里维护。
    "success": "习讯云签到成功",
    "failure": "习讯云签到失败",
    "exception": "习讯云签到异常",
    "repeated": "习讯云重复签到",
}


def build_message(
    snapshot: ExecutionSnapshot, layout_config: dict[str, list[str]]
) -> dict[str, str]:
    # 标题按最终状态选取。
    # 当前实现中的正文仍然按固定四段结构生成，layout_config 参数不会改变正文编排。
    title = snapshot.final_title or DEFAULT_TITLES.get(
        snapshot.final_status, "习讯云签到异常"
    )
    body = _compose_body(snapshot)
    return {
        "title": title,
        "current_time": snapshot.current_time_text,
        "body": body,
    }


def _compose_body(snapshot: ExecutionSnapshot) -> str:
    # 推送正文固定由结果、本月签到记录、用户资料和消息来源四个区块组成。
    sections = [
        _build_result_section(snapshot),
        _build_recent_signs_section(snapshot),
        _build_user_section(snapshot),
        _build_source_section(snapshot),
    ]
    normalized_sections = [section for section in sections if section]
    return "\n\n".join(normalized_sections).strip()


def _build_result_section(snapshot: ExecutionSnapshot) -> str:
    # 结果区块会优先展示积分摘要、接口结果和验证结果。
    lines: list[str] = []

    score_summary = _build_score_summary_line(snapshot)
    if score_summary:
        lines.append(score_summary)

    _append_combined_line(
        lines, [("当前积分", snapshot.point), ("积分排名", snapshot.point_rank)]
    )

    result_label = _get_result_label(snapshot)
    if result_label:
        lines.append(result_label)

    _append_labeled_line(lines, "发起签到接口业务码", snapshot.sign_api_code)
    _append_labeled_line(lines, "发起签到接口消息", snapshot.sign_api_message)
    _append_labeled_line(lines, "签到查询接口消息", snapshot.verify_query_message)

    if not lines:
        # 缺少可展示结果时，至少补出失败或异常原因。
        reason_line = _build_reason_line(snapshot)
        if reason_line:
            lines.append(reason_line)

    return "\n".join(lines).strip()


def _build_recent_signs_section(snapshot: ExecutionSnapshot) -> str:
    # 最近签到记录最多展示快照里已经整理好的几条时间文本。
    if not snapshot.recent_sign_times:
        return "无法获取本月最近签到记录"
    count = len(snapshot.recent_sign_times)
    lines = ["本月最近" + str(count) + "次签到时间："]
    lines.extend(
        _normalize_text(item)
        for item in snapshot.recent_sign_times
        if _normalize_text(item)
    )
    return "\n".join(lines).strip()


def _build_user_section(snapshot: ExecutionSnapshot) -> str:
    # 用户信息区块只展示当前快照中已经成功拿到的资料字段。
    lines: list[str] = []
    _append_combined_line(
        lines, [("用户ID", snapshot.user_id), ("学号", snapshot.user_number)]
    )
    _append_combined_line(
        lines, [("姓名", snapshot.user_name), ("班级", snapshot.class_name)]
    )
    _append_combined_line(
        lines,
        [("入学年份", snapshot.entrance_year), ("毕业年份", snapshot.graduation_year)],
    )
    return "\n".join(lines).strip()


def _build_source_section(snapshot: ExecutionSnapshot) -> str:
    # 来源区块用于说明消息来自哪个运行环境，以及是否触发了强制推送。
    lines: list[str] = []
    _append_labeled_line(lines, "消息推送来源", snapshot.environment_label)
    force_push_line = _build_force_push_line(snapshot)
    if force_push_line:
        lines.append(force_push_line)
    return "\n".join(lines).strip()


def _build_score_summary_line(snapshot: ExecutionSnapshot) -> str:
    # 积分摘要会把本次积分、本月签到天数和连续签到天数压缩到同一行展示。
    parts = _collect_value_parts(
        [
            ("本次签到获得 {value} 积分", snapshot.sign_point),
            ("本月已签到 {value} 天", snapshot.sign_in_month_count),
            ("连续签到 {value} 天", snapshot.continuous_sign_in),
        ]
    )
    return "，".join(parts).strip()


def _get_result_label(snapshot: ExecutionSnapshot) -> str:
    # 最终状态标签统一在这里映射成可直接展示的中文文本。
    labels = {
        "success": "本次结果：签到成功",
        "failure": "本次结果：签到失败",
        "exception": "本次结果：签到异常",
        "repeated": "本次结果：重复签到",
    }
    return labels.get(snapshot.final_status, "本次结果：签到异常")


def _build_force_push_line(snapshot: ExecutionSnapshot) -> str:
    # 强制推送状态固定输出为完整句子，避免正文里出现空白。
    if snapshot.force_push_active:
        return "本次消息为强制推送"
    return "本次消息不是强制推送"


def _build_reason_line(snapshot: ExecutionSnapshot) -> str:
    # 原因说明只在快照里存在有效文本时才输出。
    reason_text = _normalize_text(snapshot.reason)
    if reason_text:
        return f"原因说明：{reason_text}"
    return ""


def _normalize_text(value: object) -> str:
    # 所有进入正文的值都会先在这里做空值和空白清理。
    if value is None:
        return ""
    return str(value).strip()


def _append_labeled_line(lines: list[str], label: str, value: object) -> None:
    # 只有值非空时才追加带标签的单行文本，避免正文出现空标签。
    text = _normalize_text(value)
    if text:
        lines.append(f"{label}：{text}")


def _collect_value_parts(patterns: list[tuple[str, object]]) -> list[str]:
    # 模板片段只有在值非空时才参与结果行拼接。
    parts: list[str] = []
    for pattern, value in patterns:
        text = _normalize_text(value)
        if text:
            parts.append(pattern.format(value=text))
    return parts


def _append_combined_line(
    lines: list[str], field_pairs: list[tuple[str, object]]
) -> None:
    # 同一语义层级的字段会合并到一行，并用中文逗号连接。
    parts = [
        f"{label}：{text}"
        for label, value in field_pairs
        if (text := _normalize_text(value))
    ]
    if parts:
        lines.append("，".join(parts))
