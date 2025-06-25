"""
SmartUI Fusion Core Decision Engine
智慧UI融合核心決策引擎
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import time
from datetime import datetime, timedelta

from ..protocols.ag_ui_protocol import (
    AGUIMessage, MessageType, VoiceCommandMessage, 
    VisualDebugMessage, UIModificationMessage, UserInteractionMessage
)


class InputSource(Enum):
    """輸入源類型"""
    VOICE = "voice"
    VISUAL = "visual"
    USER_INTERACTION = "user_interaction"
    SYSTEM = "system"
    API = "api"


class DecisionStrategy(Enum):
    """決策策略"""
    RULE_BASED = "rule_based"
    ML_BASED = "ml_based"
    HYBRID = "hybrid"
    HEURISTIC = "heuristic"


@dataclass
class DecisionContext:
    """決策上下文"""
    input_source: InputSource
    user_id: str
    session_id: str
    current_ui_state: Dict[str, Any]
    user_profile: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    timestamp: datetime
    device_info: Dict[str, Any]
    environment: Dict[str, Any]


@dataclass
class DecisionResult:
    """決策結果"""
    action_type: str
    target_element: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]]
    execution_plan: List[Dict[str, Any]]


class SmartUIDecisionEngine:
    """SmartUI智慧決策引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategy = DecisionStrategy(config.get('strategy', 'hybrid'))
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.learning_enabled = config.get('learning_enabled', True)
        
        # 初始化各種決策組件
        self.rule_engine = RuleBasedDecisionEngine(config.get('rules', {}))
        self.ml_engine = MLBasedDecisionEngine(config.get('ml_config', {}))
        self.heuristic_engine = HeuristicDecisionEngine(config.get('heuristics', {}))
        
        # 用戶行為分析器
        self.behavior_analyzer = UserBehaviorAnalyzer()
        
        # 決策歷史記錄
        self.decision_history: List[Tuple[DecisionContext, DecisionResult]] = []
        
        # 性能指標
        self.performance_metrics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'average_confidence': 0.0,
            'average_response_time': 0.0
        }
    
    async def process_voice_command(self, voice_message: VoiceCommandMessage) -> Optional[UIModificationMessage]:
        """處理語音指令"""
        start_time = time.time()
        
        # 構建決策上下文
        context = await self._build_decision_context(
            InputSource.VOICE,
            voice_message.user_id,
            voice_message.session_id,
            voice_message.payload
        )
        
        # 分析語音指令
        intent = voice_message.payload.get('intent', {})
        transcript = voice_message.payload.get('transcript', '')
        confidence = voice_message.payload.get('confidence', 0.0)
        
        # 如果置信度太低，請求澄清
        if confidence < self.confidence_threshold:
            return await self._handle_low_confidence_command(voice_message, context)
        
        # 執行決策
        decision = await self._make_decision(context, {
            'action': intent.get('action'),
            'target': intent.get('target'),
            'parameters': intent.get('parameters', {}),
            'transcript': transcript
        })
        
        # 記錄決策
        self._record_decision(context, decision, time.time() - start_time)
        
        # 生成UI修改消息
        if decision.confidence >= self.confidence_threshold:
            return self._create_ui_modification_message(voice_message, decision)
        else:
            return await self._request_clarification(voice_message, decision)
    
    async def process_visual_debug(self, visual_message: VisualDebugMessage) -> Optional[AGUIMessage]:
        """處理可視化調試事件"""
        context = await self._build_decision_context(
            InputSource.VISUAL,
            visual_message.user_id or "developer",
            visual_message.session_id,
            visual_message.payload
        )
        
        element_id = visual_message.payload.get('element_id')
        action = visual_message.payload.get('action')
        properties = visual_message.payload.get('properties', {})
        
        if action == 'select':
            # 元素被選中，提供智能建議
            suggestions = await self._generate_element_suggestions(element_id, properties, context)
            return self._create_suggestions_message(visual_message, suggestions)
            
        elif action == 'modify':
            # 元素被修改，學習用戶偏好
            await self._learn_from_modification(element_id, properties, context)
            return self._create_learning_confirmation_message(visual_message)
            
        elif action == 'inspect':
            # 元素檢查，提供詳細信息
            analysis = await self._analyze_element(element_id, properties, context)
            return self._create_analysis_message(visual_message, analysis)
    
    async def process_user_interaction(self, interaction_message: UserInteractionMessage) -> Optional[AGUIMessage]:
        """處理用戶交互事件"""
        context = await self._build_decision_context(
            InputSource.USER_INTERACTION,
            interaction_message.user_id,
            interaction_message.session_id,
            interaction_message.payload
        )
        
        # 分析用戶行為模式
        await self.behavior_analyzer.analyze_interaction(interaction_message.payload, context)
        
        # 檢查是否需要主動幫助
        if await self._should_offer_help(context):
            help_suggestions = await self._generate_help_suggestions(context)
            return self._create_help_message(interaction_message, help_suggestions)
        
        return None
    
    async def _build_decision_context(self, input_source: InputSource, user_id: str, 
                                    session_id: str, payload: Dict[str, Any]) -> DecisionContext:
        """構建決策上下文"""
        
        # 獲取當前UI狀態
        ui_state = await self._get_current_ui_state(session_id)
        
        # 獲取用戶畫像
        user_profile = await self._get_user_profile(user_id)
        
        # 獲取交互歷史
        interaction_history = await self._get_interaction_history(user_id, session_id)
        
        # 獲取設備信息
        device_info = payload.get('device_info', {})
        
        # 獲取環境信息
        environment = await self._get_environment_info(session_id)
        
        return DecisionContext(
            input_source=input_source,
            user_id=user_id,
            session_id=session_id,
            current_ui_state=ui_state,
            user_profile=user_profile,
            interaction_history=interaction_history,
            timestamp=datetime.now(),
            device_info=device_info,
            environment=environment
        )
    
    async def _make_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """執行決策"""
        
        if self.strategy == DecisionStrategy.RULE_BASED:
            return await self.rule_engine.decide(context, input_data)
        elif self.strategy == DecisionStrategy.ML_BASED:
            return await self.ml_engine.decide(context, input_data)
        elif self.strategy == DecisionStrategy.HEURISTIC:
            return await self.heuristic_engine.decide(context, input_data)
        else:  # HYBRID
            return await self._hybrid_decision(context, input_data)
    
    async def _hybrid_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """混合決策策略"""
        
        # 並行執行多種決策策略
        rule_result = await self.rule_engine.decide(context, input_data)
        ml_result = await self.ml_engine.decide(context, input_data)
        heuristic_result = await self.heuristic_engine.decide(context, input_data)
        
        # 整合決策結果
        return await self._integrate_decisions([rule_result, ml_result, heuristic_result], context)
    
    async def _integrate_decisions(self, decisions: List[DecisionResult], context: DecisionContext) -> DecisionResult:
        """整合多個決策結果"""
        
        # 加權平均置信度
        total_confidence = sum(d.confidence for d in decisions)
        weights = [d.confidence / total_confidence if total_confidence > 0 else 1/len(decisions) for d in decisions]
        
        # 選擇最高置信度的決策作為主要結果
        primary_decision = max(decisions, key=lambda d: d.confidence)
        
        # 合併替代方案
        all_alternatives = []
        for decision in decisions:
            all_alternatives.extend(decision.alternatives)
        
        # 去重並排序
        unique_alternatives = []
        seen = set()
        for alt in all_alternatives:
            alt_key = f"{alt.get('action_type')}_{alt.get('target_element')}"
            if alt_key not in seen:
                unique_alternatives.append(alt)
                seen.add(alt_key)
        
        unique_alternatives.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return DecisionResult(
            action_type=primary_decision.action_type,
            target_element=primary_decision.target_element,
            parameters=primary_decision.parameters,
            confidence=sum(w * d.confidence for w, d in zip(weights, decisions)),
            reasoning=f"Hybrid decision based on {len(decisions)} strategies",
            alternatives=unique_alternatives[:5],  # 保留前5個替代方案
            execution_plan=primary_decision.execution_plan
        )
    
    async def _generate_element_suggestions(self, element_id: str, properties: Dict[str, Any], 
                                          context: DecisionContext) -> List[Dict[str, Any]]:
        """為選中的元素生成智能建議"""
        suggestions = []
        
        # 基於用戶歷史的建議
        historical_suggestions = await self._get_historical_suggestions(element_id, properties, context)
        suggestions.extend(historical_suggestions)
        
        # 基於設計原則的建議
        design_suggestions = await self._get_design_suggestions(properties)
        suggestions.extend(design_suggestions)
        
        # 基於可訪問性的建議
        accessibility_suggestions = await self._get_accessibility_suggestions(properties)
        suggestions.extend(accessibility_suggestions)
        
        # 基於性能的建議
        performance_suggestions = await self._get_performance_suggestions(properties)
        suggestions.extend(performance_suggestions)
        
        # 排序並返回前10個建議
        suggestions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return suggestions[:10]
    
    def _record_decision(self, context: DecisionContext, decision: DecisionResult, response_time: float):
        """記錄決策歷史"""
        self.decision_history.append((context, decision))
        
        # 更新性能指標
        self.performance_metrics['total_decisions'] += 1
        self.performance_metrics['average_response_time'] = (
            (self.performance_metrics['average_response_time'] * (self.performance_metrics['total_decisions'] - 1) + response_time) /
            self.performance_metrics['total_decisions']
        )
        
        # 保持歷史記錄在合理範圍內
        if len(self.decision_history) > 10000:
            self.decision_history = self.decision_history[-5000:]
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            **self.performance_metrics,
            'decision_history_size': len(self.decision_history),
            'last_updated': datetime.now().isoformat()
        }


