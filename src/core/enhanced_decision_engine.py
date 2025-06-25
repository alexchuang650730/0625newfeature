"""
Enhanced SmartUI Fusion Decision Engine
深度整合 smartui_mcp 的智能決策引擎

結合三框架的智能決策系統：
- Stagewise 可視化調試決策
- LiveKit 語音交互決策  
- AG-UI 協議統一決策
- smartui_mcp 用戶行為分析決策

作者: SmartUI Fusion Team
版本: 1.0.0
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from datetime import datetime, timedelta
import uuid

from ..protocols.ag_ui_protocol import (
    AGUIMessage, VoiceCommandMessage, VisualDebugMessage,
    UIModificationMessage, StateSyncMessage, UserInteractionMessage
)


class DecisionStrategy(Enum):
    """決策策略枚舉"""
    RULE_BASED = "rule_based"
    ML_BASED = "ml_based"
    HYBRID = "hybrid"
    HEURISTIC = "heuristic"
    SMARTUI_ENHANCED = "smartui_enhanced"


class FrameworkPriority(Enum):
    """框架優先級"""
    STAGEWISE = "stagewise"
    LIVEKIT = "livekit"
    SMARTUI = "smartui"
    BALANCED = "balanced"


@dataclass
class DecisionContext:
    """決策上下文"""
    user_id: str
    session_id: str
    timestamp: datetime
    device_info: Dict[str, Any]
    current_page: Optional[str] = None
    user_history: List[Dict[str, Any]] = None
    voice_context: Optional[Dict[str, Any]] = None
    visual_context: Optional[Dict[str, Any]] = None
    smartui_profile: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.user_history is None:
            self.user_history = []


@dataclass
class DecisionResult:
    """決策結果"""
    decision_id: str
    strategy_used: DecisionStrategy
    confidence: float
    primary_framework: FrameworkPriority
    actions: List[Dict[str, Any]]
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'decision_id': self.decision_id,
            'strategy_used': self.strategy_used.value,
            'confidence': self.confidence,
            'primary_framework': self.primary_framework.value,
            'actions': self.actions,
            'reasoning': self.reasoning,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class UserBehaviorAnalyzer:
    """用戶行為分析器 - 整合 smartui_mcp 的用戶分析能力"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_profiles = {}
        self.interaction_history = {}
        self.behavior_patterns = {}
        
    async def analyze_user_behavior(self, context: DecisionContext) -> Dict[str, Any]:
        """分析用戶行為模式"""
        user_id = context.user_id
        
        # 獲取或創建用戶檔案
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'preferences': {},
                'interaction_patterns': {},
                'device_preferences': {},
                'accessibility_needs': {},
                'efficiency_metrics': {}
            }
        
        profile = self.user_profiles[user_id]
        
        # 分析交互模式
        interaction_analysis = await self._analyze_interaction_patterns(context)
        profile['interaction_patterns'].update(interaction_analysis)
        
        # 分析設備偏好
        device_analysis = await self._analyze_device_preferences(context)
        profile['device_preferences'].update(device_analysis)
        
        # 分析效率指標
        efficiency_analysis = await self._analyze_efficiency_metrics(context)
        profile['efficiency_metrics'].update(efficiency_analysis)
        
        return profile
    
    async def _analyze_interaction_patterns(self, context: DecisionContext) -> Dict[str, Any]:
        """分析交互模式"""
        patterns = {
            'preferred_input_method': 'mixed',  # voice, visual, touch, mixed
            'interaction_frequency': 0,
            'session_duration': 0,
            'error_rate': 0,
            'feature_usage': {}
        }
        
        # 分析歷史交互數據
        if context.user_history:
            voice_interactions = sum(1 for h in context.user_history if h.get('type') == 'voice')
            visual_interactions = sum(1 for h in context.user_history if h.get('type') == 'visual')
            total_interactions = len(context.user_history)
            
            if total_interactions > 0:
                voice_ratio = voice_interactions / total_interactions
                visual_ratio = visual_interactions / total_interactions
                
                if voice_ratio > 0.7:
                    patterns['preferred_input_method'] = 'voice'
                elif visual_ratio > 0.7:
                    patterns['preferred_input_method'] = 'visual'
                else:
                    patterns['preferred_input_method'] = 'mixed'
        
        return patterns
    
    async def _analyze_device_preferences(self, context: DecisionContext) -> Dict[str, Any]:
        """分析設備偏好"""
        device_info = context.device_info
        
        preferences = {
            'screen_size_preference': 'medium',
            'input_method_preference': 'mixed',
            'performance_priority': 'balanced',
            'accessibility_features': []
        }
        
        # 根據設備信息調整偏好
        if device_info.get('screen_width', 1024) < 768:
            preferences['screen_size_preference'] = 'small'
            preferences['performance_priority'] = 'performance'
        elif device_info.get('screen_width', 1024) > 1920:
            preferences['screen_size_preference'] = 'large'
            preferences['performance_priority'] = 'features'
        
        return preferences
    
    async def _analyze_efficiency_metrics(self, context: DecisionContext) -> Dict[str, Any]:
        """分析效率指標"""
        metrics = {
            'task_completion_rate': 0.85,
            'average_task_time': 120,  # seconds
            'error_recovery_time': 30,
            'feature_discovery_rate': 0.6
        }
        
        # 基於歷史數據計算實際指標
        if context.user_history:
            completed_tasks = sum(1 for h in context.user_history if h.get('completed', False))
            total_tasks = len([h for h in context.user_history if h.get('type') == 'task'])
            
            if total_tasks > 0:
                metrics['task_completion_rate'] = completed_tasks / total_tasks
        
        return metrics


