# 这个模块定义主流程内部使用的结构化异常类型。
# 异常对象会同时携带阶段名、错误详情、接口名和最终状态，方便主流程统一收口处理。
from __future__ import annotations


class WorkflowError(Exception):
    # detail 直接保存最终需要展示给日志、通知和 Summary 的错误说明。
    def __init__(
        self,
        stage: str,
        detail: str,
        endpoint_name: str = "",
        final_status: str = "failure",
    ) -> None:
        super().__init__(detail)
        # stage 表示当前错误发生的业务阶段。
        self.stage = stage
        # detail 保存当前阶段最明确的失败或异常说明。
        self.detail = detail
        # endpoint_name 用于在接口失败场景里记录出错接口名称。
        self.endpoint_name = endpoint_name
        # final_status 决定主流程在捕获异常后应当记录的最终状态。
        self.final_status = final_status
