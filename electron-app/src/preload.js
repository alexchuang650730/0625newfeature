const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 給渲染進程
contextBridge.exposeInMainWorld('electronAPI', {
    // 配置管理
    getConfig: () => ipcRenderer.invoke('get-config'),
    updateConfig: (config) => ipcRenderer.invoke('update-config', config),
    
    // 服務器連接
    connectServer: () => ipcRenderer.invoke('connect-server'),
    disconnectServer: () => ipcRenderer.invoke('disconnect-server'),
    
    // 語音命令
    startVoiceCommand: () => ipcRenderer.invoke('start-voice-command'),
    stopVoiceCommand: () => ipcRenderer.invoke('stop-voice-command'),
    
    // 可視化調試
    toggleVisualDebug: () => ipcRenderer.invoke('toggle-visual-debug'),
    
    // 用戶分析
    getUserProfile: () => ipcRenderer.invoke('get-user-profile'),
    
    // 文件對話框
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
    showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
    
    // 事件監聽
    onConnectionStatus: (callback) => {
        ipcRenderer.on('connection-status', (event, data) => callback(data));
    },
    onConnectionError: (callback) => {
        ipcRenderer.on('connection-error', (event, data) => callback(data));
    },
    onUserProfileUpdate: (callback) => {
        ipcRenderer.on('user-profile-update', (event, data) => callback(data));
    },
    onVoiceCommandResult: (callback) => {
        ipcRenderer.on('voice-command-result', (event, data) => callback(data));
    },
    onVoiceListeningStatus: (callback) => {
        ipcRenderer.on('voice-listening-status', (event, data) => callback(data));
    },
    onVisualDebugData: (callback) => {
        ipcRenderer.on('visual-debug-data', (event, data) => callback(data));
    },
    onRealtimeAnalysis: (callback) => {
        ipcRenderer.on('realtime-analysis', (event, data) => callback(data));
    },
    onApplySuggestion: (callback) => {
        ipcRenderer.on('apply-suggestion', (event, data) => callback(data));
    },
    onCreateProject: (callback) => {
        ipcRenderer.on('create-project', (event, data) => callback(data));
    },
    onOpenProject: (callback) => {
        ipcRenderer.on('open-project', (event, data) => callback(data));
    },
    
    // 移除事件監聽器
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});