class EnhancedDecisionEngine:
    """增強決策引擎 - 深度整合三框架和 smartui_mcp"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategy = DecisionStrategy(config.get('strategy', 'hybrid'))
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.learning_enabled = config.get('learning_enabled', True)
        
        # 初始化子組件
        self.user_analyzer = UserBehaviorAnalyzer(config.get('user_analyzer', {}))
        self.decision_history = []
        self.framework_weights = {
            FrameworkPriority.STAGEWISE: 0.3,
            FrameworkPriority.LIVEKIT: 0.3,
            FrameworkPriority.SMARTUI: 0.4
        }
        
        # 規則引擎配置
        self.rules = config.get('rules', {})
        
        # ML 模型配置（模擬）
        self.ml_config = config.get('ml_config', {})
        
        self.logger = logging.getLogger(__name__)
    
    async def process_voice_command(self, message: VoiceCommandMessage) -> Optional[UIModificationMessage]:
        """處理語音指令"""
        context = DecisionContext(
            user_id=message.user_id,
            session_id=message.session_id,
            timestamp=datetime.now(),
            device_info=message.payload.get('device_info', {}),
            voice_context={
                'transcript': message.payload.get('transcript', ''),
                'intent': message.payload.get('intent', {}),
                'confidence': message.payload.get('confidence', 0)
            }
        )
        
        # 進行決策
        decision = await self.make_decision(context, {
            'input_type': 'voice',
            'command': message.payload.get('transcript', ''),
            'intent': message.payload.get('intent', {}),
            'confidence': message.payload.get('confidence', 0)
        })
        
        if decision.confidence >= self.confidence_threshold:
            # 生成 UI 修改指令
            ui_modification = UIModificationMessage(
                source='decision_engine',
                session_id=message.session_id,
                user_id=message.user_id,
                target_element=decision.actions[0].get('target_element', ''),
                modification_type=decision.actions[0].get('modification_type', 'style'),
                modification_data=decision.actions[0].get('modification_data', {}),
                reason=decision.reasoning
            )
            
            return ui_modification
        
        return None
    
    async def process_visual_debug(self, message: VisualDebugMessage) -> Optional[UIModificationMessage]:
        """處理可視化調試消息"""
        context = DecisionContext(
            user_id=message.user_id,
            session_id=message.session_id,
            timestamp=datetime.now(),
            device_info=message.payload.get('device_info', {}),
            visual_context={
                'selected_element': message.payload.get('selected_element', {}),
                'debug_action': message.payload.get('debug_action', ''),
                'page_context': message.payload.get('page_context', {})
            }
        )
        
        # 進行決策
        decision = await self.make_decision(context, {
            'input_type': 'visual_debug',
            'selected_element': message.payload.get('selected_element', {}),
            'debug_action': message.payload.get('debug_action', ''),
            'page_context': message.payload.get('page_context', {})
        })
        
        if decision.confidence >= self.confidence_threshold:
            # 生成 UI 修改指令
            ui_modification = UIModificationMessage(
                source='decision_engine',
                session_id=message.session_id,
                user_id=message.user_id,
                target_element=decision.actions[0].get('target_element', ''),
                modification_type=decision.actions[0].get('modification_type', 'debug'),
                modification_data=decision.actions[0].get('modification_data', {}),
                reason=decision.reasoning
            )
            
            return ui_modification
        
        return None
    
    async def make_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """核心決策方法"""
        decision_id = str(uuid.uuid4())
        
        # 分析用戶行為
        user_profile = await self.user_analyzer.analyze_user_behavior(context)
        context.smartui_profile = user_profile
        
        # 根據策略進行決策
        if self.strategy == DecisionStrategy.RULE_BASED:
            result = await self._rule_based_decision(context, input_data)
        elif self.strategy == DecisionStrategy.ML_BASED:
            result = await self._ml_based_decision(context, input_data)
        elif self.strategy == DecisionStrategy.HYBRID:
            result = await self._hybrid_decision(context, input_data)
        elif self.strategy == DecisionStrategy.SMARTUI_ENHANCED:
            result = await self._smartui_enhanced_decision(context, input_data)
        else:
            result = await self._heuristic_decision(context, input_data)
        
        # 設置決策ID和時間戳
        result.decision_id = decision_id
        result.timestamp = datetime.now()
        
        # 記錄決策歷史
        self.decision_history.append(result)
        
        # 學習和優化
        if self.learning_enabled:
            await self._learn_from_decision(result, context)
        
        return result
    
    async def _rule_based_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """基於規則的決策"""
        actions = []
        confidence = 0.6
        reasoning = "基於預定義規則的決策"
        primary_framework = FrameworkPriority.BALANCED
        
        input_type = input_data.get('input_type', 'unknown')
        
        if input_type == 'voice':
            # 語音指令規則
            transcript = input_data.get('command', '').lower()
            intent = input_data.get('intent', {})
            
            if any(keyword in transcript for keyword in ['修改', '改變', 'change', 'modify']):
                if any(keyword in transcript for keyword in ['顏色', 'color']):
                    actions.append({
                        'type': 'modify_style',
                        'target_element': intent.get('target', 'button'),
                        'modification_type': 'style',
                        'modification_data': {'color': intent.get('value', 'blue')}
                    })
                    confidence = 0.8
                    primary_framework = FrameworkPriority.LIVEKIT
                    reasoning = "語音指令匹配顏色修改規則"
            
            elif any(keyword in transcript for keyword in ['選擇', '點擊', 'select', 'click']):
                actions.append({
                    'type': 'select_element',
                    'target_element': intent.get('target', 'button'),
                    'modification_type': 'interaction',
                    'modification_data': {'action': 'click'}
                })
                confidence = 0.75
                primary_framework = FrameworkPriority.LIVEKIT
                reasoning = "語音指令匹配選擇操作規則"
        
        elif input_type == 'visual_debug':
            # 可視化調試規則
            debug_action = input_data.get('debug_action', '')
            selected_element = input_data.get('selected_element', {})
            
            if debug_action == 'inspect':
                actions.append({
                    'type': 'show_inspector',
                    'target_element': selected_element.get('id', ''),
                    'modification_type': 'debug',
                    'modification_data': {'show_properties': True, 'highlight': True}
                })
                confidence = 0.9
                primary_framework = FrameworkPriority.STAGEWISE
                reasoning = "可視化調試檢查元素規則"
            
            elif debug_action == 'modify':
                actions.append({
                    'type': 'enable_edit_mode',
                    'target_element': selected_element.get('id', ''),
                    'modification_type': 'debug',
                    'modification_data': {'edit_mode': True}
                })
                confidence = 0.85
                primary_framework = FrameworkPriority.STAGEWISE
                reasoning = "可視化調試修改元素規則"
        
        return DecisionResult(
            decision_id="",  # 將在上層設置
            strategy_used=DecisionStrategy.RULE_BASED,
            confidence=confidence,
            primary_framework=primary_framework,
            actions=actions,
            reasoning=reasoning,
            metadata={'rule_matches': len(actions)},
            timestamp=datetime.now()
        )
    
    async def _ml_based_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """基於機器學習的決策（模擬實現）"""
        # 模擬 ML 模型預測
        features = self._extract_features(context, input_data)
        
        # 簡化的 ML 決策邏輯
        confidence = 0.7 + np.random.random() * 0.2  # 模擬置信度
        
        actions = []
        primary_framework = FrameworkPriority.SMARTUI
        
        # 基於特徵進行預測
        if features.get('voice_confidence', 0) > 0.8:
            primary_framework = FrameworkPriority.LIVEKIT
            actions.append({
                'type': 'voice_response',
                'target_element': 'voice_interface',
                'modification_type': 'interaction',
                'modification_data': {'response': 'voice_command_processed'}
            })
        
        elif features.get('visual_complexity', 0) > 0.7:
            primary_framework = FrameworkPriority.STAGEWISE
            actions.append({
                'type': 'simplify_interface',
                'target_element': 'main_container',
                'modification_type': 'layout',
                'modification_data': {'complexity_reduction': True}
            })
        
        else:
            actions.append({
                'type': 'adaptive_ui',
                'target_element': 'adaptive_container',
                'modification_type': 'smart_adaptation',
                'modification_data': {'user_profile': context.smartui_profile}
            })
        
        return DecisionResult(
            decision_id="",
            strategy_used=DecisionStrategy.ML_BASED,
            confidence=confidence,
            primary_framework=primary_framework,
            actions=actions,
            reasoning="基於機器學習模型的預測決策",
            metadata={'features': features, 'model_version': '1.0'},
            timestamp=datetime.now()
        )
    
    async def _hybrid_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """混合決策策略"""
        # 獲取規則決策和ML決策
        rule_decision = await self._rule_based_decision(context, input_data)
        ml_decision = await self._ml_based_decision(context, input_data)
        
        # 結合兩種決策
        combined_confidence = (rule_decision.confidence * 0.6 + ml_decision.confidence * 0.4)
        
        # 選擇更高置信度的決策
        if rule_decision.confidence > ml_decision.confidence:
            primary_decision = rule_decision
            secondary_decision = ml_decision
        else:
            primary_decision = ml_decision
            secondary_decision = rule_decision
        
        # 合併動作
        combined_actions = primary_decision.actions + [
            action for action in secondary_decision.actions 
            if action not in primary_decision.actions
        ]
        
        return DecisionResult(
            decision_id="",
            strategy_used=DecisionStrategy.HYBRID,
            confidence=combined_confidence,
            primary_framework=primary_decision.primary_framework,
            actions=combined_actions,
            reasoning=f"混合決策：{primary_decision.reasoning} + {secondary_decision.reasoning}",
            metadata={
                'rule_confidence': rule_decision.confidence,
                'ml_confidence': ml_decision.confidence,
                'combination_weight': 0.6
            },
            timestamp=datetime.now()
        )
    
    async def _smartui_enhanced_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """SmartUI 增強決策策略"""
        user_profile = context.smartui_profile or {}
        
        # 基於用戶檔案進行個性化決策
        preferred_input = user_profile.get('interaction_patterns', {}).get('preferred_input_method', 'mixed')
        efficiency_metrics = user_profile.get('efficiency_metrics', {})
        device_preferences = user_profile.get('device_preferences', {})
        
        actions = []
        confidence = 0.8
        primary_framework = FrameworkPriority.SMARTUI
        
        # 根據用戶偏好調整界面
        if preferred_input == 'voice':
            primary_framework = FrameworkPriority.LIVEKIT
            actions.append({
                'type': 'enhance_voice_ui',
                'target_element': 'voice_interface',
                'modification_type': 'enhancement',
                'modification_data': {
                    'voice_priority': True,
                    'visual_hints': True,
                    'speech_feedback': True
                }
            })
            confidence = 0.9
        
        elif preferred_input == 'visual':
            primary_framework = FrameworkPriority.STAGEWISE
            actions.append({
                'type': 'enhance_visual_ui',
                'target_element': 'visual_interface',
                'modification_type': 'enhancement',
                'modification_data': {
                    'visual_priority': True,
                    'debug_tools': True,
                    'element_highlighting': True
                }
            })
            confidence = 0.85
        
        else:  # mixed
            actions.append({
                'type': 'balanced_ui',
                'target_element': 'main_interface',
                'modification_type': 'enhancement',
                'modification_data': {
                    'multimodal': True,
                    'adaptive_switching': True,
                    'context_awareness': True
                }
            })
        
        # 基於效率指標調整
        task_completion_rate = efficiency_metrics.get('task_completion_rate', 0.85)
        if task_completion_rate < 0.7:
            actions.append({
                'type': 'simplify_workflow',
                'target_element': 'workflow_container',
                'modification_type': 'optimization',
                'modification_data': {
                    'reduce_steps': True,
                    'add_guidance': True,
                    'error_prevention': True
                }
            })
        
        # 基於設備偏好調整
        screen_size = device_preferences.get('screen_size_preference', 'medium')
        if screen_size == 'small':
            actions.append({
                'type': 'mobile_optimization',
                'target_element': 'responsive_container',
                'modification_type': 'responsive',
                'modification_data': {
                    'mobile_first': True,
                    'touch_friendly': True,
                    'compact_layout': True
                }
            })
        
        return DecisionResult(
            decision_id="",
            strategy_used=DecisionStrategy.SMARTUI_ENHANCED,
            confidence=confidence,
            primary_framework=primary_framework,
            actions=actions,
            reasoning="基於SmartUI用戶檔案的個性化決策",
            metadata={
                'user_profile': user_profile,
                'personalization_level': 'high'
            },
            timestamp=datetime.now()
        )
    
    async def _heuristic_decision(self, context: DecisionContext, input_data: Dict[str, Any]) -> DecisionResult:
        """啟發式決策"""
        # 簡單的啟發式規則
        actions = []
        confidence = 0.5
        primary_framework = FrameworkPriority.BALANCED
        
        # 基於時間的啟發式
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # 工作時間
            actions.append({
                'type': 'work_mode_ui',
                'target_element': 'main_container',
                'modification_type': 'theme',
                'modification_data': {'theme': 'professional', 'distractions': 'minimal'}
            })
            confidence = 0.7
        
        # 基於設備的啟發式
        device_info = context.device_info
        if device_info.get('is_mobile', False):
            actions.append({
                'type': 'mobile_ui',
                'target_element': 'responsive_container',
                'modification_type': 'responsive',
                'modification_data': {'mobile_optimized': True}
            })
            confidence = 0.8
        
        return DecisionResult(
            decision_id="",
            strategy_used=DecisionStrategy.HEURISTIC,
            confidence=confidence,
            primary_framework=primary_framework,
            actions=actions,
            reasoning="基於啟發式規則的決策",
            metadata={'heuristics_applied': len(actions)},
            timestamp=datetime.now()
        )
    
    def _extract_features(self, context: DecisionContext, input_data: Dict[str, Any]) -> Dict[str, float]:
        """提取ML特徵"""
        features = {}
        
        # 語音相關特徵
        if context.voice_context:
            features['voice_confidence'] = context.voice_context.get('confidence', 0)
            features['voice_length'] = len(context.voice_context.get('transcript', '')) / 100.0
        
        # 視覺相關特徵
        if context.visual_context:
            features['visual_complexity'] = len(context.visual_context.get('selected_element', {})) / 10.0
        
        # 用戶相關特徵
        if context.smartui_profile:
            efficiency = context.smartui_profile.get('efficiency_metrics', {})
            features['user_efficiency'] = efficiency.get('task_completion_rate', 0.5)
            features['user_experience'] = len(context.user_history) / 100.0
        
        # 設備相關特徵
        device_info = context.device_info
        features['screen_size'] = min(device_info.get('screen_width', 1024) / 1920.0, 1.0)
        features['is_mobile'] = 1.0 if device_info.get('is_mobile', False) else 0.0
        
        return features
    
    async def _learn_from_decision(self, decision: DecisionResult, context: DecisionContext):
        """從決策中學習"""
        # 簡化的學習邏輯
        if decision.confidence > 0.8:
            # 高置信度決策，增強相關規則權重
            if decision.primary_framework in self.framework_weights:
                self.framework_weights[decision.primary_framework] *= 1.05
        
        elif decision.confidence < 0.5:
            # 低置信度決策，降低相關規則權重
            if decision.primary_framework in self.framework_weights:
                self.framework_weights[decision.primary_framework] *= 0.95
        
        # 正規化權重
        total_weight = sum(self.framework_weights.values())
        for framework in self.framework_weights:
            self.framework_weights[framework] /= total_weight
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        if not self.decision_history:
            return {
                'total_decisions': 0,
                'average_confidence': 0,
                'framework_distribution': {},
                'strategy_distribution': {}
            }
        
        total_decisions = len(self.decision_history)
        average_confidence = sum(d.confidence for d in self.decision_history) / total_decisions
        
        # 框架分佈
        framework_counts = {}
        for decision in self.decision_history:
            framework = decision.primary_framework.value
            framework_counts[framework] = framework_counts.get(framework, 0) + 1
        
        # 策略分佈
        strategy_counts = {}
        for decision in self.decision_history:
            strategy = decision.strategy_used.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_decisions': total_decisions,
            'average_confidence': average_confidence,
            'framework_distribution': framework_counts,
            'strategy_distribution': strategy_counts,
            'framework_weights': {k.value: v for k, v in self.framework_weights.items()}
        }

