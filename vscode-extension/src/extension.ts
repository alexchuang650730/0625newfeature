import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import axios from 'axios';

interface SmartUIConfig {
    serverUrl: string;
    enableVoiceCommands: boolean;
    enableVisualDebug: boolean;
    enableUserAnalytics: boolean;
    autoConnect: boolean;
}

interface UserProfile {
    user_id: string;
    user_type: string;
    preferred_input_methods: string[];
    efficiency_metrics: {
        success_rate: number;
        avg_task_duration: number;
        task_completion_rate: number;
    };
    accessibility_needs: {
        needs_accessibility_features: boolean;
        accessibility_score: number;
    };
}

class SmartUIFusionExtension {
    private context: vscode.ExtensionContext;
    private config: SmartUIConfig;
    private ws: WebSocket | null = null;
    private statusBarItem: vscode.StatusBarItem;
    private userProfile: UserProfile | null = null;
    private isVoiceListening = false;
    private outputChannel: vscode.OutputChannel;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel('SmartUI Fusion');
        
        // 創建狀態欄項目
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right, 
            100
        );
        this.statusBarItem.text = "$(brain) SmartUI";
        this.statusBarItem.tooltip = "SmartUI Fusion - 點擊打開面板";
        this.statusBarItem.command = 'smartui.openSmartPanel';
        this.statusBarItem.show();

        this.initialize();
    }

    private loadConfiguration(): SmartUIConfig {
        const config = vscode.workspace.getConfiguration('smartui');
        return {
            serverUrl: config.get('serverUrl', 'ws://localhost:8000/ws'),
            enableVoiceCommands: config.get('enableVoiceCommands', true),
            enableVisualDebug: config.get('enableVisualDebug', true),
            enableUserAnalytics: config.get('enableUserAnalytics', true),
            autoConnect: config.get('autoConnect', true)
        };
    }

    private async initialize() {
        this.log('SmartUI Fusion 擴展正在初始化...');
        
        // 設置上下文
        vscode.commands.executeCommand('setContext', 'smartui.enabled', true);
        
        if (this.config.autoConnect) {
            await this.connectToServer();
        }

        // 監聽配置變更
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('smartui')) {
                this.config = this.loadConfiguration();
                this.log('配置已更新');
            }
        });

        // 監聽編輯器變更
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && this.config.enableUserAnalytics) {
                this.trackUserInteraction('editor_switch', {
                    language: editor.document.languageId,
                    fileName: editor.document.fileName
                });
            }
        });

        // 監聽文檔變更
        vscode.workspace.onDidChangeTextDocument(e => {
            if (this.config.enableUserAnalytics) {
                this.trackUserInteraction('text_edit', {
                    language: e.document.languageId,
                    changes: e.contentChanges.length
                });
            }
        });

        this.log('SmartUI Fusion 擴展初始化完成');
    }

    private async connectToServer(): Promise<void> {
        try {
            this.log(`正在連接到 SmartUI 服務器: ${this.config.serverUrl}`);
            
            this.ws = new WebSocket(this.config.serverUrl);
            
            this.ws.on('open', () => {
                this.log('已連接到 SmartUI Fusion 服務器');
                this.statusBarItem.text = "$(brain) SmartUI ✓";
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
                
                // 發送初始化消息
                this.sendMessage({
                    type: 'init',
                    data: {
                        client_type: 'vscode_extension',
                        user_id: this.getUserId(),
                        workspace: vscode.workspace.name || 'unknown'
                    }
                });
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleServerMessage(message);
                } catch (error) {
                    this.log(`解析服務器消息失敗: ${error}`);
                }
            });

            this.ws.on('close', () => {
                this.log('與 SmartUI 服務器斷開連接');
                this.statusBarItem.text = "$(brain) SmartUI ✗";
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            });

            this.ws.on('error', (error) => {
                this.log(`WebSocket 錯誤: ${error.message}`);
                vscode.window.showErrorMessage(`SmartUI 連接錯誤: ${error.message}`);
            });

        } catch (error) {
            this.log(`連接失敗: ${error}`);
            vscode.window.showErrorMessage(`無法連接到 SmartUI 服務器: ${error}`);
        }
    }

    private handleServerMessage(message: any) {
        switch (message.type) {
            case 'user_profile_update':
                this.userProfile = message.data;
                this.log('用戶檔案已更新');
                break;
                
            case 'voice_command_result':
                this.handleVoiceCommandResult(message.data);
                break;
                
            case 'visual_debug_data':
                this.handleVisualDebugData(message.data);
                break;
                
            case 'smart_suggestion':
                this.showSmartSuggestion(message.data);
                break;
                
            default:
                this.log(`未知消息類型: ${message.type}`);
        }
    }

    private handleVoiceCommandResult(data: any) {
        this.log(`語音命令結果: ${data.command}`);
        
        switch (data.action) {
            case 'open_file':
                this.openFile(data.file_path);
                break;
                
            case 'search_text':
                this.searchInWorkspace(data.query);
                break;
                
            case 'run_command':
                vscode.commands.executeCommand(data.command, ...data.args);
                break;
                
            case 'insert_text':
                this.insertTextAtCursor(data.text);
                break;
                
            default:
                vscode.window.showInformationMessage(`語音命令: ${data.command}`);
        }
    }

    private handleVisualDebugData(data: any) {
        // 在 VS Code 中顯示可視化調試信息
        const panel = vscode.window.createWebviewPanel(
            'smartui-debug',
            'SmartUI 可視化調試',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.getDebugWebviewContent(data);
    }

    private showSmartSuggestion(data: any) {
        const message = `SmartUI 建議: ${data.suggestion}`;
        
        if (data.actionable) {
            vscode.window.showInformationMessage(
                message,
                '應用建議',
                '忽略'
            ).then(selection => {
                if (selection === '應用建議') {
                    this.applySuggestion(data);
                }
            });
        } else {
            vscode.window.showInformationMessage(message);
        }
    }

    private async applySuggestion(suggestion: any) {
        switch (suggestion.type) {
            case 'code_completion':
                await this.insertTextAtCursor(suggestion.code);
                break;
                
            case 'refactor':
                await this.applyRefactoring(suggestion.refactoring);
                break;
                
            case 'optimization':
                await this.applyOptimization(suggestion.optimization);
                break;
        }
    }

    // 命令處理方法
    public async startVoiceCommand() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            vscode.window.showErrorMessage('請先連接到 SmartUI 服務器');
            return;
        }

        if (this.isVoiceListening) {
            vscode.window.showWarningMessage('語音命令已在運行中');
            return;
        }

        this.isVoiceListening = true;
        this.statusBarItem.text = "$(mic) 聽取中...";
        
        this.sendMessage({
            type: 'start_voice_command',
            data: {
                context: this.getCurrentContext()
            }
        });

        vscode.window.showInformationMessage('語音命令已啟動，請說話...');
    }

    public async stopVoiceCommand() {
        if (!this.isVoiceListening) {
            return;
        }

        this.isVoiceListening = false;
        this.statusBarItem.text = "$(brain) SmartUI ✓";
        
        this.sendMessage({
            type: 'stop_voice_command',
            data: {}
        });

        vscode.window.showInformationMessage('語音命令已停止');
    }

    public async toggleVisualDebug() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            vscode.window.showErrorMessage('請先連接到 SmartUI 服務器');
            return;
        }

        this.sendMessage({
            type: 'toggle_visual_debug',
            data: {
                workspace: vscode.workspace.name,
                active_file: vscode.window.activeTextEditor?.document.fileName
            }
        });

        vscode.window.showInformationMessage('可視化調試模式已切換');
    }

    public async showUserAnalytics() {
        if (!this.userProfile) {
            vscode.window.showWarningMessage('用戶分析數據尚未載入');
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'smartui-analytics',
            'SmartUI 用戶分析',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.getAnalyticsWebviewContent(this.userProfile);
    }

    public async openSmartPanel() {
        const panel = vscode.window.createWebviewPanel(
            'smartui-panel',
            'SmartUI Fusion 控制面板',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.getMainPanelWebviewContent();
        
        // 處理來自 webview 的消息
        panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'startVoice':
                        this.startVoiceCommand();
                        break;
                    case 'stopVoice':
                        this.stopVoiceCommand();
                        break;
                    case 'toggleDebug':
                        this.toggleVisualDebug();
                        break;
                }
            },
            undefined,
            this.context.subscriptions
        );
    }

    // 輔助方法
    private getCurrentContext() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return {};
        }

        return {
            file_path: editor.document.fileName,
            language: editor.document.languageId,
            cursor_position: editor.selection.start,
            selected_text: editor.document.getText(editor.selection),
            workspace: vscode.workspace.name
        };
    }

    private async trackUserInteraction(type: string, data: any) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        this.sendMessage({
            type: 'user_interaction',
            data: {
                interaction_type: type,
                timestamp: Date.now(),
                context: this.getCurrentContext(),
                ...data
            }
        });
    }

    private sendMessage(message: any) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    private getUserId(): string {
        // 使用 VS Code 的機器 ID 作為用戶標識
        return vscode.env.machineId;
    }

    private async openFile(filePath: string) {
        try {
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            vscode.window.showErrorMessage(`無法打開文件: ${filePath}`);
        }
    }

    private async searchInWorkspace(query: string) {
        await vscode.commands.executeCommand('workbench.action.findInFiles', {
            query: query,
            triggerSearch: true
        });
    }

    private async insertTextAtCursor(text: string) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }

        await editor.edit(editBuilder => {
            editBuilder.insert(editor.selection.start, text);
        });
    }

    private async applyRefactoring(refactoring: any) {
        // 實現重構邏輯
        this.log(`應用重構: ${refactoring.type}`);
    }

    private async applyOptimization(optimization: any) {
        // 實現優化邏輯
        this.log(`應用優化: ${optimization.type}`);
    }

    private getMainPanelWebviewContent(): string {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SmartUI Fusion 控制面板</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                }
                .panel-section {
                    margin-bottom: 20px;
                    padding: 15px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 5px;
                }
                .button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 8px 16px;
                    margin: 5px;
                    border-radius: 3px;
                    cursor: pointer;
                }
                .button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .status {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }
                .status.connected {
                    background-color: var(--vscode-testing-iconPassed);
                    color: white;
                }
                .status.disconnected {
                    background-color: var(--vscode-testing-iconFailed);
                    color: white;
                }
            </style>
        </head>
        <body>
            <h1>🧠 SmartUI Fusion 控制面板</h1>
            
            <div class="panel-section">
                <h2>連接狀態</h2>
                <span class="status connected">已連接</span>
                <p>與 SmartUI Fusion 服務器的連接正常</p>
            </div>

            <div class="panel-section">
                <h2>🎤 語音命令</h2>
                <button class="button" onclick="startVoice()">開始語音命令</button>
                <button class="button" onclick="stopVoice()">停止語音命令</button>
                <p>使用語音控制 VS Code，支持文件操作、代碼編輯等功能</p>
            </div>

            <div class="panel-section">
                <h2>👁️ 可視化調試</h2>
                <button class="button" onclick="toggleDebug()">切換調試模式</button>
                <p>啟用智能代碼分析和可視化調試工具</p>
            </div>

            <div class="panel-section">
                <h2>📊 用戶分析</h2>
                <button class="button" onclick="showAnalytics()">查看分析報告</button>
                <p>查看您的編程習慣和效率分析</p>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function startVoice() {
                    vscode.postMessage({ command: 'startVoice' });
                }

                function stopVoice() {
                    vscode.postMessage({ command: 'stopVoice' });
                }

                function toggleDebug() {
                    vscode.postMessage({ command: 'toggleDebug' });
                }

                function showAnalytics() {
                    vscode.postMessage({ command: 'showAnalytics' });
                }
            </script>
        </body>
        </html>
        `;
    }

    private getAnalyticsWebviewContent(userProfile: UserProfile): string {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SmartUI 用戶分析</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                }
                .metric {
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 3px solid var(--vscode-textLink-foreground);
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                }
                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background-color: var(--vscode-progressBar-background);
                    border-radius: 10px;
                    overflow: hidden;
                }
                .progress-fill {
                    height: 100%;
                    background-color: var(--vscode-progressBar-foreground);
                    transition: width 0.3s ease;
                }
            </style>
        </head>
        <body>
            <h1>📊 用戶分析報告</h1>
            
            <div class="metric">
                <h3>用戶類型</h3>
                <p>${userProfile.user_type}</p>
            </div>

            <div class="metric">
                <h3>任務成功率</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${userProfile.efficiency_metrics.success_rate * 100}%"></div>
                </div>
                <p>${Math.round(userProfile.efficiency_metrics.success_rate * 100)}%</p>
            </div>

            <div class="metric">
                <h3>任務完成率</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${userProfile.efficiency_metrics.task_completion_rate * 100}%"></div>
                </div>
                <p>${Math.round(userProfile.efficiency_metrics.task_completion_rate * 100)}%</p>
            </div>

            <div class="metric">
                <h3>偏好輸入方式</h3>
                <p>${userProfile.preferred_input_methods.join(', ')}</p>
            </div>

            <div class="metric">
                <h3>平均任務時間</h3>
                <p>${Math.round(userProfile.efficiency_metrics.avg_task_duration / 1000)} 秒</p>
            </div>
        </body>
        </html>
        `;
    }

    private getDebugWebviewContent(data: any): string {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SmartUI 可視化調試</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                }
                .debug-info {
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 5px;
                }
                pre {
                    background-color: var(--vscode-textCodeBlock-background);
                    padding: 10px;
                    border-radius: 3px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <h1>🔍 可視化調試信息</h1>
            
            <div class="debug-info">
                <h3>調試數據</h3>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        </body>
        </html>
        `;
    }

    private log(message: string) {
        this.outputChannel.appendLine(`[${new Date().toISOString()}] ${message}`);
    }

    public dispose() {
        if (this.ws) {
            this.ws.close();
        }
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
    }
}

// 擴展激活函數
export function activate(context: vscode.ExtensionContext) {
    console.log('SmartUI Fusion 擴展正在激活...');

    const extension = new SmartUIFusionExtension(context);

    // 註冊命令
    const commands = [
        vscode.commands.registerCommand('smartui.startVoiceCommand', () => extension.startVoiceCommand()),
        vscode.commands.registerCommand('smartui.stopVoiceCommand', () => extension.stopVoiceCommand()),
        vscode.commands.registerCommand('smartui.toggleVisualDebug', () => extension.toggleVisualDebug()),
        vscode.commands.registerCommand('smartui.showUserAnalytics', () => extension.showUserAnalytics()),
        vscode.commands.registerCommand('smartui.openSmartPanel', () => extension.openSmartPanel())
    ];

    commands.forEach(command => context.subscriptions.push(command));
    context.subscriptions.push(extension);

    console.log('SmartUI Fusion 擴展已激活');
}

export function deactivate() {
    console.log('SmartUI Fusion 擴展正在停用...');
}

