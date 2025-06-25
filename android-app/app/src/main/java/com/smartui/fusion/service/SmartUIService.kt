package com.smartui.fusion.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.lifecycle.MutableLiveData
import com.google.gson.Gson
import com.smartui.fusion.R
import com.smartui.fusion.model.*
import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

class SmartUIService : Service() {
    
    companion object {
        const val CHANNEL_ID = "SmartUIServiceChannel"
        const val NOTIFICATION_ID = 1
        
        const val ACTION_CONNECT = "com.smartui.fusion.ACTION_CONNECT"
        const val ACTION_DISCONNECT = "com.smartui.fusion.ACTION_DISCONNECT"
        const val ACTION_START_VOICE = "com.smartui.fusion.ACTION_START_VOICE"
        const val ACTION_STOP_VOICE = "com.smartui.fusion.ACTION_STOP_VOICE"
    }
    
    private val binder = SmartUIBinder()
    private var webSocketClient: WebSocketClient? = null
    private val gson = Gson()
    private val executor: ScheduledExecutorService = Executors.newScheduledThreadPool(2)
    
    // LiveData for communication with UI
    val connectionStatus = MutableLiveData<Boolean>()
    val userProfile = MutableLiveData<UserProfile>()
    val voiceCommandResult = MutableLiveData<VoiceCommandResult>()
    val visualDebugData = MutableLiveData<VisualDebugData>()
    val smartSuggestion = MutableLiveData<SmartSuggestion>()
    val realtimeAnalysis = MutableLiveData<RealtimeAnalysis>()
    val errorMessage = MutableLiveData<String>()
    
