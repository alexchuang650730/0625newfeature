"""
SmartUI User Analyzer - 深度整合用戶行為分析
整合原有 smartui_mcp 的用戶分析能力到三框架系統

功能特點：
- 實時用戶行為追蹤和分析
- 多模態交互模式識別
- 個性化用戶檔案建立
- 智能偏好學習和預測
- 可訪問性需求分析

作者: SmartUI Fusion Team
版本: 1.0.0
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from enum import Enum
import uuid


class InteractionType(Enum):
    """交互類型"""
    VOICE = "voice"
    VISUAL = "visual"
    TOUCH = "touch"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    GESTURE = "gesture"


class UserPreferenceCategory(Enum):
    """用戶偏好類別"""
    INPUT_METHOD = "input_method"
    UI_THEME = "ui_theme"
    LAYOUT_DENSITY = "layout_density"
    ANIMATION_SPEED = "animation_speed"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"


@dataclass
class UserInteraction:
    """用戶交互記錄"""
    interaction_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    interaction_type: InteractionType
    element_id: Optional[str]
    element_type: Optional[str]
    action: str
    context: Dict[str, Any]
    success: bool
    duration: float  # 毫秒
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'interaction_id': self.interaction_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'interaction_type': self.interaction_type.value,
            'element_id': self.element_id,
            'element_type': self.element_type,
            'action': self.action,
            'context': self.context,
            'success': self.success,
            'duration': self.duration,
            'error_message': self.error_message
        }


@dataclass
class UserProfile:
    """用戶檔案"""
    user_id: str
    created_at: datetime
    last_updated: datetime
    
    # 基本信息
    device_preferences: Dict[str, Any]
    accessibility_needs: Dict[str, Any]
    
    # 交互偏好
    preferred_input_methods: List[InteractionType]
    interaction_patterns: Dict[str, Any]
    
    # 效率指標
    efficiency_metrics: Dict[str, float]
    
    # 學習數據
    feature_usage: Dict[str, int]
    error_patterns: Dict[str, int]
    
    # 個性化設置
    ui_preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'device_preferences': self.device_preferences,
            'accessibility_needs': self.accessibility_needs,
            'preferred_input_methods': [method.value for method in self.preferred_input_methods],
            'interaction_patterns': self.interaction_patterns,
            'efficiency_metrics': self.efficiency_metrics,
            'feature_usage': self.feature_usage,
            'error_patterns': self.error_patterns,
            'ui_preferences': self.ui_preferences
        }


class SmartUIUserAnalyzer:
    """SmartUI 用戶分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 用戶數據存儲
        self.user_profiles: Dict[str, UserProfile] = {}
        self.interaction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.session_data: Dict[str, Dict[str, Any]] = {}
        
        # 分析配置
        self.analysis_window = timedelta(days=config.get('analysis_window_days', 30))
        self.min_interactions_for_analysis = config.get('min_interactions_for_analysis', 10)
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        
        # 實時分析緩存
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=config.get('cache_ttl_minutes', 15))
        
        # 模式識別
        self.pattern_detectors = {
            'input_preference': self._detect_input_preference,
            'efficiency_pattern': self._detect_efficiency_pattern,
            'error_pattern': self._detect_error_pattern,
            'accessibility_needs': self._detect_accessibility_needs,
            'device_adaptation': self._detect_device_adaptation
        }
    
    async def record_interaction(self, interaction: UserInteraction) -> bool:
        """記錄用戶交互"""
        try:
            # 添加到歷史記錄
            self.interaction_history[interaction.user_id].append(interaction)
            
            # 更新會話數據
            if interaction.session_id not in self.session_data:
                self.session_data[interaction.session_id] = {
                    'start_time': interaction.timestamp,
                    'interactions': [],
                    'user_id': interaction.user_id
                }
            
            self.session_data[interaction.session_id]['interactions'].append(interaction)
            
            # 實時分析更新
            await self._update_real_time_analysis(interaction)
            
            # 清理過期緩存
            await self._cleanup_expired_cache()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record interaction: {e}")
            return False
    
    async def analyze_user_behavior(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析用戶行為"""
        # 檢查緩存
        cache_key = f"{user_id}_{hash(str(context))}"
        if cache_key in self.analysis_cache:
            cache_entry = self.analysis_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                return cache_entry['analysis']
        
        # 獲取或創建用戶檔案
        profile = await self.get_or_create_user_profile(user_id)
        
        # 獲取最近的交互數據
        recent_interactions = self._get_recent_interactions(user_id)
        
        if len(recent_interactions) < self.min_interactions_for_analysis:
            return self._get_default_analysis(profile)
        
        # 執行各種模式分析
        analysis_results = {}
        
        for pattern_name, detector in self.pattern_detectors.items():
            try:
                result = await detector(user_id, recent_interactions, profile, context)
                analysis_results[pattern_name] = result
            except Exception as e:
                self.logger.error(f"Pattern detection failed for {pattern_name}: {e}")
                analysis_results[pattern_name] = {'confidence': 0, 'data': {}}
        
        # 綜合分析結果
        comprehensive_analysis = await self._synthesize_analysis(analysis_results, profile, context)
        
        # 更新緩存
        self.analysis_cache[cache_key] = {
            'timestamp': datetime.now(),
            'analysis': comprehensive_analysis
        }
        
        # 更新用戶檔案
        await self._update_user_profile(profile, comprehensive_analysis)
        
        return comprehensive_analysis
    
    async def get_or_create_user_profile(self, user_id: str) -> UserProfile:
        """獲取或創建用戶檔案"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                device_preferences={},
                accessibility_needs={},
                preferred_input_methods=[],
                interaction_patterns={},
                efficiency_metrics={},
                feature_usage={},
                error_patterns={},
                ui_preferences={}
            )
        
        return self.user_profiles[user_id]
    
    def _get_recent_interactions(self, user_id: str, limit: Optional[int] = None) -> List[UserInteraction]:
        """獲取最近的交互記錄"""
        if user_id not in self.interaction_history:
            return []
        
        cutoff_time = datetime.now() - self.analysis_window
        recent_interactions = [
            interaction for interaction in self.interaction_history[user_id]
            if interaction.timestamp >= cutoff_time
        ]
        
        if limit:
            recent_interactions = recent_interactions[-limit:]
        
        return recent_interactions
    
    async def _detect_input_preference(self, user_id: str, interactions: List[UserInteraction], 
                                     profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """檢測輸入偏好模式"""
        if not interactions:
            return {'confidence': 0, 'data': {}}
        
        # 統計各種輸入方式的使用頻率
        input_counts = defaultdict(int)
        success_rates = defaultdict(list)
        
        for interaction in interactions:
            input_type = interaction.interaction_type
            input_counts[input_type] += 1
            success_rates[input_type].append(1 if interaction.success else 0)
        
        # 計算偏好分數
        total_interactions = len(interactions)
        preference_scores = {}
        
        for input_type, count in input_counts.items():
            frequency_score = count / total_interactions
            success_rate = np.mean(success_rates[input_type]) if success_rates[input_type] else 0
            
            # 綜合分數：頻率 * 成功率
            preference_scores[input_type.value] = frequency_score * success_rate
        
        # 確定主要偏好
        if preference_scores:
            primary_preference = max(preference_scores.keys(), key=lambda k: preference_scores[k])
            confidence = preference_scores[primary_preference]
        else:
            primary_preference = 'mixed'
            confidence = 0.5
        
        return {
            'confidence': confidence,
            'data': {
                'primary_preference': primary_preference,
                'preference_scores': preference_scores,
                'input_distribution': {k.value: v for k, v in input_counts.items()},
                'success_rates': {k.value: np.mean(v) for k, v in success_rates.items()}
            }
        }
    
    async def _detect_efficiency_pattern(self, user_id: str, interactions: List[UserInteraction],
                                       profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """檢測效率模式"""
        if not interactions:
            return {'confidence': 0, 'data': {}}
        
        # 計算效率指標
        total_interactions = len(interactions)
        successful_interactions = sum(1 for i in interactions if i.success)
        success_rate = successful_interactions / total_interactions if total_interactions > 0 else 0
        
        # 計算平均任務時間
        task_durations = [i.duration for i in interactions if i.success]
        avg_task_duration = np.mean(task_durations) if task_durations else 0
        
        # 計算錯誤恢復時間
        error_interactions = [i for i in interactions if not i.success]
        error_recovery_times = []
        
        for i, error_interaction in enumerate(error_interactions):
            # 查找錯誤後的下一個成功交互
            error_time = error_interaction.timestamp
            for j in range(len(interactions)):
                if (interactions[j].timestamp > error_time and 
                    interactions[j].success and 
                    interactions[j].element_id == error_interaction.element_id):
                    recovery_time = (interactions[j].timestamp - error_time).total_seconds() * 1000
                    error_recovery_times.append(recovery_time)
                    break
        
        avg_error_recovery_time = np.mean(error_recovery_times) if error_recovery_times else 0
        
        # 計算學習曲線
        learning_trend = self._calculate_learning_trend(interactions)
        
        # 效率等級評估
        efficiency_level = self._assess_efficiency_level(success_rate, avg_task_duration, learning_trend)
        
        confidence = 0.8 if total_interactions >= 20 else 0.5
        
        return {
            'confidence': confidence,
            'data': {
                'success_rate': success_rate,
                'avg_task_duration': avg_task_duration,
                'avg_error_recovery_time': avg_error_recovery_time,
                'learning_trend': learning_trend,
                'efficiency_level': efficiency_level,
                'total_interactions': total_interactions,
                'error_rate': 1 - success_rate
            }
        }
    
    async def _detect_error_pattern(self, user_id: str, interactions: List[UserInteraction],
                                  profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """檢測錯誤模式"""
        error_interactions = [i for i in interactions if not i.success]
        
        if not error_interactions:
            return {'confidence': 0.8, 'data': {'error_free': True}}
        
        # 錯誤類型分析
        error_types = defaultdict(int)
        error_elements = defaultdict(int)
        error_times = []
        
        for error in error_interactions:
            if error.error_message:
                error_types[error.error_message] += 1
            if error.element_type:
                error_elements[error.element_type] += 1
            error_times.append(error.timestamp.hour)
        
        # 時間模式分析
        error_time_distribution = defaultdict(int)
        for hour in error_times:
            if 6 <= hour < 12:
                error_time_distribution['morning'] += 1
            elif 12 <= hour < 18:
                error_time_distribution['afternoon'] += 1
            elif 18 <= hour < 24:
                error_time_distribution['evening'] += 1
            else:
                error_time_distribution['night'] += 1
        
        # 錯誤趨勢分析
        error_trend = self._calculate_error_trend(error_interactions)
        
        confidence = 0.7 if len(error_interactions) >= 5 else 0.4
        
        return {
            'confidence': confidence,
            'data': {
                'total_errors': len(error_interactions),
                'error_rate': len(error_interactions) / len(interactions),
                'common_error_types': dict(error_types),
                'problematic_elements': dict(error_elements),
                'error_time_distribution': dict(error_time_distribution),
                'error_trend': error_trend,
                'needs_assistance': len(error_interactions) / len(interactions) > 0.3
            }
        }
    
    async def _detect_accessibility_needs(self, user_id: str, interactions: List[UserInteraction],
                                        profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """檢測可訪問性需求"""
        accessibility_indicators = {
            'high_contrast_usage': 0,
            'large_text_preference': 0,
            'keyboard_navigation': 0,
            'voice_preference': 0,
            'slow_interaction_speed': 0,
            'repetitive_actions': 0
        }
        
        # 分析交互模式以識別可訪問性需求
        keyboard_interactions = sum(1 for i in interactions if i.interaction_type == InteractionType.KEYBOARD)
        voice_interactions = sum(1 for i in interactions if i.interaction_type == InteractionType.VOICE)
        
        total_interactions = len(interactions)
        if total_interactions > 0:
            keyboard_ratio = keyboard_interactions / total_interactions
            voice_ratio = voice_interactions / total_interactions
            
            if keyboard_ratio > 0.7:
                accessibility_indicators['keyboard_navigation'] = 1
            if voice_ratio > 0.5:
                accessibility_indicators['voice_preference'] = 1
        
        # 分析交互速度
        interaction_speeds = [i.duration for i in interactions if i.duration > 0]
        if interaction_speeds:
            avg_speed = np.mean(interaction_speeds)
            if avg_speed > 3000:  # 超過3秒認為是慢速交互
                accessibility_indicators['slow_interaction_speed'] = 1
        
        # 檢測重複動作（可能表示困難）
        action_counts = defaultdict(int)
        for interaction in interactions:
            action_key = f"{interaction.element_id}_{interaction.action}"
            action_counts[action_key] += 1
        
        repetitive_actions = sum(1 for count in action_counts.values() if count > 5)
        if repetitive_actions > 0:
            accessibility_indicators['repetitive_actions'] = 1
        
        # 計算可訪問性需求分數
        accessibility_score = sum(accessibility_indicators.values()) / len(accessibility_indicators)
        
        # 生成建議
        recommendations = []
        if accessibility_indicators['keyboard_navigation']:
            recommendations.append('enhanced_keyboard_navigation')
        if accessibility_indicators['voice_preference']:
            recommendations.append('voice_interface_optimization')
        if accessibility_indicators['slow_interaction_speed']:
            recommendations.append('extended_timeout_settings')
        if accessibility_indicators['repetitive_actions']:
            recommendations.append('simplified_workflows')
        
        confidence = 0.6 if total_interactions >= 15 else 0.3
        
        return {
            'confidence': confidence,
            'data': {
                'accessibility_score': accessibility_score,
                'indicators': accessibility_indicators,
                'recommendations': recommendations,
                'needs_accessibility_features': accessibility_score > 0.3
            }
        }
    
    async def _detect_device_adaptation(self, user_id: str, interactions: List[UserInteraction],
                                      profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """檢測設備適應模式"""
        device_contexts = [i.context.get('device_info', {}) for i in interactions if 'device_info' in i.context]
        
        if not device_contexts:
            return {'confidence': 0, 'data': {}}
        
        # 分析設備使用模式
        device_types = defaultdict(int)
        screen_sizes = []
        input_methods = defaultdict(int)
        
        for device_info in device_contexts:
            device_type = device_info.get('type', 'unknown')
            device_types[device_type] += 1
            
            if 'screen_width' in device_info:
                screen_sizes.append(device_info['screen_width'])
            
            if 'primary_input' in device_info:
                input_methods[device_info['primary_input']] += 1
        
        # 設備偏好分析
        primary_device = max(device_types.keys(), key=lambda k: device_types[k]) if device_types else 'unknown'
        
        # 屏幕尺寸偏好
        if screen_sizes:
            avg_screen_size = np.mean(screen_sizes)
            if avg_screen_size < 768:
                screen_preference = 'small'
            elif avg_screen_size > 1920:
                screen_preference = 'large'
            else:
                screen_preference = 'medium'
        else:
            screen_preference = 'unknown'
        
        # 輸入方法偏好
        primary_input = max(input_methods.keys(), key=lambda k: input_methods[k]) if input_methods else 'unknown'
        
        confidence = 0.7 if len(device_contexts) >= 10 else 0.4
        
        return {
            'confidence': confidence,
            'data': {
                'primary_device': primary_device,
                'device_distribution': dict(device_types),
                'screen_preference': screen_preference,
                'primary_input_method': primary_input,
                'input_method_distribution': dict(input_methods),
                'multi_device_user': len(device_types) > 1
            }
        }
    
    def _calculate_learning_trend(self, interactions: List[UserInteraction]) -> float:
        """計算學習趨勢"""
        if len(interactions) < 10:
            return 0.0
        
        # 將交互分為前半部分和後半部分
        mid_point = len(interactions) // 2
        early_interactions = interactions[:mid_point]
        recent_interactions = interactions[mid_point:]
        
        # 計算成功率變化
        early_success_rate = sum(1 for i in early_interactions if i.success) / len(early_interactions)
        recent_success_rate = sum(1 for i in recent_interactions if i.success) / len(recent_interactions)
        
        # 計算平均任務時間變化
        early_durations = [i.duration for i in early_interactions if i.success]
        recent_durations = [i.duration for i in recent_interactions if i.success]
        
        early_avg_duration = np.mean(early_durations) if early_durations else 0
        recent_avg_duration = np.mean(recent_durations) if recent_durations else 0
        
        # 學習趨勢 = 成功率提升 + 速度提升
        success_improvement = recent_success_rate - early_success_rate
        speed_improvement = (early_avg_duration - recent_avg_duration) / early_avg_duration if early_avg_duration > 0 else 0
        
        learning_trend = (success_improvement + speed_improvement) / 2
        return max(-1.0, min(1.0, learning_trend))  # 限制在 -1 到 1 之間
    
    def _calculate_error_trend(self, error_interactions: List[UserInteraction]) -> str:
        """計算錯誤趨勢"""
        if len(error_interactions) < 5:
            return 'insufficient_data'
        
        # 按時間排序
        sorted_errors = sorted(error_interactions, key=lambda x: x.timestamp)
        
        # 分析最近的錯誤頻率
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_errors = [e for e in sorted_errors if e.timestamp >= recent_cutoff]
        
        if len(recent_errors) == 0:
            return 'improving'
        elif len(recent_errors) > len(sorted_errors) * 0.5:
            return 'worsening'
        else:
            return 'stable'
    
    def _assess_efficiency_level(self, success_rate: float, avg_duration: float, learning_trend: float) -> str:
        """評估效率等級"""
        # 綜合評分
        efficiency_score = (success_rate * 0.4 + 
                          (1 - min(avg_duration / 5000, 1)) * 0.3 + 
                          (learning_trend + 1) / 2 * 0.3)
        
        if efficiency_score >= 0.8:
            return 'expert'
        elif efficiency_score >= 0.6:
            return 'proficient'
        elif efficiency_score >= 0.4:
            return 'intermediate'
        else:
            return 'beginner'
    
    async def _synthesize_analysis(self, analysis_results: Dict[str, Dict[str, Any]], 
                                 profile: UserProfile, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """綜合分析結果"""
        synthesis = {
            'user_id': profile.user_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_confidence': 0,
            'user_type': 'unknown',
            'recommendations': [],
            'insights': {}
        }
        
        # 計算總體置信度
        confidences = [result['confidence'] for result in analysis_results.values()]
        synthesis['overall_confidence'] = np.mean(confidences) if confidences else 0
        
        # 提取關鍵洞察
        for pattern_name, result in analysis_results.items():
            if result['confidence'] >= self.confidence_threshold:
                synthesis['insights'][pattern_name] = result['data']
        
        # 用戶類型分類
        synthesis['user_type'] = self._classify_user_type(analysis_results)
        
        # 生成個性化建議
        synthesis['recommendations'] = await self._generate_recommendations(analysis_results, profile)
        
        return synthesis
    
    def _classify_user_type(self, analysis_results: Dict[str, Dict[str, Any]]) -> str:
        """分類用戶類型"""
        # 基於分析結果分類用戶
        efficiency_data = analysis_results.get('efficiency_pattern', {}).get('data', {})
        input_data = analysis_results.get('input_preference', {}).get('data', {})
        accessibility_data = analysis_results.get('accessibility_needs', {}).get('data', {})
        
        efficiency_level = efficiency_data.get('efficiency_level', 'intermediate')
        primary_input = input_data.get('primary_preference', 'mixed')
        needs_accessibility = accessibility_data.get('needs_accessibility_features', False)
        
        # 分類邏輯
        if needs_accessibility:
            return 'accessibility_user'
        elif efficiency_level == 'expert':
            return 'power_user'
        elif efficiency_level == 'beginner':
            return 'novice_user'
        elif primary_input == 'voice':
            return 'voice_first_user'
        elif primary_input == 'visual':
            return 'visual_user'
        else:
            return 'balanced_user'
    
    async def _generate_recommendations(self, analysis_results: Dict[str, Dict[str, Any]], 
                                      profile: UserProfile) -> List[str]:
        """生成個性化建議"""
        recommendations = []
        
        # 基於效率分析的建議
        efficiency_data = analysis_results.get('efficiency_pattern', {}).get('data', {})
        if efficiency_data.get('error_rate', 0) > 0.2:
            recommendations.append('error_prevention_enhancement')
        if efficiency_data.get('avg_task_duration', 0) > 3000:
            recommendations.append('workflow_simplification')
        
        # 基於輸入偏好的建議
        input_data = analysis_results.get('input_preference', {}).get('data', {})
        primary_input = input_data.get('primary_preference', 'mixed')
        if primary_input == 'voice':
            recommendations.append('voice_interface_optimization')
        elif primary_input == 'visual':
            recommendations.append('visual_debugging_enhancement')
        
        # 基於可訪問性需求的建議
        accessibility_data = analysis_results.get('accessibility_needs', {}).get('data', {})
        if accessibility_data.get('needs_accessibility_features', False):
            recommendations.extend(accessibility_data.get('recommendations', []))
        
        # 基於設備適應的建議
        device_data = analysis_results.get('device_adaptation', {}).get('data', {})
        if device_data.get('multi_device_user', False):
            recommendations.append('cross_device_synchronization')
        if device_data.get('screen_preference') == 'small':
            recommendations.append('mobile_optimization')
        
        return list(set(recommendations))  # 去重
    
    def _get_default_analysis(self, profile: UserProfile) -> Dict[str, Any]:
        """獲取默認分析結果"""
        return {
            'user_id': profile.user_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_confidence': 0.3,
            'user_type': 'new_user',
            'recommendations': ['onboarding_assistance', 'usage_tracking'],
            'insights': {
                'insufficient_data': True,
                'needs_more_interactions': True
            }
        }
    
    async def _update_real_time_analysis(self, interaction: UserInteraction):
        """實時分析更新"""
        # 簡化的實時更新邏輯
        user_id = interaction.user_id
        
        # 更新實時統計
        if user_id not in self.analysis_cache:
            self.analysis_cache[user_id] = {
                'timestamp': datetime.now(),
                'real_time_stats': {
                    'recent_success_rate': 1.0 if interaction.success else 0.0,
                    'recent_interaction_count': 1,
                    'last_interaction_type': interaction.interaction_type.value
                }
            }
        else:
            stats = self.analysis_cache[user_id]['real_time_stats']
            stats['recent_interaction_count'] += 1
            
            # 更新成功率（滑動平均）
            current_success = 1.0 if interaction.success else 0.0
            alpha = 0.1  # 學習率
            stats['recent_success_rate'] = (1 - alpha) * stats['recent_success_rate'] + alpha * current_success
            stats['last_interaction_type'] = interaction.interaction_type.value
    
    async def _update_user_profile(self, profile: UserProfile, analysis: Dict[str, Any]):
        """更新用戶檔案"""
        profile.last_updated = datetime.now()
        
        # 更新交互模式
        insights = analysis.get('insights', {})
        if 'input_preference' in insights:
            input_data = insights['input_preference']
            profile.preferred_input_methods = [
                InteractionType(method) for method in input_data.get('preference_scores', {}).keys()
            ]
            profile.interaction_patterns.update(input_data)
        
        # 更新效率指標
        if 'efficiency_pattern' in insights:
            profile.efficiency_metrics.update(insights['efficiency_pattern'])
        
        # 更新可訪問性需求
        if 'accessibility_needs' in insights:
            profile.accessibility_needs.update(insights['accessibility_needs'])
        
        # 更新設備偏好
        if 'device_adaptation' in insights:
            profile.device_preferences.update(insights['device_adaptation'])
    
    async def _cleanup_expired_cache(self):
        """清理過期緩存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, value in self.analysis_cache.items()
            if current_time - value['timestamp'] > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.analysis_cache[key]
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶洞察摘要"""
        profile = await self.get_or_create_user_profile(user_id)
        recent_analysis = await self.analyze_user_behavior(user_id)
        
        return {
            'user_profile': profile.to_dict(),
            'recent_analysis': recent_analysis,
            'interaction_count': len(self.interaction_history.get(user_id, [])),
            'profile_completeness': self._calculate_profile_completeness(profile)
        }
    
    def _calculate_profile_completeness(self, profile: UserProfile) -> float:
        """計算檔案完整度"""
        completeness_factors = [
            bool(profile.preferred_input_methods),
            bool(profile.interaction_patterns),
            bool(profile.efficiency_metrics),
            bool(profile.device_preferences),
            bool(profile.ui_preferences)
        ]
        
        return sum(completeness_factors) / len(completeness_factors)

