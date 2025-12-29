"""
Layer 1: Master Agent 层 (意图路由)

职责:
- 理解用户自然语言输入
- 分析意图并提取实体
- 规划执行方案，分配给合适的子Agent
- 协调多个子Agent的协作
- 汇总结果并回报用户
"""

import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from ..models import (
    IntentAnalysis,
    ExecutionPlan,
    MasterAgentSession,
    SubAgentTask,
    ExecutionStatus,
)

if TYPE_CHECKING:
    from .sub_agents import SubAgentManager


class MasterAgent:
    """总部运营 Master Agent"""

    # 意图识别规则
    INTENT_PATTERNS = {
        "product_launch": {
            "keywords": ["上市", "新品", "发布", "推出", "首发", "上线新"],
            "required_agents": ["product-agent"],
            "optional_agents": ["pricing-agent", "marketing-agent"],
        },
        "menu_config": {
            "keywords": ["菜品", "菜单", "新增菜", "添加菜", "配置菜"],
            "required_agents": ["product-agent"],
            "optional_agents": [],
        },
        "price_adjust": {
            "keywords": ["涨价", "降价", "调价", "价格调整", "定价"],
            "required_agents": ["pricing-agent"],
            "optional_agents": [],
        },
        "campaign_setup": {
            "keywords": ["活动", "促销", "满减", "优惠", "打折", "折扣"],
            "required_agents": ["marketing-agent"],
            "optional_agents": [],
        },
        "report_gen": {
            "keywords": ["报告", "报表", "周报", "月报", "分析", "统计"],
            "required_agents": ["analytics-agent"],
            "optional_agents": [],
        },
        "inventory_check": {
            "keywords": ["库存", "盘点", "备货", "缺货"],
            "required_agents": ["supply-chain-agent"],
            "optional_agents": [],
        },
        "clearance_sale": {
            "keywords": ["清仓", "临期", "过期", "处理库存", "库存清理"],
            "required_agents": ["supply-chain-agent", "pricing-agent"],
            "optional_agents": ["marketing-agent"],
        },
        "seasonal_launch": {
            "keywords": ["季节", "限定", "夏季", "冬季", "春季", "秋季", "节日"],
            "required_agents": ["product-agent", "marketing-agent"],
            "optional_agents": ["pricing-agent"],
        },
    }

    # 运营场景模板库
    SCENARIO_TEMPLATES = {
        "seasonal_new_product": {
            "id": "seasonal_new_product",
            "name": "季节性新品发布",
            "description": "适用于季节限定新品的全国/区域上市",
            "category": "product",
            "icon": "🌸",
            "color": "blue",
            "template": "{season}限定{product}产品，{date}{region}上市，定价{price}元",
            "required_entities": ["product", "date", "region"],
            "optional_entities": ["price", "season"],
            "example": "夏季限定芒果系列产品，6月1日全国上市，定价28元",
            "default_values": {
                "region": "全国",
                "season": "夏季",
            },
            "estimated_impact": {
                "stores": 2847,
                "skus": 5,
                "duration_hours": 2,
            },
        },
        "holiday_promotion": {
            "id": "holiday_promotion",
            "name": "节日促销",
            "description": "适用于春节、国庆等节日期间的促销活动",
            "category": "campaign",
            "icon": "🎉",
            "color": "pink",
            "template": "配置{holiday}满{threshold}减{reduction}活动，{start_date}至{end_date}，{region}门店参与",
            "required_entities": ["holiday", "discount"],
            "optional_entities": ["date_range", "region"],
            "example": "配置春节满100减20活动，1月20日至2月10日，全国门店参与",
            "default_values": {
                "region": "全国",
            },
            "estimated_impact": {
                "stores": 2847,
                "skus": 50,
                "duration_hours": 1,
            },
        },
        "inventory_clearance": {
            "id": "inventory_clearance",
            "name": "库存清仓",
            "description": "适用于临期产品或过季产品的折扣清仓",
            "category": "supply_chain",
            "icon": "📦",
            "color": "amber",
            "template": "临期产品{discount_percent}折清仓，涉及{region}{sku_count}个SKU，{duration}，{effective_date}生效",
            "required_entities": ["discount_percent", "region"],
            "optional_entities": ["sku_count", "duration", "effective_date"],
            "example": "临期产品7折清仓，涉及华北区3个SKU，为期一周，明天生效",
            "default_values": {
                "duration": "一周",
                "effective_date": "明天",
            },
            "estimated_impact": {
                "stores": 521,
                "skus": 3,
                "duration_hours": 0.5,
            },
        },
        "regional_price_adjust": {
            "id": "regional_price_adjust",
            "name": "区域调价",
            "description": "适用于特定区域的产品价格批量调整",
            "category": "pricing",
            "icon": "💰",
            "color": "green",
            "template": "{region}全线{category}产品{adjust_type}{percentage}%，{effective_date}生效",
            "required_entities": ["region", "percentage"],
            "optional_entities": ["category", "adjust_type", "effective_date"],
            "example": "华东区全线汉堡产品涨价5%，下周一生效",
            "default_values": {
                "category": "全部",
                "adjust_type": "涨价",
                "effective_date": "下周一",
            },
            "estimated_impact": {
                "stores": 892,
                "skus": 15,
                "duration_hours": 1.5,
            },
        },
        "competitive_pricing": {
            "id": "competitive_pricing",
            "name": "竞品定价策略",
            "description": "根据竞品价格制定产品定价策略",
            "category": "pricing",
            "icon": "⚔️",
            "color": "purple",
            "template": "{product}定价比竞品{compare_type}{diff_amount}元，{region}市场",
            "required_entities": ["product", "competitor_reference"],
            "optional_entities": ["region"],
            "example": "川香麻辣鸡腿堡定价比竞品低2元，全国市场",
            "default_values": {
                "region": "全国",
            },
            "estimated_impact": {
                "stores": 2847,
                "skus": 1,
                "duration_hours": 1,
            },
        },
        "new_store_opening": {
            "id": "new_store_opening",
            "name": "新店开业",
            "description": "新门店开业促销活动配置",
            "category": "campaign",
            "icon": "🏪",
            "color": "cyan",
            "template": "配置{store_name}开业促销，全场{discount_percent}折，持续{duration}天，送{gift}",
            "required_entities": ["store_name", "discount_percent"],
            "optional_entities": ["duration", "gift"],
            "example": "配置上海新天地店开业促销，全场8折，持续3天，送开业礼品",
            "default_values": {
                "duration": "3",
                "gift": "开业礼品",
            },
            "estimated_impact": {
                "stores": 1,
                "skus": 100,
                "duration_hours": 0.5,
            },
        },
    }

    # 实体提取规则
    ENTITY_PATTERNS = {
        "product_name": r'[\u300c\u201c"\']?([^\u300c\u300d\u201c\u201d"\'\u2018\u2019]+?)[\u300d\u201d"\']?(?:产品|新品|菜品)?',
        "price": r"(?:定价|价格|售价)?[\uff1a:]?\s*(?:\u00a5)?(\d+(?:\.\d{1,2})?)\s*元?",
        "date": r"(\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        "region": r"(全国|华东|华南|华北|华中|西南|西北|东北|[^\uff0c,]+区)",
        "percentage": r"(\d+(?:\.\d{1,2})?)\s*[%\uff05]",
        "discount": r"满(\d+)减(\d+)",
    }

    # 区域门店数量映射
    REGION_STORE_COUNT = {
        "全国": 2847,
        "华东": 892,
        "华南": 634,
        "华北": 521,
        "华中": 312,
        "西南": 245,
        "西北": 128,
        "东北": 115,
    }

    # 相对日期映射
    RELATIVE_DATE_PATTERNS = {
        "今天": 0,
        "明天": 1,
        "后天": 2,
        "大后天": 3,
        "下周一": "next_monday",
        "下周二": "next_tuesday",
        "下周三": "next_wednesday",
        "下周四": "next_thursday",
        "下周五": "next_friday",
        "下周六": "next_saturday",
        "下周日": "next_sunday",
        "本周一": "this_monday",
        "本周二": "this_tuesday",
        "本周三": "this_wednesday",
        "本周四": "this_thursday",
        "本周五": "this_friday",
        "本周六": "this_saturday",
        "本周日": "this_sunday",
        "下个月": "next_month",
        "月底": "end_of_month",
        # 新增模式
        "下下周一": "next_next_monday",
        "下下周二": "next_next_tuesday",
        "下下周三": "next_next_wednesday",
        "下下周四": "next_next_thursday",
        "下下周五": "next_next_friday",
        "两周后": "two_weeks_later",
        "一周后": "one_week_later",
        "月初": "start_of_month",
        "季末": "end_of_quarter",
        "下季度": "next_quarter",
    }

    def __init__(self, sub_agent_manager: "SubAgentManager"):
        self.sub_agent_manager = sub_agent_manager
        self.sessions: dict[str, MasterAgentSession] = {}

    def process(self, user_input: str) -> MasterAgentSession:
        """处理用户输入"""
        session_id = str(uuid.uuid4())[:8]
        session = MasterAgentSession(
            session_id=session_id,
            user_input=user_input,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            # Step 1: 意图分析
            intent_analysis = self._analyze_intent(user_input)
            session.intent_analysis = intent_analysis

            # Step 2: 生成执行计划
            execution_plan = self._create_execution_plan(intent_analysis)
            session.execution_plan = execution_plan

            # Step 3: 分配任务给子Agent
            agent_tasks = self._dispatch_to_agents(execution_plan, intent_analysis.entities)
            session.agent_tasks = agent_tasks

            # Step 4: 执行任务
            for task in agent_tasks:
                executed_task = self.sub_agent_manager.execute_task(task.task_id)

                # 如果需要审批，暂停会话
                if executed_task.status == ExecutionStatus.AWAITING_APPROVAL:
                    session.status = ExecutionStatus.AWAITING_APPROVAL
                    session.pending_approvals.append(task.task_id)

            # Step 5: 汇总结果
            if session.status != ExecutionStatus.AWAITING_APPROVAL:
                session.status = ExecutionStatus.SUCCESS
                session.final_result = self._generate_summary(session)
                session.summary = self._generate_brief_summary(session)

        except Exception as e:
            session.status = ExecutionStatus.ERROR
            session.final_result = f"执行失败: {str(e)}"

        session.completed_at = datetime.now() if session.status != ExecutionStatus.AWAITING_APPROVAL else None
        if session.completed_at:
            session.total_duration_ms = (session.completed_at - session.started_at).total_seconds() * 1000

        self.sessions[session_id] = session
        return session

    def _analyze_intent(self, user_input: str) -> IntentAnalysis:
        """分析用户意图"""
        input_lower = user_input.lower()

        # 识别意图类型
        intent_type = "unknown"
        confidence = 0.0
        required_agents = []
        optional_agents = []

        for intent, config in self.INTENT_PATTERNS.items():
            matches = sum(1 for kw in config["keywords"] if kw in input_lower)
            if matches > 0:
                score = matches / len(config["keywords"])
                if score > confidence:
                    confidence = score
                    intent_type = intent
                    required_agents = config["required_agents"]
                    optional_agents = config["optional_agents"]

        # 提取实体
        entities = self._extract_entities(user_input)

        # 根据实体调整需要的Agent
        all_agents = required_agents.copy()
        if entities.get("price") and "pricing-agent" not in all_agents:
            all_agents.append("pricing-agent")
        if entities.get("discount") and "marketing-agent" not in all_agents:
            all_agents.append("marketing-agent")

        # 确定建议的工作流
        suggested_workflows = []
        for agent_id in all_agents:
            agent = self.sub_agent_manager.get_agent(agent_id)
            if agent:
                suggested_workflows.extend(agent.available_workflows)

        return IntentAnalysis(
            original_input=user_input,
            intent_type=intent_type,
            confidence=min(confidence + 0.3, 1.0),  # 调整置信度
            entities=entities,
            required_agents=all_agents,
            suggested_workflows=list(dict.fromkeys(suggested_workflows)),
        )

    def _extract_entities(self, text: str) -> dict:
        """从文本中提取实体"""
        entities = {}

        # 提取价格
        price_match = re.search(r"(?:定价|价格|售价)?[：:]?\s*(?:¥)?(\d+(?:\.\d{1,2})?)\s*元?", text)
        if price_match:
            entities["price"] = float(price_match.group(1))

        # 提取相对日期 (优先于绝对日期)
        relative_date = self._extract_relative_date(text)
        if relative_date:
            entities["date"] = relative_date
            entities["relative_date_original"] = relative_date.get("original")
        else:
            # 提取绝对日期
            date_match = re.search(r"(\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
            if date_match:
                entities["date"] = date_match.group(1)

        # 提取区域
        region_match = re.search(r"(全国|华东|华南|华北|华中|西南|西北|东北)", text)
        if region_match:
            entities["region"] = region_match.group(1)

        # 提取百分比
        percent_match = re.search(r"(\d+(?:\.\d{1,2})?)\s*[%％]", text)
        if percent_match:
            entities["percentage"] = float(percent_match.group(1))

        # 提取满减规则
        discount_match = re.search(r"满(\d+)减(\d+)", text)
        if discount_match:
            entities["discount"] = {
                "threshold": int(discount_match.group(1)),
                "reduction": int(discount_match.group(2)),
            }

        # 提取产品系列
        series_match = self._extract_product_series(text)
        if series_match:
            entities["product_series"] = series_match

        # 提取竞品参照
        competitor_ref = self._extract_competitor_reference(text)
        if competitor_ref:
            entities["competitor_reference"] = competitor_ref

        # 提取数量词
        quantities = self._extract_quantities(text)
        if quantities:
            entities.update(quantities)

        # 提取产品名称 (简单启发式)
        # 尝试从引号中提取
        quoted = re.search(r'[\u300c\u201c\'\u300a]([^\u300d\u201d\'\u300b]+)[\u300d\u201d\'\u300b]', text)
        if quoted:
            entities["product_name"] = quoted.group(1)
        else:
            # 尝试从"上市/发布/新品"后面提取
            product_match = re.search(r'(?:上市|发布|新品|推出)[\uff1a:\u662f]?\s*([^\uff0c,\u3002\s]+)', text)
            if product_match:
                entities["product_name"] = product_match.group(1)

        return entities

    def _extract_relative_date(self, text: str) -> Optional[dict]:
        """提取相对日期并转换为具体日期"""
        today = datetime.now()
        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }

        for pattern, offset in self.RELATIVE_DATE_PATTERNS.items():
            if pattern in text:
                target_date = None

                if isinstance(offset, int):
                    # 简单天数偏移
                    target_date = today + timedelta(days=offset)
                elif isinstance(offset, str):
                    if offset.startswith("next_next_"):
                        # 下下周X
                        weekday_name = offset.replace("next_next_", "")
                        target_weekday = weekday_map.get(weekday_name, 0)
                        days_ahead = target_weekday - today.weekday() + 14
                        if days_ahead <= 7:
                            days_ahead += 7
                        target_date = today + timedelta(days=days_ahead)
                    elif offset.startswith("next_"):
                        # 下周X
                        weekday_name = offset.replace("next_", "")
                        target_weekday = weekday_map.get(weekday_name, 0)
                        days_ahead = target_weekday - today.weekday() + 7
                        if days_ahead <= 0:
                            days_ahead += 7
                        target_date = today + timedelta(days=days_ahead)
                    elif offset.startswith("this_"):
                        # 本周X
                        weekday_name = offset.replace("this_", "")
                        target_weekday = weekday_map.get(weekday_name, 0)
                        days_diff = target_weekday - today.weekday()
                        target_date = today + timedelta(days=days_diff)
                    elif offset == "next_month":
                        # 下个月1日
                        if today.month == 12:
                            target_date = today.replace(year=today.year + 1, month=1, day=1)
                        else:
                            target_date = today.replace(month=today.month + 1, day=1)
                    elif offset == "end_of_month":
                        # 本月底
                        if today.month == 12:
                            target_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                        else:
                            target_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                    elif offset == "start_of_month":
                        # 下月初
                        if today.month == 12:
                            target_date = today.replace(year=today.year + 1, month=1, day=1)
                        else:
                            target_date = today.replace(month=today.month + 1, day=1)
                    elif offset == "two_weeks_later":
                        # 两周后
                        target_date = today + timedelta(days=14)
                    elif offset == "one_week_later":
                        # 一周后
                        target_date = today + timedelta(days=7)
                    elif offset == "end_of_quarter":
                        # 季末 (当前季度最后一天)
                        quarter_end_months = {1: 3, 2: 3, 3: 3, 4: 6, 5: 6, 6: 6,
                                              7: 9, 8: 9, 9: 9, 10: 12, 11: 12, 12: 12}
                        end_month = quarter_end_months[today.month]
                        if end_month == 12:
                            target_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                        else:
                            target_date = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
                    elif offset == "next_quarter":
                        # 下季度第一天
                        quarter_start = {1: 4, 2: 4, 3: 4, 4: 7, 5: 7, 6: 7,
                                         7: 10, 8: 10, 9: 10, 10: 1, 11: 1, 12: 1}
                        start_month = quarter_start[today.month]
                        if start_month == 1:
                            target_date = today.replace(year=today.year + 1, month=1, day=1)
                        else:
                            target_date = today.replace(month=start_month, day=1)

                if target_date:
                    return {
                        "original": pattern,
                        "resolved": target_date.strftime("%Y-%m-%d"),
                        "formatted": f"{target_date.month}月{target_date.day}日",
                    }

        return None

    def _extract_product_series(self, text: str) -> Optional[str]:
        """提取产品系列"""
        # 匹配 "XX系列" 模式 (排除日期词汇)
        series_match = re.search(r"(?<!周)([一-龥]{2,6})系列", text)
        if series_match:
            # 过滤掉日期相关的错误匹配
            series_name = series_match.group(1)
            date_words = ["下周", "本周", "上周", "明天", "今天", "昨天", "后天"]
            if not any(series_name.startswith(dw) for dw in date_words):
                return series_name + "系列"

        # 匹配 "XX类产品" 模式
        category_match = re.search(r"([一-龥]{2,6})类(?:产品)?", text)
        if category_match:
            return category_match.group(1) + "类"

        # 匹配 "全线XX产品" 模式
        full_line_match = re.search(r"全线([一-龥]{2,6})(?:产品)?", text)
        if full_line_match:
            return full_line_match.group(1) + "全系"

        # 匹配常见系列名称
        common_series = ["川香", "麻辣", "香辣", "黑椒", "芝士", "照烧", "藤椒", "酸辣", "咖喱",
                         "经典", "招牌", "新品", "限定", "季节", "早餐", "套餐", "小食", "饮品"]
        for series in common_series:
            if series in text:
                return series + "系列"

        return None

    def _extract_competitor_reference(self, text: str) -> Optional[dict]:
        """提取竞品参照"""
        # 匹配 "比竞品低/高X元"
        comp_match = re.search(r"比竞品(低|高)(\d+(?:\.\d{1,2})?)\s*元", text)
        if comp_match:
            return {
                "type": "lower" if comp_match.group(1) == "低" else "higher",
                "amount": float(comp_match.group(2)),
                "reference": "竞品",
            }

        # 匹配 "比竞品低/高X%" (百分比)
        percent_match = re.search(r"比竞品(低|高)(\d+(?:\.\d{1,2})?)\s*[%％]", text)
        if percent_match:
            return {
                "type": "lower" if percent_match.group(1) == "低" else "higher",
                "percentage": float(percent_match.group(2)),
                "reference": "竞品",
            }

        # 匹配 "比XX便宜/贵X元"
        brand_match = re.search(r"比([一-龥a-zA-Z]+)(便宜|贵)(\d+(?:\.\d{1,2})?)\s*元", text)
        if brand_match:
            return {
                "type": "lower" if brand_match.group(2) == "便宜" else "higher",
                "amount": float(brand_match.group(3)),
                "reference": brand_match.group(1),
            }

        # 匹配 "比XX便宜/贵X%" (百分比)
        brand_percent_match = re.search(r"比([一-龥a-zA-Z]+)(便宜|贵)(\d+(?:\.\d{1,2})?)\s*[%％]", text)
        if brand_percent_match:
            return {
                "type": "lower" if brand_percent_match.group(2) == "便宜" else "higher",
                "percentage": float(brand_percent_match.group(3)),
                "reference": brand_percent_match.group(1),
            }

        # 匹配 "对标竞品" 表述
        if "对标竞品" in text or "参照竞品" in text or "竞品定价" in text:
            return {
                "type": "reference",
                "reference": "竞品",
            }

        return None

    def _extract_quantities(self, text: str) -> dict:
        """提取数量词"""
        quantities = {}

        # 提取SKU数量
        sku_match = re.search(r"(\d+)\s*个?\s*SKU", text, re.IGNORECASE)
        if sku_match:
            quantities["sku_count"] = int(sku_match.group(1))

        # 提取门店数量
        store_match = re.search(r"(\d+)\s*家\s*门店", text)
        if store_match:
            quantities["store_count"] = int(store_match.group(1))

        # 提取天数/周期
        duration_match = re.search(r"(?:持续|为期)\s*(\d+)\s*(天|周|个月)", text)
        if duration_match:
            value = int(duration_match.group(1))
            unit = duration_match.group(2)
            quantities["duration"] = {
                "value": value,
                "unit": unit,
                "days": value * (1 if unit == "天" else 7 if unit == "周" else 30)
            }

        return quantities

    def _create_execution_plan(self, intent: IntentAnalysis) -> ExecutionPlan:
        """创建执行计划"""
        plan_id = str(uuid.uuid4())[:8]

        # 构建Agent任务列表
        agent_tasks = []
        for i, agent_id in enumerate(intent.required_agents):
            agent = self.sub_agent_manager.get_agent(agent_id)
            if agent:
                task = {
                    "agent_id": agent_id,
                    "agent_name": agent.display_name,
                    "instruction": self._generate_agent_instruction(agent, intent),
                    "priority": i + 1,
                    "dependencies": [],  # 简单实现，暂无依赖
                }
                agent_tasks.append(task)

        # 确定执行顺序 (简单实现: 按优先级串行)
        execution_order = [[task["agent_id"]] for task in agent_tasks]

        # 确定审批点
        approval_points = []
        for agent_id in intent.required_agents:
            agent = self.sub_agent_manager.get_agent(agent_id)
            if agent and agent.requires_approval_from:
                approval_points.append(agent_id)

        return ExecutionPlan(
            plan_id=plan_id,
            intent=intent,
            agent_tasks=agent_tasks,
            execution_order=execution_order,
            approval_points=approval_points,
        )

    def _generate_agent_instruction(self, agent, intent: IntentAnalysis) -> str:
        """为子Agent生成具体指令"""
        base_instruction = intent.original_input

        # 添加实体信息
        if intent.entities:
            entity_str = ", ".join(f"{k}={v}" for k, v in intent.entities.items())
            base_instruction += f" [实体: {entity_str}]"

        return base_instruction

    def _dispatch_to_agents(self, plan: ExecutionPlan, entities: dict) -> list[SubAgentTask]:
        """将任务分发给子Agent"""
        tasks = []

        for task_config in plan.agent_tasks:
            task = self.sub_agent_manager.create_task(
                agent_id=task_config["agent_id"],
                instruction=task_config["instruction"],
                context=entities,
            )
            tasks.append(task)

        return tasks

    def _generate_summary(self, session: MasterAgentSession) -> str:
        """生成执行结果摘要"""
        lines = []
        lines.append("=" * 50)
        lines.append("执行结果摘要")
        lines.append("=" * 50)

        # 意图分析
        if session.intent_analysis:
            lines.append(f"\n📋 意图识别")
            lines.append(f"   类型: {session.intent_analysis.intent_type}")
            lines.append(f"   置信度: {session.intent_analysis.confidence:.0%}")
            if session.intent_analysis.entities:
                lines.append(f"   实体: {session.intent_analysis.entities}")

        # 执行计划
        if session.execution_plan:
            lines.append(f"\n📝 执行计划")
            for task in session.execution_plan.agent_tasks:
                lines.append(f"   → {task['agent_name']}")

        # 任务执行结果
        lines.append(f"\n🔧 任务执行")
        for task in session.agent_tasks:
            status_icon = "✅" if task.status == ExecutionStatus.SUCCESS else "⏳" if task.status == ExecutionStatus.AWAITING_APPROVAL else "❌"
            lines.append(f"   {status_icon} {task.agent_name}: {task.status.value}")

            for wf_exec in task.workflow_executions:
                lines.append(f"      └─ {wf_exec.workflow_name}: {len(wf_exec.node_executions)}个节点")

        lines.append("\n" + "=" * 50)

        return "\n".join(lines)

    def _generate_brief_summary(self, session: MasterAgentSession) -> str:
        """生成简短摘要"""
        if session.intent_analysis:
            intent = session.intent_analysis.intent_type
            agents = len(session.agent_tasks)
            workflows = sum(len(t.workflow_executions) for t in session.agent_tasks)
            return f"识别意图: {intent}, 调用{agents}个Agent, 执行{workflows}个工作流"
        return "执行完成"

    def approve_session(self, session_id: str, approved: bool, approved_by: str = "运营总监") -> Optional[MasterAgentSession]:
        """审批会话中的待审批任务"""
        session = self.sessions.get(session_id)
        if not session or session.status != ExecutionStatus.AWAITING_APPROVAL:
            return None

        # 审批所有待审批的任务
        for task_id in session.pending_approvals:
            self.sub_agent_manager.approve_task(task_id, approved, approved_by)

        session.pending_approvals = []

        if approved:
            # 检查是否还有待审批的任务
            all_complete = all(
                task.status in [ExecutionStatus.SUCCESS, ExecutionStatus.REJECTED]
                for task in session.agent_tasks
            )

            if all_complete:
                session.status = ExecutionStatus.SUCCESS
                session.final_result = self._generate_summary(session)
                session.summary = self._generate_brief_summary(session)
            else:
                # 可能还有新的审批点
                for task in session.agent_tasks:
                    if task.status == ExecutionStatus.AWAITING_APPROVAL:
                        session.pending_approvals.append(task.task_id)

                if session.pending_approvals:
                    session.status = ExecutionStatus.AWAITING_APPROVAL
                else:
                    session.status = ExecutionStatus.SUCCESS
        else:
            session.status = ExecutionStatus.REJECTED

        if session.status != ExecutionStatus.AWAITING_APPROVAL:
            session.completed_at = datetime.now()
            session.total_duration_ms = (session.completed_at - session.started_at).total_seconds() * 1000

        return session

    def get_session(self, session_id: str) -> Optional[MasterAgentSession]:
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> list[MasterAgentSession]:
        return list(self.sessions.values())

    def get_templates(self) -> list[dict]:
        """获取所有运营场景模板"""
        return list(self.SCENARIO_TEMPLATES.values())

    def get_template(self, template_id: str) -> Optional[dict]:
        """获取指定模板"""
        return self.SCENARIO_TEMPLATES.get(template_id)

    def match_template(self, user_input: str) -> Optional[dict]:
        """根据用户输入匹配最佳模板"""
        input_lower = user_input.lower()
        best_match = None
        best_score = 0

        for template_id, template in self.SCENARIO_TEMPLATES.items():
            score = 0
            # 检查模板关键词匹配
            if template["category"] == "product":
                if any(kw in input_lower for kw in ["上市", "新品", "发布", "限定"]):
                    score += 2
            elif template["category"] == "campaign":
                if any(kw in input_lower for kw in ["活动", "促销", "满减", "优惠"]):
                    score += 2
            elif template["category"] == "supply_chain":
                if any(kw in input_lower for kw in ["清仓", "临期", "库存"]):
                    score += 2
            elif template["category"] == "pricing":
                if any(kw in input_lower for kw in ["调价", "涨价", "定价", "竞品"]):
                    score += 2

            # 检查示例相似度
            example_words = set(template["example"])
            input_words = set(user_input)
            overlap = len(example_words & input_words)
            score += overlap * 0.1

            if score > best_score:
                best_score = score
                best_match = template

        return best_match if best_score > 0 else None

    def enrich_input(self, user_input: str) -> dict:
        """丰富化自然语言输入，返回结构化信息"""
        # 提取实体
        entities = self._extract_entities(user_input)

        # 匹配模板
        matched_template = self.match_template(user_input)

        # 填充默认值
        if matched_template and "default_values" in matched_template:
            for key, value in matched_template["default_values"].items():
                if key not in entities:
                    entities[key] = value

        # 解析复杂表达式
        enriched = {
            "original_input": user_input,
            "entities": entities,
            "matched_template": matched_template,
            "normalized_input": self._normalize_input(user_input, entities),
            "complexity_level": self._assess_complexity(user_input, entities),
        }

        return enriched

    def _normalize_input(self, user_input: str, entities: dict) -> str:
        """将自然语言输入标准化"""
        normalized = user_input

        # 替换相对日期为具体日期
        if "date" in entities and isinstance(entities["date"], dict):
            if "original" in entities["date"] and "formatted" in entities["date"]:
                normalized = normalized.replace(
                    entities["date"]["original"],
                    entities["date"]["formatted"]
                )

        # 标准化竞品比价表述
        if "competitor_reference" in entities:
            comp_ref = entities["competitor_reference"]
            if comp_ref["type"] == "lower":
                normalized = normalized + f" (实际策略: 比{comp_ref['reference']}低{comp_ref['amount']}元)"
            else:
                normalized = normalized + f" (实际策略: 比{comp_ref['reference']}高{comp_ref['amount']}元)"

        return normalized

    def _assess_complexity(self, user_input: str, entities: dict) -> str:
        """评估输入的复杂度"""
        complexity_score = 0

        # 多个实体增加复杂度
        complexity_score += len(entities) * 0.5

        # 竞品比价增加复杂度
        if "competitor_reference" in entities:
            complexity_score += 1

        # 多区域增加复杂度
        if "region" in entities and "全国" in str(entities.get("region", "")):
            complexity_score += 0.5

        # 系列产品增加复杂度
        if "product_series" in entities:
            complexity_score += 1

        if complexity_score < 1:
            return "simple"
        elif complexity_score < 3:
            return "medium"
        else:
            return "complex"

    def preview(self, user_input: str) -> dict:
        """预览执行，返回影响估算但不实际执行"""
        # 分析意图
        intent_analysis = self._analyze_intent(user_input)

        # 获取执行计划
        execution_plan = self._create_execution_plan(intent_analysis)

        # 估算影响
        impact = self._estimate_impact(intent_analysis, execution_plan)

        # 构建执行步骤预览
        execution_steps = self._build_execution_steps_preview(execution_plan)

        return {
            "intent": intent_analysis.intent_type,
            "confidence": intent_analysis.confidence,
            "entities": intent_analysis.entities,
            "estimated_impact": impact,
            "execution_steps": execution_steps,
            "required_agents": intent_analysis.required_agents,
            "suggested_workflows": intent_analysis.suggested_workflows,
        }

    def _estimate_impact(self, intent: IntentAnalysis, plan: ExecutionPlan) -> dict:
        """估算执行影响"""
        entities = intent.entities

        # 计算影响门店数
        region = entities.get("region", "全国")
        affected_stores = self.REGION_STORE_COUNT.get(region, 2847)

        # 如果用户指定了门店数，使用用户指定的
        if "store_count" in entities:
            affected_stores = entities["store_count"]

        # 计算涉及SKU数
        affected_skus = entities.get("sku_count", 1)
        if entities.get("product_series"):
            # 系列产品一般有5-8个SKU
            affected_skus = max(affected_skus, 5)

        # 计算涉及系统
        affected_systems = set()
        for task in plan.agent_tasks:
            agent = self.sub_agent_manager.get_agent(task["agent_id"])
            if agent:
                # 根据agent类型推断涉及的系统
                if "product" in task["agent_id"]:
                    affected_systems.update(["POS", "APP", "MENU_BOARD", "INVENTORY"])
                elif "pricing" in task["agent_id"]:
                    affected_systems.update(["POS", "APP", "PRICING"])
                elif "marketing" in task["agent_id"]:
                    affected_systems.update(["POS", "APP", "MARKETING", "CRM"])
                elif "analytics" in task["agent_id"]:
                    affected_systems.update(["ANALYTICS"])
                elif "supply" in task["agent_id"]:
                    affected_systems.update(["INVENTORY"])

        # 估算执行时间
        base_time_minutes = len(plan.agent_tasks) * 30  # 每个Agent约30分钟
        if affected_stores > 2000:
            base_time_minutes *= 1.5
        elif affected_stores > 1000:
            base_time_minutes *= 1.2

        if base_time_minutes < 60:
            estimated_duration = f"约{int(base_time_minutes)}分钟"
        else:
            hours = base_time_minutes / 60
            estimated_duration = f"约{hours:.1f}小时"

        # 判断是否需要审批
        requires_approval = len(plan.approval_points) > 0
        approval_roles = []
        for agent_id in plan.approval_points:
            agent = self.sub_agent_manager.get_agent(agent_id)
            if agent and agent.requires_approval_from:
                approval_roles.extend(agent.requires_approval_from)

        return {
            "affected_stores": affected_stores,
            "affected_skus": affected_skus,
            "affected_systems": list(affected_systems),
            "estimated_duration": estimated_duration,
            "requires_approval": requires_approval,
            "approval_roles": list(set(approval_roles)),
            "region": region,
        }

    def _build_execution_steps_preview(self, plan: ExecutionPlan) -> list[dict]:
        """构建执行步骤预览"""
        steps = []
        step_num = 1

        for task in plan.agent_tasks:
            agent = self.sub_agent_manager.get_agent(task["agent_id"])
            if not agent:
                continue

            # 根据agent类型生成步骤
            if "product" in task["agent_id"]:
                steps.extend([
                    {"step": step_num, "name": "创建SKU", "system": "INVENTORY", "duration": "~30s"},
                    {"step": step_num + 1, "name": "配置POS菜单", "system": "POS", "duration": "~5min"},
                    {"step": step_num + 2, "name": "同步App", "system": "APP", "duration": "~2min"},
                    {"step": step_num + 3, "name": "更新菜单屏", "system": "MENU_BOARD", "duration": "~3min"},
                ])
                step_num += 4
            elif "pricing" in task["agent_id"]:
                steps.extend([
                    {"step": step_num, "name": "计算价格", "system": "PRICING", "duration": "~1min"},
                    {"step": step_num + 1, "name": "更新POS价格", "system": "POS", "duration": "~5min"},
                    {"step": step_num + 2, "name": "同步App价格", "system": "APP", "duration": "~2min"},
                ])
                step_num += 3
            elif "marketing" in task["agent_id"]:
                steps.extend([
                    {"step": step_num, "name": "创建活动", "system": "MARKETING", "duration": "~1min"},
                    {"step": step_num + 1, "name": "配置POS折扣", "system": "POS", "duration": "~3min"},
                    {"step": step_num + 2, "name": "设置会员积分", "system": "CRM", "duration": "~2min"},
                ])
                step_num += 3
            elif "analytics" in task["agent_id"]:
                steps.extend([
                    {"step": step_num, "name": "获取销售数据", "system": "ANALYTICS", "duration": "~2min"},
                    {"step": step_num + 1, "name": "生成报告", "system": "ANALYTICS", "duration": "~5min"},
                ])
                step_num += 2

        # 添加通知步骤
        if steps:
            steps.append({"step": step_num, "name": "发送通知", "system": "NOTIFICATION", "duration": "~1min"})

        return steps
