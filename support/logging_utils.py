# 控制台日志和阶段时间线都统一由这个模块维护。
# 同一份日志数据会同时服务于终端输出、GitHub Actions Summary 和异常排查。
from __future__ import annotations

from typing import Iterable

from core.models import StageLog
from support.time_utils import format_datetime, now_in_timezone


class RunLogger:
    # 这个日志器既负责把日志打印到控制台，也负责保留结构化时间线。
    def __init__(self, timezone_name: str, time_format: str) -> None:
        self.timezone_name = timezone_name
        self.time_format = time_format
        self.timeline: list[StageLog] = []

    def _emit(self, level: str, stage: str, message: str) -> None:
        # 每条日志在写出前都会生成统一格式的时间戳文本。
        timestamp_text = format_datetime(
            now_in_timezone(self.timezone_name), self.time_format
        )
        line = f"[{timestamp_text}] [{level}] [{stage}] {message}"
        print(line)
        # 原始输出行和结构化字段会同时保存，其他模块可以直接复用这些数据。
        self.timeline.append(
            StageLog(
                level=level,
                stage=stage,
                message=message,
                timestamp_text=timestamp_text,
                raw_line=line,
            )
        )

    def info(self, stage: str, message: str) -> None:
        # 普通流程提示统一使用 INFO 级别。
        self._emit("INFO", stage, message)

    def success(self, stage: str, message: str) -> None:
        # 阶段明确成功时使用 SUCCESS 级别，方便在 Summary 中快速识别。
        self._emit("SUCCESS", stage, message)

    def error(self, stage: str, message: str) -> None:
        # 所有失败和异常提示都必须带上阶段名，便于在日志中直接定位。
        self._emit("ERROR", stage, message)

    def dump_lines(self) -> list[str]:
        # 这里返回按顺序保存的原始日志行，供外部直接复用。
        return [item.raw_line for item in self.timeline]

    def extend_context(self, stage: str, lines: Iterable[str]) -> None:
        # 多行上下文信息会逐行写入，保证每一行都带有统一的阶段和时间戳。
        for line in lines:
            self.info(stage, line)
