const { app, BrowserWindow, Menu, ipcMain, dialog, shell, globalShortcut } = require('electron');
const path = require('path');
const WebSocket = require('ws');
const Store = require('electron-store');

// 配置存儲
const store = new Store();

class SmartUIFusionApp {
    constructor() {
        this.mainWindow = null;
        this.settingsWindow = null;
        this.analyticsWindow = null;
        this.ws = null;
        this.isVoiceListening = false;
        this.userProfile = null;
        
        this.config = {
            serverUrl: store.get('serverUrl', 'ws://localhost:8000/ws'),
            enableVoiceCommands: store.get('enableVoiceCommands', true),
            enableVisualDebug: store.get('enableVisualDebug', true),
            enableUserAnalytics: store.get('enableUserAnalytics', true),
            autoConnect: store.get('autoConnect', true),
            windowBounds: store.get('windowBounds', { width: 1200, height: 800 })
        };

        this.initialize();
    }

    initialize() {
        // 當 Electron 完成初始化時創建窗口
        app.whenReady().then(() => {
            this.createMainWindow();
            this.setupMenu();
            this.setupGlobalShortcuts();
            this.setupIPC();
            
            if (this.config.autoConnect) {
                this.connectToServer();
            }
        });

        // 當所有窗口關閉時退出應用
        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        // 在 macOS 上，當點擊 dock 圖標時重新創建窗口
        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createMainWindow();
            }
        });

        // 應用退出前清理
        app.on('before-quit', () => {
            this.cleanup();
        });
    }

    createMainWindow() {
        // 創建主窗口
        this.mainWindow = new BrowserWindow({
            width: this.config.windowBounds.width,
            height: this.config.windowBounds.height,
            minWidth: 800,
            minHeight: 600,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'preload.js')
            },
            icon: path.join(__dirname, '../assets/icon.png'),
            title: 'SmartUI Fusion',
            show: false // 先隱藏，載入完成後顯示
        });

        // 載入主頁面
        this.mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

        // 窗口準備好後顯示
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            
            // 開發模式下打開開發者工具
            if (process.argv.includes('--dev')) {
                this.mainWindow.webContents.openDevTools();
            }
        });

        // 保存窗口大小和位置
        this.mainWindow.on('close', () => {
            const bounds = this.mainWindow.getBounds();
            store.set('windowBounds', bounds);
        });

        // 處理外部鏈接
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });
    }

    setupMenu() {
        const template = [
            {
                label: '文件',
                submenu: [
                    {
                        label: '新建項目',
                        accelerator: 'CmdOrCtrl+N',
                        click: () => this.createNewProject()
                    },
                    {
                        label: '打開項目',
                        accelerator: 'CmdOrCtrl+O',
                        click: () => this.openProject()
                    },
                    { type: 'separator' },
                    {
                        label: '設置',
                        accelerator: 'CmdOrCtrl+,',
                        click: () => this.openSettings()
                    },
                    { type: 'separator' },
                    {
                        label: '退出',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => app.quit()
                    }
                ]
            },
            {
                label: 'SmartUI',
                submenu: [
                    {
                        label: '開始語音命令',
                        accelerator: 'CmdOrCtrl+Shift+V',
                        click: () => this.startVoiceCommand()
                    },
                    {
                        label: '停止語音命令',
                        accelerator: 'CmdOrCtrl+Shift+S',
                        click: () => this.stopVoiceCommand()
                    },
                    { type: 'separator' },
                    {
                        label: '可視化調試',
                        accelerator: 'CmdOrCtrl+Shift+D',
                        click: () => this.toggleVisualDebug()
                    },
                    {
                        label: '用戶分析',
                        accelerator: 'CmdOrCtrl+Shift+A',
                        click: () => this.showUserAnalytics()
                    },
                    { type: 'separator' },
                    {
                        label: '連接服務器',
                        click: () => this.connectToServer()
                    },
                    {
                        label: '斷開連接',
                        click: () => this.disconnectFromServer()
                    }
                ]
            },
            {
                label: '視圖',
                submenu: [
                    {
                        label: '重新載入',
                        accelerator: 'CmdOrCtrl+R',
                        click: () => this.mainWindow.reload()
                    },
                    {
                        label: '強制重新載入',
                        accelerator: 'CmdOrCtrl+Shift+R',
                        click: () => this.mainWindow.webContents.reloadIgnoringCache()
                    },
                    {
                        label: '開發者工具',
                        accelerator: 'F12',
                        click: () => this.mainWindow.webContents.toggleDevTools()
                    },
                    { type: 'separator' },
                    {
                        label: '實際大小',
                        accelerator: 'CmdOrCtrl+0',
                        click: () => this.mainWindow.webContents.setZoomLevel(0)
                    },
                    {
                        label: '放大',
                        accelerator: 'CmdOrCtrl+Plus',
                        click: () => {
                            const currentZoom = this.mainWindow.webContents.getZoomLevel();
                            this.mainWindow.webContents.setZoomLevel(currentZoom + 1);
                        }
                    },
                    {
                        label: '縮小',
                        accelerator: 'CmdOrCtrl+-',
                        click: () => {
                            const currentZoom = this.mainWindow.webContents.getZoomLevel();
                            this.mainWindow.webContents.setZoomLevel(currentZoom - 1);
                        }
                    },
                    { type: 'separator' },
                    {
                        label: '全屏',
                        accelerator: 'F11',
                        click: () => {
                            const isFullScreen = this.mainWindow.isFullScreen();
                            this.mainWindow.setFullScreen(!isFullScreen);
                        }
                    }
                ]
            },
            {
                label: '幫助',
                submenu: [
                    {
                        label: '關於 SmartUI Fusion',
                        click: () => this.showAbout()
                    },
                    {
                        label: '用戶手冊',
                        click: () => shell.openExternal('https://smartui-fusion.com/docs')
                    },
                    {
                        label: '報告問題',
                        click: () => shell.openExternal('https://github.com/smartui-fusion/issues')
                    }
                ]
            }
        ];

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    setupGlobalShortcuts() {
        // 註冊全局快捷鍵
        globalShortcut.register('CommandOrControl+Alt+V', () => {
            this.startVoiceCommand();
        });

        globalShortcut.register('CommandOrControl+Alt+S', () => {
            this.stopVoiceCommand();
        });

        globalShortcut.register('CommandOrControl+Alt+D', () => {
            this.toggleVisualDebug();
        });
    }

    setupIPC() {
        // 處理來自渲染進程的消息
        ipcMain.handle('get-config', () => {
            return this.config;
        });

        ipcMain.handle('update-config', (event, newConfig) => {
            this.config = { ...this.config, ...newConfig };
            // 保存到持久化存儲
            Object.keys(newConfig).forEach(key => {
                store.set(key, newConfig[key]);
            });
            return this.config;
        });

        ipcMain.handle('connect-server', () => {
            return this.connectToServer();
        });

        ipcMain.handle('disconnect-server', () => {
            return this.disconnectFromServer();
        });

        ipcMain.handle('start-voice-command', () => {
            return this.startVoiceCommand();
        });

        ipcMain.handle('stop-voice-command', () => {
            return this.stopVoiceCommand();
        });

        ipcMain.handle('toggle-visual-debug', () => {
            return this.toggleVisualDebug();
        });

        ipcMain.handle('get-user-profile', () => {
            return this.userProfile;
        });

        ipcMain.handle('show-save-dialog', async (event, options) => {
            const result = await dialog.showSaveDialog(this.mainWindow, options);
            return result;
        });

        ipcMain.handle('show-open-dialog', async (event, options) => {
            const result = await dialog.showOpenDialog(this.mainWindow, options);
            return result;
        });

        ipcMain.handle('show-message-box', async (event, options) => {
            const result = await dialog.showMessageBox(this.mainWindow, options);
            return result;
        });
    }

    async connectToServer() {
        try {
            console.log(`正在連接到 SmartUI 服務器: ${this.config.serverUrl}`);
            
            this.ws = new WebSocket(this.config.serverUrl);
            
            this.ws.on('open', () => {
                console.log('已連接到 SmartUI Fusion 服務器');
                this.sendToRenderer('connection-status', { connected: true });
                
                // 發送初始化消息
                this.sendMessage({
                    type: 'init',
                    data: {
                        client_type: 'desktop_app',
                        user_id: this.getUserId(),
                        platform: process.platform,
                        app_version: app.getVersion()
                    }
                });
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleServerMessage(message);
                } catch (error) {
                    console.error('解析服務器消息失敗:', error);
                }
            });

            this.ws.on('close', () => {
                console.log('與 SmartUI 服務器斷開連接');
                this.sendToRenderer('connection-status', { connected: false });
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket 錯誤:', error);
                this.sendToRenderer('connection-error', { error: error.message });
            });

            return { success: true };
        } catch (error) {
            console.error('連接失敗:', error);
            return { success: false, error: error.message };
        }
    }

    disconnectFromServer() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        return { success: true };
    }

    handleServerMessage(message) {
        console.log('收到服務器消息:', message.type);
        
        switch (message.type) {
            case 'user_profile_update':
                this.userProfile = message.data;
                this.sendToRenderer('user-profile-update', this.userProfile);
                break;
                
            case 'voice_command_result':
                this.handleVoiceCommandResult(message.data);
                break;
                
            case 'visual_debug_data':
                this.sendToRenderer('visual-debug-data', message.data);
                break;
                
            case 'smart_suggestion':
                this.showSmartSuggestion(message.data);
                break;
                
            case 'realtime_analysis':
                this.sendToRenderer('realtime-analysis', message.data);
                break;
                
            default:
                console.log('未知消息類型:', message.type);
        }
    }

    handleVoiceCommandResult(data) {
        console.log('語音命令結果:', data.command);
        this.sendToRenderer('voice-command-result', data);
        
        // 根據命令類型執行相應操作
        switch (data.action) {
            case 'open_file':
                this.openFileInSystem(data.file_path);
                break;
                
            case 'create_project':
                this.createNewProject(data.project_type);
                break;
                
            case 'show_analytics':
                this.showUserAnalytics();
                break;
                
            case 'toggle_debug':
                this.toggleVisualDebug();
                break;
                
            default:
                // 將命令轉發給渲染進程處理
                this.sendToRenderer('voice-command-action', data);
        }
    }

    showSmartSuggestion(data) {
        const options = {
            type: 'info',
            title: 'SmartUI 建議',
            message: data.suggestion,
            buttons: data.actionable ? ['應用建議', '忽略'] : ['確定']
        };

        dialog.showMessageBox(this.mainWindow, options).then(result => {
            if (result.response === 0 && data.actionable) {
                this.applySuggestion(data);
            }
        });
    }

    applySuggestion(suggestion) {
        console.log('應用建議:', suggestion.type);
        this.sendToRenderer('apply-suggestion', suggestion);
    }

    async startVoiceCommand() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            dialog.showErrorBox('錯誤', '請先連接到 SmartUI 服務器');
            return { success: false, error: '未連接到服務器' };
        }

        if (this.isVoiceListening) {
            return { success: false, error: '語音命令已在運行中' };
        }

        this.isVoiceListening = true;
        
        this.sendMessage({
            type: 'start_voice_command',
            data: {
                context: this.getCurrentContext()
            }
        });

        this.sendToRenderer('voice-listening-status', { listening: true });
        
        return { success: true };
    }

    async stopVoiceCommand() {
        if (!this.isVoiceListening) {
            return { success: false, error: '語音命令未在運行' };
        }

        this.isVoiceListening = false;
        
        this.sendMessage({
            type: 'stop_voice_command',
            data: {}
        });

        this.sendToRenderer('voice-listening-status', { listening: false });
        
        return { success: true };
    }

    async toggleVisualDebug() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            dialog.showErrorBox('錯誤', '請先連接到 SmartUI 服務器');
            return { success: false, error: '未連接到服務器' };
        }

        this.sendMessage({
            type: 'toggle_visual_debug',
            data: {
                platform: process.platform,
                app_version: app.getVersion()
            }
        });

        return { success: true };
    }

    showUserAnalytics() {
        if (this.analyticsWindow) {
            this.analyticsWindow.focus();
            return;
        }

        this.analyticsWindow = new BrowserWindow({
            width: 800,
            height: 600,
            parent: this.mainWindow,
            modal: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            },
            title: 'SmartUI 用戶分析'
        });

        this.analyticsWindow.loadFile(path.join(__dirname, 'renderer/analytics.html'));

        this.analyticsWindow.on('closed', () => {
            this.analyticsWindow = null;
        });
    }

    openSettings() {
        if (this.settingsWindow) {
            this.settingsWindow.focus();
            return;
        }

        this.settingsWindow = new BrowserWindow({
            width: 600,
            height: 500,
            parent: this.mainWindow,
            modal: true,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            },
            title: 'SmartUI Fusion 設置'
        });

        this.settingsWindow.loadFile(path.join(__dirname, 'renderer/settings.html'));

        this.settingsWindow.on('closed', () => {
            this.settingsWindow = null;
        });
    }

    async createNewProject(projectType = 'web') {
        const result = await dialog.showSaveDialog(this.mainWindow, {
            title: '創建新項目',
            defaultPath: 'my-smartui-project',
            filters: [
                { name: '項目文件夾', extensions: [] }
            ],
            properties: ['createDirectory']
        });

        if (!result.canceled) {
            this.sendToRenderer('create-project', {
                path: result.filePath,
                type: projectType
            });
        }
    }

    async openProject() {
        const result = await dialog.showOpenDialog(this.mainWindow, {
            title: '打開項目',
            properties: ['openDirectory']
        });

        if (!result.canceled && result.filePaths.length > 0) {
            this.sendToRenderer('open-project', {
                path: result.filePaths[0]
            });
        }
    }

    openFileInSystem(filePath) {
        shell.openPath(filePath);
    }

    showAbout() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: '關於 SmartUI Fusion',
            message: 'SmartUI Fusion',
            detail: `版本: ${app.getVersion()}\\n\\n智能UI開發和分析工具\\n\\n© 2024 SmartUI Fusion Team`,
            buttons: ['確定']
        });
    }

    getCurrentContext() {
        return {
            platform: process.platform,
            app_version: app.getVersion(),
            timestamp: Date.now()
        };
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    sendToRenderer(channel, data) {
        if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            this.mainWindow.webContents.send(channel, data);
        }
    }

    getUserId() {
        // 使用機器ID作為用戶標識
        return require('os').hostname() + '-' + require('os').userInfo().username;
    }

    cleanup() {
        // 清理全局快捷鍵
        globalShortcut.unregisterAll();
        
        // 關閉 WebSocket 連接
        if (this.ws) {
            this.ws.close();
        }
    }
}

// 創建應用實例
new SmartUIFusionApp();

