import uuid
import time
from datetime import datetime
from typing import Optional

from .models import Skill, ExecutionResult, ExecutionStep, SkillStatus
from .parser import StepParser
from .simulator import SystemSimulator


class SkillExecutor:
    """
    技能执行器 - 负责技能的执行逻辑
    """

    def __init__(self):
        self.executions: dict[str, ExecutionResult] = {}
        self.parser = StepParser()
        self.simulator = SystemSimulator()

    def execute(self, skill: Skill, args: Optional[str] = None) -> ExecutionResult:
        """执行技能"""
        execution_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()

        result = ExecutionResult(
            execution_id=execution_id,
            skill_id=skill.id,
            skill_name=skill.name,
            status=SkillStatus.RUNNING,
            input_args=args,
            started_at=started_at,
            affected_systems=skill.affected_systems,
            requires_approval=skill.requires_approval,
        )

        steps = self.parser.parse(skill.prompt)

        try:
            for i, step_desc in enumerate(steps):
                step = self._execute_step(skill, i, step_desc, args)
                result.steps.append(step)

            # 生成最终结果
            result.final_result = self.simulator.get_final_result(skill.name, args)

            # 检查是否需要审批
            if skill.requires_approval:
                result.status = SkillStatus.AWAITING_APPROVAL
                result.approval_status = "pending"
            else:
                result.status = SkillStatus.SUCCESS

        except Exception as e:
            result.status = SkillStatus.ERROR
            result.error = str(e)
            if result.steps:
                result.steps[-1].status = SkillStatus.ERROR

        result.completed_at = datetime.now()
        result.total_duration_ms = (result.completed_at - started_at).total_seconds() * 1000

        self.executions[execution_id] = result
        return result

    def _execute_step(
        self, skill: Skill, step_idx: int, step_desc: str, args: Optional[str]
    ) -> ExecutionStep:
        """执行单个步骤"""
        step_start = time.time()

        step = ExecutionStep(
            step_id=step_idx + 1,
            action=step_desc,
            detail=f"执行中: {step_desc}",
            status=SkillStatus.RUNNING,
        )

        # 模拟系统操作
        system_ops = self.simulator.simulate_operations(
            skill.name, step_idx, skill.affected_systems
        )
        step.system_operations = system_ops

        # 模拟步骤执行
        time.sleep(0.05)
        step_result = self.simulator.get_step_result(skill.name, step_idx, args)

        step.status = SkillStatus.SUCCESS
        step.result = step_result
        step.duration_ms = (time.time() - step_start) * 1000
        step.detail = f"已完成: {step_desc}"

        # 更新系统操作状态
        for op in step.system_operations:
            op.status = SkillStatus.SUCCESS
            op.duration_ms = (
                step.duration_ms / len(step.system_operations)
                if step.system_operations
                else 0
            )

        return step

    def approve(
        self, execution_id: str, approved: bool, approved_by: str = "运营总监"
    ) -> Optional[ExecutionResult]:
        """审批执行结果"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None

        if approved:
            execution.status = SkillStatus.SUCCESS
            execution.approval_status = "approved"
        else:
            execution.status = SkillStatus.REJECTED
            execution.approval_status = "rejected"

        execution.approved_by = approved_by
        return execution

    def get(self, execution_id: str) -> Optional[ExecutionResult]:
        """获取执行结果"""
        return self.executions.get(execution_id)

    def get_all(self) -> list[ExecutionResult]:
        """获取所有执行结果"""
        return list(self.executions.values())
