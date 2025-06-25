package com.smartui.fusion

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.snackbar.Snackbar
import com.karumi.dexter.Dexter
import com.karumi.dexter.MultiplePermissionsReport
import com.karumi.dexter.PermissionToken
import com.karumi.dexter.listener.PermissionRequest
import com.karumi.dexter.listener.multi.MultiplePermissionsListener
import com.smartui.fusion.databinding.ActivityMainBinding
import com.smartui.fusion.service.SmartUIService
import com.smartui.fusion.service.VoiceRecognitionService
import com.smartui.fusion.viewmodel.MainViewModel
import java.util.*

class MainActivity : AppCompatActivity(), TextToSpeech.OnInitListener {

    private lateinit var binding: ActivityMainBinding
    private lateinit var viewModel: MainViewModel
    private lateinit var appBarConfiguration: AppBarConfiguration
    
    private var textToSpeech: TextToSpeech? = null
    private var speechRecognizer: SpeechRecognizer? = null
    private var isVoiceListening = false
    
    // 權限請求啟動器
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            initializeSmartUIFeatures()
        } else {
            showPermissionDeniedMessage()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // 初始化 ViewModel
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]
        
        setupUI()
        setupObservers()
        requestPermissions()
    }

    private fun setupUI() {
        setSupportActionBar(binding.toolbar)
        
        // 設置導航
        val navController = findNavController(R.id.nav_host_fragment_content_main)
        val bottomNav = findViewById<BottomNavigationView>(R.id.bottom_navigation)
        
        appBarConfiguration = AppBarConfiguration(
            setOf(
                R.id.nav_home,
                R.id.nav_voice,
                R.id.nav_debug,
                R.id.nav_analytics
            )
        )
        
        setupActionBarWithNavController(navController, appBarConfiguration)
        bottomNav.setupWithNavController(navController)
        
        // 設置 FAB
        binding.fab.setOnClickListener { view ->
            if (isVoiceListening) {
                stopVoiceRecognition()
            } else {
                startVoiceRecognition()
            }
        }
        
        updateFabIcon()
    }

    private fun setupObservers() {
        // 觀察連接狀態
        viewModel.connectionStatus.observe(this) { isConnected ->
            updateConnectionStatus(isConnected)
        }
        
        // 觀察語音狀態
        viewModel.voiceListeningStatus.observe(this) { isListening ->
            isVoiceListening = isListening
            updateFabIcon()
        }
        
        // 觀察用戶檔案
        viewModel.userProfile.observe(this) { profile ->
            // 更新UI顯示用戶信息
            profile?.let {
                showUserProfileUpdate(it)
            }
        }
        
        // 觀察語音命令結果
        viewModel.voiceCommandResult.observe(this) { result ->
            handleVoiceCommandResult(result)
        }
        
        // 觀察智能建議
        viewModel.smartSuggestion.observe(this) { suggestion ->
            showSmartSuggestion(suggestion)
        }
        
        // 觀察錯誤消息
        viewModel.errorMessage.observe(this) { error ->
            showError(error)
        }
    }

    private fun requestPermissions() {
        val permissions = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE
        )
        
        Dexter.withContext(this)
            .withPermissions(*permissions)
            .withListener(object : MultiplePermissionsListener {
                override fun onPermissionsChecked(report: MultiplePermissionsReport) {
                    if (report.areAllPermissionsGranted()) {
                        initializeSmartUIFeatures()
                    } else {
                        showPermissionDeniedMessage()
                    }
                }
                
                override fun onPermissionRationaleShouldBeShown(
                    permissions: List<PermissionRequest>,
                    token: PermissionToken
                ) {
                    token.continuePermissionRequest()
                }
            })
            .check()
    }

    private fun initializeSmartUIFeatures() {
        // 初始化文字轉語音
        textToSpeech = TextToSpeech(this, this)
        
        // 初始化語音識別
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        }
        
        // 啟動 SmartUI 服務
        val serviceIntent = Intent(this, SmartUIService::class.java)
        startForegroundService(serviceIntent)
        
        // 連接到 SmartUI 服務器
        viewModel.connectToServer()
    }

    private fun startVoiceRecognition() {
        if (!checkAudioPermission()) {
            requestAudioPermission()
            return
        }
        
        val intent = Intent(this, VoiceRecognitionService::class.java)
        intent.action = VoiceRecognitionService.ACTION_START_LISTENING
        startForegroundService(intent)
        
        viewModel.startVoiceCommand()
        
        Snackbar.make(binding.root, "語音命令已啟動，請說話...", Snackbar.LENGTH_SHORT).show()
    }

    private fun stopVoiceRecognition() {
        val intent = Intent(this, VoiceRecognitionService::class.java)
        intent.action = VoiceRecognitionService.ACTION_STOP_LISTENING
        startService(intent)
        
        viewModel.stopVoiceCommand()
        
        Snackbar.make(binding.root, "語音命令已停止", Snackbar.LENGTH_SHORT).show()
    }

    private fun handleVoiceCommandResult(result: VoiceCommandResult) {
        when (result.action) {
            "open_analytics" -> {
                startActivity(Intent(this, AnalyticsActivity::class.java))
            }
            "open_settings" -> {
                startActivity(Intent(this, SettingsActivity::class.java))
            }
            "toggle_debug" -> {
                viewModel.toggleVisualDebug()
            }
            "speak_text" -> {
                speakText(result.text ?: "命令已執行")
            }
            "show_toast" -> {
                Toast.makeText(this, result.text ?: "語音命令執行成功", Toast.LENGTH_SHORT).show()
            }
            else -> {
                Toast.makeText(this, "語音命令: ${result.command}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showSmartSuggestion(suggestion: SmartSuggestion) {
        val snackbar = Snackbar.make(
            binding.root,
            "SmartUI 建議: ${suggestion.message}",
            Snackbar.LENGTH_LONG
        )
        
        if (suggestion.actionable) {
            snackbar.setAction("應用") {
                viewModel.applySuggestion(suggestion)
            }
        }
        
        snackbar.show()
    }

    private fun updateConnectionStatus(isConnected: Boolean) {
        val statusText = if (isConnected) "已連接" else "未連接"
        val color = if (isConnected) 
            ContextCompat.getColor(this, R.color.success_green) 
        else 
            ContextCompat.getColor(this, R.color.error_red)
        
        // 更新工具欄狀態指示器
        supportActionBar?.subtitle = "SmartUI: $statusText"
    }

    private fun updateFabIcon() {
        val iconRes = if (isVoiceListening) {
            R.drawable.ic_mic_off
        } else {
            R.drawable.ic_mic
        }
        binding.fab.setImageResource(iconRes)
    }

    private fun showUserProfileUpdate(profile: UserProfile) {
        val message = "用戶檔案已更新 - 類型: ${profile.userType}, 效率: ${(profile.efficiencyMetrics.successRate * 100).toInt()}%"
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
    }

    private fun showError(error: String) {
        Snackbar.make(binding.root, "錯誤: $error", Snackbar.LENGTH_LONG)
            .setBackgroundTint(ContextCompat.getColor(this, R.color.error_red))
            .show()
    }

    private fun showPermissionDeniedMessage() {
        Snackbar.make(
            binding.root,
            "需要權限才能使用 SmartUI 功能",
            Snackbar.LENGTH_LONG
        ).setAction("設置") {
            startActivity(Intent(this, SettingsActivity::class.java))
        }.show()
    }

    private fun checkAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun requestAudioPermission() {
        permissionLauncher.launch(arrayOf(Manifest.permission.RECORD_AUDIO))
    }

    private fun speakText(text: String) {
        textToSpeech?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = textToSpeech?.setLanguage(Locale.TRADITIONAL_CHINESE)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                // 如果不支持繁體中文，使用簡體中文
                textToSpeech?.setLanguage(Locale.SIMPLIFIED_CHINESE)
            }
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                startActivity(Intent(this, SettingsActivity::class.java))
                true
            }
            R.id.action_analytics -> {
                startActivity(Intent(this, AnalyticsActivity::class.java))
                true
            }
            R.id.action_connect -> {
                viewModel.connectToServer()
                true
            }
            R.id.action_disconnect -> {
                viewModel.disconnectFromServer()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        val navController = findNavController(R.id.nav_host_fragment_content_main)
        return navController.navigateUp(appBarConfiguration) || super.onSupportNavigateUp()
    }

    override fun onDestroy() {
        super.onDestroy()
        
        // 清理資源
        textToSpeech?.shutdown()
        speechRecognizer?.destroy()
        
        // 停止服務
        stopService(Intent(this, SmartUIService::class.java))
        stopService(Intent(this, VoiceRecognitionService::class.java))
    }

    override fun onPause() {
        super.onPause()
        if (isVoiceListening) {
            stopVoiceRecognition()
        }
    }
}

