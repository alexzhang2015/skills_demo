import re


class StepParser:
    """
    步骤解析器 - 从Skill prompt中解析执行步骤
    """

    def parse(self, prompt: str) -> list[str]:
        """从prompt中解析执行步骤"""
        lines = prompt.split('\n')
        steps = []
        in_steps_section = False

        for line in lines:
            line = line.strip()
            if '执行步骤' in line or 'Steps' in line:
                in_steps_section = True
                continue
            if in_steps_section and line.startswith('#'):
                in_steps_section = False
                continue
            if in_steps_section and re.match(r'^\d+\.', line):
                step_text = re.sub(r'^\d+\.\s*', '', line)
                steps.append(step_text)

        return steps if steps else ["执行Skill指令"]