class RuleBasedDecisionEngine:
    """基於規則的決策引擎"""
    
    def __init__(self, rules_config: Dict[str, Any]):
        self.rules = rules_config
        
    async def decide(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """基於規則進行決策"""
        
        action = input_data.get('action', '')
        target = input_data.get('target', '')
        parameters = input_data.get('parameters', {})
        
        # 簡單的規則匹配邏輯
        if action == 'modify' and target:
            return DecisionResult(
                action_type='ui_modification',
                target_element=target,
                parameters=parameters,
                confidence=0.8,
                reasoning="Rule-based decision for UI modification",
                alternatives=[],
                execution_plan=[{
                    'step': 1,
                    'action': 'modify_element',
                    'target': target,
                    'parameters': parameters
                }]
            )
        
        # 默認決策
        return DecisionResult(
            action_type='unknown',
            target_element='',
            parameters={},
            confidence=0.1,
            reasoning="No matching rule found",
            alternatives=[],
            execution_plan=[]
        )


class MLBasedDecisionEngine:
    """基於機器學習的決策引擎"""
    
    def __init__(self, ml_config: Dict[str, Any]):
        self.config = ml_config
        # 這裡可以初始化ML模型
        
    async def decide(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """基於機器學習進行決策"""
        
        # 這裡實現ML決策邏輯
        # 暫時返回模擬結果
        return DecisionResult(
            action_type='ml_prediction',
            target_element=input_data.get('target', ''),
            parameters=input_data.get('parameters', {}),
            confidence=0.75,
            reasoning="ML-based prediction",
            alternatives=[],
            execution_plan=[]
        )


class HeuristicDecisionEngine:
    """基於啟發式的決策引擎"""
    
    def __init__(self, heuristics_config: Dict[str, Any]):
        self.config = heuristics_config
        
    async def decide(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """基於啟發式進行決策"""
        
        # 實現啟發式決策邏輯
        return DecisionResult(
            action_type='heuristic_decision',
            target_element=input_data.get('target', ''),
            parameters=input_data.get('parameters', {}),
            confidence=0.6,
            reasoning="Heuristic-based decision",
            alternatives=[],
            execution_plan=[]
        )


class UserBehaviorAnalyzer:
    """用戶行為分析器"""
    
    def __init__(self):
        self.behavior_patterns = {}
        
    async def analyze_interaction(self, interaction_data: Dict[str, Any], context: DecisionContext):
        """分析用戶交互行為"""
        
        user_id = context.user_id
        if user_id not in self.behavior_patterns:
            self.behavior_patterns[user_id] = {
                'interaction_count': 0,
                'common_actions': {},
                'preferred_elements': {},
                'efficiency_score': 0.0
            }
        
        pattern = self.behavior_patterns[user_id]
        pattern['interaction_count'] += 1
        
        # 記錄常見動作
        action = interaction_data.get('interaction_type', 'unknown')
        pattern['common_actions'][action] = pattern['common_actions'].get(action, 0) + 1
        
        # 記錄偏好元素
        element_info = interaction_data.get('element_info', {})
        element_type = element_info.get('tagName', 'unknown')
        pattern['preferred_elements'][element_type] = pattern['preferred_elements'].get(element_type, 0) + 1