    private var serverUrl = "ws://localhost:8000/ws"
    private var isConnected = false
    private var isVoiceListening = false
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    
    inner class SmartUIBinder : Binder() {
        fun getService(): SmartUIService = this@SmartUIService
    }
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        loadConfiguration()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CONNECT -> connectToServer()
            ACTION_DISCONNECT -> disconnectFromServer()
            ACTION_START_VOICE -> startVoiceCommand()
            ACTION_STOP_VOICE -> stopVoiceCommand()
        }
        
        startForeground(NOTIFICATION_ID, createNotification())
        return START_STICKY
    }
    
    override fun onBind(intent: Intent): IBinder {
        return binder
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "SmartUI Fusion Service",
                NotificationManager.IMPORTANCE_LOW
            )
            serviceChannel.description = "SmartUI Fusion 後台服務"
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }
    
    private fun createNotification(): Notification {
        val notificationIntent = Intent(this, com.smartui.fusion.MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val statusText = if (isConnected) "已連接" else "未連接"
        val voiceText = if (isVoiceListening) " | 語音聽取中" else ""
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("SmartUI Fusion")
            .setContentText("狀態: $statusText$voiceText")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
    
    private fun updateNotification() {
        val notification = createNotification()
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
    
    private fun loadConfiguration() {
        val sharedPrefs = getSharedPreferences("smartui_config", Context.MODE_PRIVATE)
        serverUrl = sharedPrefs.getString("server_url", "ws://localhost:8000/ws") ?: "ws://localhost:8000/ws"
    }
    
    fun connectToServer() {
        if (isConnected) {
            return
        }
        
        try {
            val uri = URI(serverUrl)
            webSocketClient = object : WebSocketClient(uri) {
                override fun onOpen(handshake: ServerHandshake?) {
                    isConnected = true
                    reconnectAttempts = 0
                    connectionStatus.postValue(true)
                    updateNotification()
                    
                    // 發送初始化消息
                    sendMessage(SmartUIMessage(
                        type = "init",
                        data = mapOf(
                            "client_type" to "android_app",
                            "user_id" to getUserId(),
                            "device_info" to getDeviceInfo()
                        )
                    ))
                }
                
                override fun onMessage(message: String?) {
                    message?.let { handleServerMessage(it) }
                }
                
                override fun onClose(code: Int, reason: String?, remote: Boolean) {
                    isConnected = false
                    connectionStatus.postValue(false)
                    updateNotification()
                    
                    // 自動重連
                    if (reconnectAttempts < maxReconnectAttempts) {
                        scheduleReconnect()
                    }
                }
                
                override fun onError(ex: Exception?) {
                    errorMessage.postValue("連接錯誤: ${ex?.message}")
                    isConnected = false
                    connectionStatus.postValue(false)
                }
            }
            
            webSocketClient?.connect()
            
        } catch (e: Exception) {
            errorMessage.postValue("連接失敗: ${e.message}")
        }
    }
    
    fun disconnectFromServer() {
        webSocketClient?.close()
        isConnected = false
        connectionStatus.postValue(false)
        updateNotification()
    }
    
    private fun scheduleReconnect() {
        reconnectAttempts++
        val delay = (reconnectAttempts * 5).toLong() // 5, 10, 15, 20, 25 秒
        
        executor.schedule({
            if (!isConnected) {
                connectToServer()
            }
        }, delay, TimeUnit.SECONDS)
    }
    
    private fun handleServerMessage(message: String) {
        try {
            val smartUIMessage = gson.fromJson(message, SmartUIMessage::class.java)
            
            when (smartUIMessage.type) {
                "user_profile_update" -> {
                    val profile = gson.fromJson(
                        gson.toJson(smartUIMessage.data),
                        UserProfile::class.java
                    )
                    userProfile.postValue(profile)
                }
                
                "voice_command_result" -> {
                    val result = gson.fromJson(
                        gson.toJson(smartUIMessage.data),
                        VoiceCommandResult::class.java
                    )
                    voiceCommandResult.postValue(result)
                }
                
                "visual_debug_data" -> {
                    val debugData = gson.fromJson(
                        gson.toJson(smartUIMessage.data),
                        VisualDebugData::class.java
                    )
                    visualDebugData.postValue(debugData)
                }
                
                "smart_suggestion" -> {
                    val suggestion = gson.fromJson(
                        gson.toJson(smartUIMessage.data),
                        SmartSuggestion::class.java
                    )
                    smartSuggestion.postValue(suggestion)
                }
                
                "realtime_analysis" -> {
                    val analysis = gson.fromJson(
                        gson.toJson(smartUIMessage.data),
                        RealtimeAnalysis::class.java
                    )
                    realtimeAnalysis.postValue(analysis)
                }
            }
            
        } catch (e: Exception) {
            errorMessage.postValue("解析服務器消息失敗: ${e.message}")
        }
    }
    
    fun startVoiceCommand() {
        if (!isConnected) {
            errorMessage.postValue("請先連接到 SmartUI 服務器")
            return
        }
        
        isVoiceListening = true
        updateNotification()
        
        sendMessage(SmartUIMessage(
            type = "start_voice_command",
            data = mapOf(
                "context" to getCurrentContext()
            )
        ))
    }
    
    fun stopVoiceCommand() {
        isVoiceListening = false
        updateNotification()
        
        sendMessage(SmartUIMessage(
            type = "stop_voice_command",
            data = emptyMap()
        ))
    }
    
    fun toggleVisualDebug() {
        if (!isConnected) {
            errorMessage.postValue("請先連接到 SmartUI 服務器")
            return
        }
        
        sendMessage(SmartUIMessage(
            type = "toggle_visual_debug",
            data = mapOf(
                "device_info" to getDeviceInfo()
            )
        ))
    }
    
    fun sendUserInteraction(interaction: UserInteraction) {
        sendMessage(SmartUIMessage(
            type = "user_interaction",
            data = mapOf(
                "interaction" to interaction,
                "timestamp" to System.currentTimeMillis(),
                "context" to getCurrentContext()
            )
        ))
    }
    
    fun applySuggestion(suggestion: SmartSuggestion) {
        sendMessage(SmartUIMessage(
            type = "apply_suggestion",
            data = mapOf(
                "suggestion_id" to suggestion.id,
                "suggestion_type" to suggestion.type
            )
        ))
    }
    
    private fun sendMessage(message: SmartUIMessage) {
        if (isConnected && webSocketClient != null) {
            try {
                val json = gson.toJson(message)
                webSocketClient?.send(json)
            } catch (e: Exception) {
                errorMessage.postValue("發送消息失敗: ${e.message}")
            }
        }
    }
    
    private fun getUserId(): String {
        val sharedPrefs = getSharedPreferences("smartui_user", Context.MODE_PRIVATE)
        var userId = sharedPrefs.getString("user_id", null)
        
        if (userId == null) {
            userId = "android_${System.currentTimeMillis()}"
            sharedPrefs.edit().putString("user_id", userId).apply()
        }
        
        return userId
    }
    
    private fun getDeviceInfo(): Map<String, Any> {
        return mapOf(
            "platform" to "Android",
            "version" to Build.VERSION.RELEASE,
            "model" to Build.MODEL,
            "manufacturer" to Build.MANUFACTURER,
            "app_version" to getAppVersion()
        )
    }
    
    private fun getCurrentContext(): Map<String, Any> {
        return mapOf(
            "timestamp" to System.currentTimeMillis(),
            "device_info" to getDeviceInfo(),
            "app_state" to "foreground" // 可以根據實際情況調整
        )
    }
    
    private fun getAppVersion(): String {
        return try {
            val packageInfo = packageManager.getPackageInfo(packageName, 0)
            packageInfo.versionName ?: "1.0.0"
        } catch (e: Exception) {
            "1.0.0"
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        disconnectFromServer()
        executor.shutdown()
    }
}

