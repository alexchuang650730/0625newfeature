import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  Mic, 
  MicOff, 
  Eye, 
  Settings, 
  Brain, 
  Zap, 
  Users, 
  BarChart3,
  Smartphone,
  Monitor,
  Tablet,
  Volume2,
  VolumeX,
  Activity,
  Target,
  TrendingUp
} from 'lucide-react'
import './App.css'

function App() {
  // 狀態管理
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setSpeaking] = useState(false)
  const [currentUser, setCurrentUser] = useState('demo_user_001')
  const [userProfile, setUserProfile] = useState(null)
  const [realtimeAnalysis, setRealtimeAnalysis] = useState(null)
  const [voiceCommand, setVoiceCommand] = useState('')
  const [systemMetrics, setSystemMetrics] = useState({
    totalDecisions: 0,
    averageConfidence: 0,
    frameworkDistribution: {},
    activeUsers: 0
  })

  // WebSocket 連接
  const wsRef = useRef(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')

  // 模擬數據
  const mockUserProfile = {
    user_id: 'demo_user_001',
    user_type: 'power_user',
    preferred_input_methods: ['voice', 'visual'],
    efficiency_metrics: {
      success_rate: 0.92,
      avg_task_duration: 1200,
      task_completion_rate: 0.89
    },
    accessibility_needs: {
      needs_accessibility_features: false,
      accessibility_score: 0.2
    },
    device_preferences: {
      primary_device: 'desktop',
      screen_preference: 'large'
    }
  }

  const mockRealtimeAnalysis = {
    overall_confidence: 0.85,
    user_type: 'power_user',
    recommendations: [
      'voice_interface_optimization',
      'visual_debugging_enhancement'
    ],
    insights: {
      input_preference: {
        primary_preference: 'voice',
        confidence: 0.9
      },
      efficiency_pattern: {
        efficiency_level: 'expert',
        learning_trend: 0.15
      }
    }
  }

  // 初始化連接
  useEffect(() => {
    // 模擬 WebSocket 連接
    const connectToSmartUI = () => {
      setConnectionStatus('connecting')
      
      // 模擬連接延遲
      setTimeout(() => {
        setIsConnected(true)
        setConnectionStatus('connected')
        setUserProfile(mockUserProfile)
        setRealtimeAnalysis(mockRealtimeAnalysis)
        setSystemMetrics({
          totalDecisions: 1247,
          averageConfidence: 0.83,
          frameworkDistribution: {
            stagewise: 35,
            livekit: 28,
            smartui: 37
          },
          activeUsers: 23
        })
      }, 2000)
    }

    connectToSmartUI()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // 語音命令處理
  const handleVoiceCommand = async () => {
    if (!isListening) {
      setIsListening(true)
      setVoiceCommand('正在聽取語音指令...')
      
      // 模擬語音識別
      setTimeout(() => {
        const commands = [
          '修改按鈕顏色為藍色',
          '增加字體大小',
          '切換到深色主題',
          '顯示用戶統計',
          '開啟可視化調試'
        ]
        const randomCommand = commands[Math.floor(Math.random() * commands.length)]
        setVoiceCommand(`識別到指令: "${randomCommand}"`)
        setIsListening(false)
        
        // 模擬處理結果
        setTimeout(() => {
          setVoiceCommand(`✅ 指令已執行: ${randomCommand}`)
        }, 1000)
      }, 3000)
    } else {
      setIsListening(false)
      setVoiceCommand('')
    }
  }

  // 可視化調試
  const handleVisualDebug = () => {
    alert('🔍 可視化調試模式已啟動！\n\n在實際應用中，這會啟動 Stagewise 可視化調試工具，允許您：\n• 檢查頁面元素\n• 實時修改樣式\n• 分析性能指標\n• 查看交互熱力圖')
  }

  // 語音回饋
  const handleSpeechFeedback = () => {
    setSpeaking(!isSpeaking)
    if (!isSpeaking) {
      // 模擬語音合成
      setTimeout(() => {
        setSpeaking(false)
      }, 2000)
    }
  }

  // 獲取設備圖標
  const getDeviceIcon = (device) => {
    switch (device) {
      case 'mobile': return <Smartphone className="h-4 w-4" />
      case 'tablet': return <Tablet className="h-4 w-4" />
      default: return <Monitor className="h-4 w-4" />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* 頭部 */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              SmartUI Fusion
            </h1>
            <Zap className="h-8 w-8 text-purple-600" />
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            三框架智慧UI整合平台 - 深度整合 smartui_mcp 的革命性用戶界面系統
          </p>
          
          {/* 連接狀態 */}
          <div className="flex items-center justify-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
            <span className="text-sm font-medium">
              {connectionStatus === 'connecting' ? '正在連接...' : 
               connectionStatus === 'connected' ? '已連接到 SmartUI Fusion' : '未連接'}
            </span>
          </div>
        </div>

        {/* 主要功能區域 */}
        <Tabs defaultValue="interaction" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="interaction">多模態交互</TabsTrigger>
            <TabsTrigger value="analysis">用戶分析</TabsTrigger>
            <TabsTrigger value="debug">可視化調試</TabsTrigger>
            <TabsTrigger value="metrics">系統指標</TabsTrigger>
          </TabsList>

          {/* 多模態交互 */}
          <TabsContent value="interaction" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* 語音交互 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Mic className="h-5 w-5" />
                    <span>語音交互</span>
                  </CardTitle>
                  <CardDescription>
                    基於 LiveKit 的智能語音命令系統
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button 
                    onClick={handleVoiceCommand}
                    className={`w-full ${isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                    disabled={!isConnected}
                  >
                    {isListening ? (
                      <>
                        <MicOff className="h-4 w-4 mr-2" />
                        停止聽取
                      </>
                    ) : (
                      <>
                        <Mic className="h-4 w-4 mr-2" />
                        開始語音命令
                      </>
                    )}
                  </Button>
                  
                  {voiceCommand && (
                    <Alert>
                      <AlertDescription>{voiceCommand}</AlertDescription>
                    </Alert>
                  )}
                  
                  <Button 
                    onClick={handleSpeechFeedback}
                    variant="outline"
                    className="w-full"
                    disabled={!isConnected}
                  >
                    {isSpeaking ? (
                      <>
                        <VolumeX className="h-4 w-4 mr-2" />
                        停止語音回饋
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-4 w-4 mr-2" />
                        語音回饋
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* 可視化調試 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Eye className="h-5 w-5" />
                    <span>可視化調試</span>
                  </CardTitle>
                  <CardDescription>
                    基於 Stagewise 的智能界面調試工具
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button 
                    onClick={handleVisualDebug}
                    className="w-full bg-green-500 hover:bg-green-600"
                    disabled={!isConnected}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    啟動可視化調試
                  </Button>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>元素檢查</span>
                      <Badge variant="secondary">已啟用</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>實時編輯</span>
                      <Badge variant="secondary">已啟用</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>性能監控</span>
                      <Badge variant="secondary">已啟用</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 智能適配 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Settings className="h-5 w-5" />
                    <span>智能適配</span>
                  </CardTitle>
                  <CardDescription>
                    基於用戶行為的自動界面優化
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {userProfile && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">用戶類型</span>
                        <Badge>{userProfile.user_type}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">主要設備</span>
                        <div className="flex items-center space-x-1">
                          {getDeviceIcon(userProfile.device_preferences.primary_device)}
                          <span className="text-sm">{userProfile.device_preferences.primary_device}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">偏好輸入</span>
                        <div className="flex space-x-1">
                          {userProfile.preferred_input_methods.map((method, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {method}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 用戶分析 */}
          <TabsContent value="analysis" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* 用戶檔案 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5" />
                    <span>用戶檔案分析</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {userProfile ? (
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">任務成功率</span>
                          <span className="text-sm">{Math.round(userProfile.efficiency_metrics.success_rate * 100)}%</span>
                        </div>
                        <Progress value={userProfile.efficiency_metrics.success_rate * 100} />
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">任務完成率</span>
                          <span className="text-sm">{Math.round(userProfile.efficiency_metrics.task_completion_rate * 100)}%</span>
                        </div>
                        <Progress value={userProfile.efficiency_metrics.task_completion_rate * 100} />
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">可訪問性分數</span>
                          <span className="text-sm">{Math.round(userProfile.accessibility_needs.accessibility_score * 100)}%</span>
                        </div>
                        <Progress value={userProfile.accessibility_needs.accessibility_score * 100} />
                      </div>
                      
                      <div className="pt-2 border-t">
                        <div className="text-sm text-gray-600">
                          平均任務時間: {Math.round(userProfile.efficiency_metrics.avg_task_duration / 1000)}秒
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500">載入用戶數據中...</div>
                  )}
                </CardContent>
              </Card>

              {/* 實時分析 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5" />
                    <span>實時行為分析</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {realtimeAnalysis ? (
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">分析置信度</span>
                          <span className="text-sm">{Math.round(realtimeAnalysis.overall_confidence * 100)}%</span>
                        </div>
                        <Progress value={realtimeAnalysis.overall_confidence * 100} />
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium mb-2">智能建議</div>
                        <div className="space-y-1">
                          {realtimeAnalysis.recommendations.map((rec, index) => (
                            <Badge key={index} variant="outline" className="mr-1 mb-1">
                              {rec.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium mb-2">學習趨勢</div>
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-4 w-4 text-green-500" />
                          <span className="text-sm">
                            效率提升 {Math.round(realtimeAnalysis.insights.efficiency_pattern.learning_trend * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500">載入分析數據中...</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 可視化調試詳情 */}
          <TabsContent value="debug" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Stagewise 可視化調試工具</CardTitle>
                <CardDescription>
                  智能界面分析和實時調試功能
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <Target className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                    <h3 className="font-medium">元素定位</h3>
                    <p className="text-sm text-gray-600">精確識別和標註頁面元素</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                    <h3 className="font-medium">性能分析</h3>
                    <p className="text-sm text-gray-600">實時性能監控和優化建議</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <Settings className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                    <h3 className="font-medium">實時編輯</h3>
                    <p className="text-sm text-gray-600">即時修改樣式和佈局</p>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">調試功能特色</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• 智能元素識別和語義分析</li>
                    <li>• 實時樣式編輯和預覽</li>
                    <li>• 性能熱力圖和瓶頸分析</li>
                    <li>• 用戶交互路徑追蹤</li>
                    <li>• 可訪問性自動檢測</li>
                    <li>• 響應式設計測試</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 系統指標 */}
          <TabsContent value="metrics" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">總決策數</p>
                      <p className="text-2xl font-bold">{systemMetrics.totalDecisions.toLocaleString()}</p>
                    </div>
                    <Brain className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">平均置信度</p>
                      <p className="text-2xl font-bold">{Math.round(systemMetrics.averageConfidence * 100)}%</p>
                    </div>
                    <Target className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">活躍用戶</p>
                      <p className="text-2xl font-bold">{systemMetrics.activeUsers}</p>
                    </div>
                    <Users className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">系統狀態</p>
                      <p className="text-2xl font-bold text-green-600">正常</p>
                    </div>
                    <Activity className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* 框架分佈 */}
            <Card>
              <CardHeader>
                <CardTitle>三框架使用分佈</CardTitle>
                <CardDescription>各框架在決策中的使用比例</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Stagewise (可視化調試)</span>
                      <span className="text-sm">{systemMetrics.frameworkDistribution.stagewise}%</span>
                    </div>
                    <Progress value={systemMetrics.frameworkDistribution.stagewise} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">LiveKit (語音交互)</span>
                      <span className="text-sm">{systemMetrics.frameworkDistribution.livekit}%</span>
                    </div>
                    <Progress value={systemMetrics.frameworkDistribution.livekit} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">SmartUI (智能決策)</span>
                      <span className="text-sm">{systemMetrics.frameworkDistribution.smartui}%</span>
                    </div>
                    <Progress value={systemMetrics.frameworkDistribution.smartui} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* 底部信息 */}
        <div className="text-center text-sm text-gray-500 space-y-2">
          <p>SmartUI Fusion - 三框架智慧UI整合平台</p>
          <p>深度整合 smartui_mcp | 支持多模態交互 | 實時智能分析</p>
          <div className="flex justify-center space-x-4">
            <Badge variant="outline">React 18+</Badge>
            <Badge variant="outline">WebSocket</Badge>
            <Badge variant="outline">實時分析</Badge>
            <Badge variant="outline">多模態交互</Badge>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

