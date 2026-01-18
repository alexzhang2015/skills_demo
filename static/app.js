// Agentic Operations - 前端应用

class SkillsApp {
    constructor() {
        this.currentSkillId = null;
        this.skills = [];
        this.currentCategory = 'all';
        this.metrics = { timeSaved: 0, systems: 0, tasks: 0 };
        this.executionStartTime = null;
        this.timerInterval = null;
        this.workflowStages = [];
        this.init();
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.loadAllData();
        console.log('Agentic Operations 平台已初始化');
    }

    async loadAllData() {
        await Promise.all([
            this.loadSkills(),
            this.loadAgents(),
            this.loadWorkflows()
        ]);
    }

    async loadAgents() {
        try {
            const response = await fetch('/api/agents');
            const data = await response.json();
            this.agents = data.agents || [];
            this.renderAgentsList();
        } catch (error) {
            console.error('加载Agents失败:', error);
        }
    }

    async loadWorkflows() {
        try {
            const response = await fetch('/api/workflows');
            const data = await response.json();
            this.workflows = data.workflows || [];
            this.renderWorkflowsList();
        } catch (error) {
            console.error('加载Workflows失败:', error);
        }
    }

    renderAgentsList() {
        const agentsList = document.getElementById('agentsList');
        if (!agentsList || !this.agents) return;

        agentsList.innerHTML = this.agents.map(agent => {
            // Handle capabilities - could be strings or objects
            const caps = (agent.capabilities || []).slice(0, 3).map(cap => {
                if (typeof cap === 'string') return cap;
                if (cap && cap.name) return cap.name;
                return '';
            }).filter(c => c);

            return `
                <div class="agent-card p-2 rounded cursor-pointer border border-transparent hover:bg-gray-100 dark:hover:bg-dark-hover transition-all" data-id="${agent.id}">
                    <div class="flex items-center gap-1.5 mb-0.5">
                        <div class="w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center">
                            <span class="text-[10px] text-white">🤖</span>
                        </div>
                        <h3 class="text-[11px] font-medium text-blue-600 dark:text-blue-400 flex-1 truncate">${agent.display_name || agent.id}</h3>
                    </div>
                    <p class="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1">${agent.description || '子场景Agent'}</p>
                    <div class="flex flex-wrap gap-0.5 mt-1">
                        ${caps.map(cap => `
                            <span class="px-1 py-0.5 text-[8px] rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">${cap}</span>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers
        agentsList.querySelectorAll('.agent-card').forEach(card => {
            card.addEventListener('click', () => this.previewAgent(card.dataset.id));
        });
    }

    renderWorkflowsList() {
        const workflowsList = document.getElementById('workflowsList');
        if (!workflowsList || !this.workflows) return;

        workflowsList.innerHTML = this.workflows.map(workflow => `
            <div class="workflow-card p-2 rounded cursor-pointer border border-transparent hover:bg-gray-100 dark:hover:bg-dark-hover transition-all" data-id="${workflow.id}">
                <div class="flex items-center gap-1.5 mb-0.5">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 flex items-center justify-center">
                        <span class="text-[10px] text-white">⚙️</span>
                    </div>
                    <h3 class="text-[11px] font-medium text-cyan-600 dark:text-cyan-400 flex-1 truncate">${workflow.name}</h3>
                    ${workflow.requires_approval ? `<span class="px-1 py-0.5 text-[8px] rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">审批</span>` : ''}
                </div>
                <p class="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1">${workflow.description || ''}</p>
                <div class="flex items-center gap-1 mt-1 text-[8px] text-gray-400">
                    <span>${(workflow.nodes || []).length} 节点</span>
                    <span>•</span>
                    <span>${(workflow.involved_skills || []).length} 技能</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        workflowsList.querySelectorAll('.workflow-card').forEach(card => {
            card.addEventListener('click', () => this.previewWorkflow(card.dataset.id));
        });
    }

    bindElements() {
        // Essential elements for 4-layer architecture
        this.naturalLanguageInput = document.getElementById('naturalLanguageInput');
        this.executionResults = document.getElementById('executionResults');
        this.executionLog = document.getElementById('executionLog');
        this.executionTimer = document.getElementById('executionTimer');
        this.timerValue = document.getElementById('timerValue');
        this.systemBadges = document.getElementById('systemBadges');
        this.skillsList = document.getElementById('skillsList');

        // Optional elements (may not exist in new template)
        this.skillForm = document.getElementById('skillForm');
        this.skillId = document.getElementById('skillId');
        this.skillName = document.getElementById('skillName');
        this.skillDesc = document.getElementById('skillDesc');
        this.skillPrompt = document.getElementById('skillPrompt');
        this.skillCategory = document.getElementById('skillCategory');
        this.requiresApproval = document.getElementById('requiresApproval');
        this.executeArgs = document.getElementById('executeArgs');
        this.skillMeta = document.getElementById('skillMeta');
    }

    bindEvents() {
        // Optional skill management buttons (may not exist in new template)
        document.getElementById('newSkillBtn')?.addEventListener('click', () => this.newSkill());
        document.getElementById('saveSkillBtn')?.addEventListener('click', () => this.saveSkill());
        document.getElementById('deleteSkillBtn')?.addEventListener('click', () => this.deleteSkill());
        document.getElementById('executeBtn')?.addEventListener('click', () => this.executeSkill());
        document.getElementById('clearResultsBtn')?.addEventListener('click', () => this.clearResults());

        // Tab switching for right panel
        document.querySelectorAll('.result-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Natural language agent execution (main functionality)
        const agentBtn = document.getElementById('agentExecuteBtn');
        if (agentBtn) {
            agentBtn.addEventListener('click', () => this.executeNaturalLanguage());
        }
        if (this.naturalLanguageInput) {
            this.naturalLanguageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.executeNaturalLanguage();
            });
        }

        // Quick examples
        document.querySelectorAll('.quick-example').forEach(btn => {
            btn.addEventListener('click', () => {
                this.naturalLanguageInput.value = btn.dataset.text;
                this.naturalLanguageInput.focus();
                this.triggerPreview(btn.dataset.text);
            });
        });

        // Real-time preview on input (with debounce)
        if (this.naturalLanguageInput) {
            const debouncedPreview = this.debounce((text) => this.fetchPreview(text), 300);
            this.naturalLanguageInput.addEventListener('input', (e) => {
                debouncedPreview(e.target.value);
            });
        }

        // Template toggle
        const toggleTemplatesBtn = document.getElementById('toggleTemplates');
        if (toggleTemplatesBtn) {
            toggleTemplatesBtn.addEventListener('click', () => this.toggleTemplates());
        }

        // Business Impact Modal
        const businessImpactBtn = document.getElementById('businessImpactBtn');
        const businessImpactModal = document.getElementById('businessImpactModal');
        const closeImpactModal = document.getElementById('closeImpactModal');

        if (businessImpactBtn && businessImpactModal) {
            businessImpactBtn.addEventListener('click', () => this.openBusinessImpactModal());
            closeImpactModal?.addEventListener('click', () => this.closeBusinessImpactModal());
            businessImpactModal.addEventListener('click', (e) => {
                if (e.target === businessImpactModal) this.closeBusinessImpactModal();
            });
        }

        // Tech Documentation PDF
        const techPptBtn = document.getElementById('techPptBtn');
        const techPptModal = document.getElementById('techPptModal');
        const closePptModal = document.getElementById('closePptModal');
        const pptPrevBtn = document.getElementById('pptPrevBtn');
        const pptNextBtn = document.getElementById('pptNextBtn');

        if (techPptBtn) {
            techPptBtn.addEventListener('click', () => {
                window.open('/static/Agentic_Operations_Skills_Platform.pdf', '_blank');
            });
        }

        // Video Tutorial Button
        const videoBtn = document.getElementById('videoBtn');
        if (videoBtn) {
            videoBtn.addEventListener('click', () => {
                window.open('/static/智能体运营：将手动流程转变为自动化技能.mp4', '_blank');
            });
        }

        // Keep modal handlers for potential future use
        if (techPptModal) {
            closePptModal?.addEventListener('click', () => this.closeTechPptModal());
            techPptModal.addEventListener('click', (e) => {
                if (e.target === techPptModal) this.closeTechPptModal();
            });
            pptPrevBtn?.addEventListener('click', () => this.pptPrevSlide());
            pptNextBtn?.addEventListener('click', () => this.pptNextSlide());
            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (!techPptModal.classList.contains('hidden')) {
                    if (e.key === 'ArrowLeft') this.pptPrevSlide();
                    if (e.key === 'ArrowRight') this.pptNextSlide();
                    if (e.key === 'Escape') this.closeTechPptModal();
                }
            });
        }

        // Scenario templates
        document.querySelectorAll('.scenario-template').forEach(btn => {
            btn.addEventListener('click', () => {
                this.naturalLanguageInput.value = btn.dataset.text;
                this.naturalLanguageInput.focus();
                this.triggerPreview(btn.dataset.text);
            });
        });

        // Category filter
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentCategory = btn.dataset.category;
                this.renderSkillsList();
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('ring-2', 'ring-purple-500'));
                btn.classList.add('ring-2', 'ring-purple-500');
            });
        });

        // Panel tab switching (Agents, Workflows, Skills)
        document.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchPanelTab(tab.dataset.panel));
        });

        // Optional: executeArgs keypress (may not exist)
        this.executeArgs?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.executeSkill();
        });
    }

    // Tab switching for right panel
    switchTab(tabName) {
        document.querySelectorAll('.result-tab').forEach(tab => {
            if (tab.dataset.tab === tabName) {
                tab.classList.add('text-purple-600', 'dark:text-purple-400', 'border-b-2', 'border-purple-500', 'font-medium');
                tab.classList.remove('text-gray-500', 'dark:text-gray-400');
            } else {
                tab.classList.remove('text-purple-600', 'dark:text-purple-400', 'border-b-2', 'border-purple-500', 'font-medium');
                tab.classList.add('text-gray-500', 'dark:text-gray-400');
            }
        });
        document.getElementById('executionTab')?.classList.toggle('hidden', tabName !== 'execution');
        document.getElementById('logTab')?.classList.toggle('hidden', tabName !== 'log');
    }

    // Tab switching for left panel (Agents, Workflows, Skills)
    switchPanelTab(panelName) {
        document.querySelectorAll('.panel-tab').forEach(tab => {
            if (tab.dataset.panel === panelName) {
                tab.classList.add('text-purple-600', 'dark:text-purple-400', 'border-b-2', 'border-purple-500', 'font-medium');
                tab.classList.remove('text-gray-500', 'dark:text-gray-400');
            } else {
                tab.classList.remove('text-purple-600', 'dark:text-purple-400', 'border-b-2', 'border-purple-500', 'font-medium');
                tab.classList.add('text-gray-500', 'dark:text-gray-400');
            }
        });
        document.getElementById('agentsPanel')?.classList.toggle('hidden', panelName !== 'agents');
        document.getElementById('workflowsPanel')?.classList.toggle('hidden', panelName !== 'workflows');
        document.getElementById('skillsPanel')?.classList.toggle('hidden', panelName !== 'skills');
    }

    // Execution timer
    startTimer() {
        this.executionStartTime = Date.now();
        this.executionTimer.classList.remove('hidden');
        this.timerInterval = setInterval(() => {
            const elapsed = (Date.now() - this.executionStartTime) / 1000;
            this.timerValue.textContent = elapsed.toFixed(1) + 's';
        }, 100);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // Debounce utility
    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Trigger preview immediately (for template/example clicks)
    triggerPreview(text) {
        this.fetchPreview(text);
    }

    // Fetch preview from API
    async fetchPreview(text) {
        const previewHint = document.getElementById('previewHint');
        const quickPreviewHint = document.getElementById('quickPreviewHint');

        if (!text || !text.trim()) {
            this.hidePreviewHint();
            return;
        }

        // Show loading state
        if (quickPreviewHint) {
            quickPreviewHint.classList.remove('hidden');
            document.getElementById('quickPreviewText').textContent = '分析中...';
        }

        try {
            const response = await fetch('/api/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: text })
            });
            const preview = await response.json();
            this.showPreviewHint(preview);
        } catch (error) {
            console.error('预览失败:', error);
            this.hidePreviewHint();
        } finally {
            if (quickPreviewHint) {
                quickPreviewHint.classList.add('hidden');
            }
        }
    }

    // Show preview hint with impact data
    showPreviewHint(preview) {
        const previewHint = document.getElementById('previewHint');
        if (!previewHint) return;

        const impact = preview.estimated_impact || {};
        const entities = preview.entities || {};

        // Update statistics
        document.getElementById('previewStores').textContent = impact.affected_stores || '-';
        document.getElementById('previewSkus').textContent = impact.affected_skus || '-';
        document.getElementById('previewSystems').textContent = (impact.affected_systems || []).length || '-';
        document.getElementById('previewDuration').textContent = impact.estimated_duration || '-';

        // Update complexity badge
        const complexityEl = document.getElementById('previewComplexity');
        if (complexityEl) {
            const confidence = Math.round((preview.confidence || 0) * 100);
            complexityEl.textContent = `${preview.intent || '未知'} (${confidence}%)`;
        }

        // Update details section
        const detailsEl = document.getElementById('previewDetails');
        if (detailsEl) {
            let detailsHtml = '';

            // Show region
            if (impact.region) {
                detailsHtml += `<div><span class="text-gray-400">区域:</span> ${impact.region}</div>`;
            }

            // Show affected systems as badges
            if (impact.affected_systems && impact.affected_systems.length > 0) {
                detailsHtml += `<div class="flex flex-wrap gap-1 mt-1">`;
                impact.affected_systems.forEach(sys => {
                    const colors = {
                        'POS': 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
                        'APP': 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
                        'MENU_BOARD': 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
                        'INVENTORY': 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
                        'PRICING': 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
                        'CRM': 'bg-pink-100 text-pink-600 dark:bg-pink-900/30 dark:text-pink-400',
                        'MARKETING': 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
                    };
                    const colorClass = colors[sys] || 'bg-gray-100 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400';
                    detailsHtml += `<span class="px-1.5 py-0.5 text-[10px] rounded ${colorClass}">${sys}</span>`;
                });
                detailsHtml += `</div>`;
            }

            // Show approval requirement
            if (impact.requires_approval) {
                detailsHtml += `<div class="mt-1 flex items-center gap-1 text-amber-600 dark:text-amber-400">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                    <span>需要审批: ${(impact.approval_roles || []).join(', ') || '运营总监'}</span>
                </div>`;
            }

            // Show execution steps preview
            if (preview.execution_steps && preview.execution_steps.length > 0) {
                detailsHtml += `<div class="mt-2 pt-2 border-t border-gray-200 dark:border-dark-border">
                    <div class="text-[10px] text-gray-400 mb-1">执行步骤预览:</div>
                    <div class="space-y-0.5">`;
                preview.execution_steps.slice(0, 4).forEach((step, idx) => {
                    detailsHtml += `<div class="flex items-center gap-1 text-[10px]">
                        <span class="w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-500">${idx + 1}</span>
                        <span class="flex-1">${step.name}</span>
                        <span class="text-gray-400">${step.system}</span>
                    </div>`;
                });
                if (preview.execution_steps.length > 4) {
                    detailsHtml += `<div class="text-[10px] text-gray-400">+${preview.execution_steps.length - 4} 更多步骤...</div>`;
                }
                detailsHtml += `</div></div>`;
            }

            detailsEl.innerHTML = detailsHtml;
        }

        // Show the preview hint
        previewHint.classList.remove('hidden');
    }

    // Hide preview hint
    hidePreviewHint() {
        const previewHint = document.getElementById('previewHint');
        if (previewHint) {
            previewHint.classList.add('hidden');
        }
    }

    // Toggle templates container
    toggleTemplates() {
        const container = document.getElementById('templatesContainer');
        const toggleText = document.getElementById('toggleTemplatesText');
        const toggleIcon = document.getElementById('toggleTemplatesIcon');

        if (container) {
            const isHidden = container.classList.contains('hidden');
            container.classList.toggle('hidden');

            if (toggleText) {
                toggleText.textContent = isHidden ? '收起' : '展开';
            }
            if (toggleIcon) {
                toggleIcon.style.transform = isHidden ? 'rotate(180deg)' : '';
            }
        }
    }

    // Execution log
    addLog(message, type = 'info') {
        const colors = {
            info: 'text-gray-300',
            success: 'text-green-400',
            warning: 'text-yellow-400',
            error: 'text-red-400',
            system: 'text-cyan-400',
            api: 'text-purple-400'
        };
        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${colors[type] || colors.info}`;
        logEntry.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${message}`;
        this.executionLog.appendChild(logEntry);
        this.executionLog.scrollTop = this.executionLog.scrollHeight;
    }

    clearLog() {
        this.executionLog.innerHTML = `
            <div class="text-gray-500"># Agent执行日志</div>
            <div class="text-gray-500"># 等待执行命令...</div>
        `;
    }

    async loadSkills() {
        try {
            const response = await fetch('/api/skills');
            const data = await response.json();
            this.skills = data.skills;
            this.renderSkillsList();
            if (this.skills.length > 0 && !this.currentSkillId) {
                this.selectSkill(this.skills[0].id);
            }
        } catch (error) {
            console.error('加载Skills失败:', error);
        }
    }

    // Natural language to skill matching
    matchSkillFromText(text) {
        const lowerText = text.toLowerCase();
        const keywords = {
            'menu-config': ['菜品', '菜单', '新增', '上架', '下架', '添加菜'],
            'price-adjust': ['涨价', '降价', '价格', '调价', '定价'],
            'product-launch': ['上市', '新品', '发布', '推出', '首发'],
            'campaign-setup': ['活动', '促销', '满减', '优惠', '打折', '折扣'],
            'store-audit': ['巡检', '检查', '合规', '审核', '门店检查'],
            'report-gen': ['报告', '报表', '周报', '月报', '分析', '统计']
        };

        for (const [skillName, kws] of Object.entries(keywords)) {
            if (kws.some(kw => lowerText.includes(kw))) {
                return this.skills.find(s => s.name === skillName);
            }
        }
        return this.skills[0]; // Default to first skill
    }

    async executeNaturalLanguage() {
        const text = this.naturalLanguageInput.value.trim();
        if (!text) {
            alert('请输入您想要执行的操作');
            return;
        }

        // Hide preview hint when starting execution
        this.hidePreviewHint();

        // Start timer and clear log
        this.startTimer();
        this.clearLog();
        this.addLog('Master Agent 开始处理请求', 'info');
        this.addLog(`输入: "${text}"`, 'info');

        // Show workflow timeline
        this.showWorkflowTimeline(text);

        // Update workflow stage: Intent Recognition
        await this.sleep(300);
        this.updateWorkflowStage('intent', 'processing');
        this.addLog('正在分析用户意图...', 'system');

        try {
            // Call the new 4-layer API
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: text })
            });

            const session = await response.json();
            this.addLog(`会话ID: ${session.session_id}`, 'info');

            // Update intent stage
            this.updateWorkflowStage('intent', 'complete');
            if (session.intent_analysis) {
                this.addLog(`意图识别: ${session.intent_analysis.intent_type} (置信度: ${(session.intent_analysis.confidence * 100).toFixed(0)}%)`, 'success');
            }

            // Update match stage
            this.updateWorkflowStage('match', 'processing');
            await this.sleep(300);
            this.updateWorkflowStage('match', 'complete');

            // Show session result
            await this.showSessionResult(session);

        } catch (error) {
            console.error('执行失败:', error);
            this.addLog(`执行失败: ${error.message}`, 'error');
            this.updateWorkflowStage('intent', 'error', '失败');
            this.stopTimer();
        }
    }

    async showSessionResult(session) {
        // Update session detail panel
        this.updateSessionDetail(session);

        // Update right panel layer execution
        this.updateLayerExecution(session);

        // Update execute stage
        this.updateWorkflowStage('execute', 'processing');
        this.addLog('执行子Agent任务...', 'system');

        // Display agent tasks
        if (session.agent_tasks && session.agent_tasks.length > 0) {
            for (const task of session.agent_tasks) {
                await this.sleep(200);
                this.addLog(`  ↳ ${task.agent_name}: ${task.status}`, 'api');

                // Show workflow executions if any
                if (task.workflow_executions) {
                    for (const wf of task.workflow_executions) {
                        this.addLog(`    → 工作流: ${wf.workflow_name}`, 'api');

                        // Show skill executions with MCP calls
                        if (wf.node_executions) {
                            for (const node of wf.node_executions) {
                                if (node.skill_execution) {
                                    const skill = node.skill_execution;
                                    const mcpCount = skill.tool_calls ? skill.tool_calls.length : 0;
                                    if (mcpCount > 0) {
                                        this.addLog(`      ⚡ ${skill.skill_name} → ${mcpCount}个MCP调用`, 'system');
                                        // Show first few MCP tool calls
                                        skill.tool_calls.slice(0, 2).forEach(call => {
                                            this.addLog(`        🔌 ${call.system}.${call.operation}`, 'api');
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        this.updateWorkflowStage('execute', 'complete');

        // Update systems stage
        this.updateWorkflowStage('systems', 'processing');
        await this.sleep(300);
        this.updateWorkflowStage('systems', 'complete');

        // Create result card
        const resultCard = document.createElement('div');
        resultCard.className = 'animate-slideIn bg-white dark:bg-dark-card rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden mt-2';

        const statusColor = session.status === 'success' ? 'green' :
                           session.status === 'awaiting_approval' ? 'amber' : 'blue';

        resultCard.innerHTML = `
            <div class="px-3 py-2 bg-gradient-to-r from-${statusColor}-50 to-emerald-50 dark:from-${statusColor}-900/20 dark:to-emerald-900/20 border-b border-gray-200 dark:border-dark-border">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-medium">会话结果</span>
                        <span class="text-[10px] text-gray-400">${session.session_id}</span>
                    </div>
                    <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-${statusColor}-100 dark:bg-${statusColor}-900/30 text-${statusColor}-600 dark:text-${statusColor}-400">
                        ${session.status === 'success' ? '执行成功' : session.status === 'awaiting_approval' ? '等待审批' : session.status}
                    </span>
                </div>
            </div>
            <div class="p-3 space-y-2">
                ${session.intent_analysis ? `
                <div class="text-xs">
                    <span class="text-gray-500">意图:</span>
                    <span class="ml-1 font-medium">${session.intent_analysis.intent_type}</span>
                    <span class="text-gray-400 ml-2">(${(session.intent_analysis.confidence * 100).toFixed(0)}%)</span>
                </div>
                ` : ''}
                ${session.agent_tasks && session.agent_tasks.length > 0 ? `
                <div class="text-xs">
                    <span class="text-gray-500">调用Agent:</span>
                    <span class="ml-1">${session.agent_tasks.map(t => t.agent_name).join(', ')}</span>
                </div>
                ` : ''}
                ${session.final_result ? `
                <div class="mt-2 p-2 bg-gray-50 dark:bg-dark-hover rounded text-xs font-mono whitespace-pre-wrap max-h-40 overflow-auto">
                    ${this.escapeHtml(session.final_result)}
                </div>
                ` : ''}
            </div>
        `;

        const workflowTimeline = document.getElementById('workflow-timeline');
        if (workflowTimeline) {
            workflowTimeline.after(resultCard);
        } else {
            this.executionResults.insertBefore(resultCard, this.executionResults.firstChild);
        }

        // Update completion stage
        if (session.status === 'awaiting_approval') {
            this.updateWorkflowStage('complete', 'processing', '等待审批');
            this.addLog('执行完成，等待人工审批', 'warning');
            this.updateWorkflowStatus('awaiting_approval');
        } else {
            this.updateWorkflowStage('complete', 'complete', '执行成功');
            this.addLog('执行成功完成!', 'success');
            this.updateWorkflowStatus('complete');
        }

        // Stop timer
        this.stopTimer();
        const elapsed = ((Date.now() - this.executionStartTime) / 1000).toFixed(2);
        this.addLog(`总耗时: ${elapsed}s`, 'info');

        // Update metrics
        this.updateSessionMetrics(session);
    }

    updateSessionMetrics(session) {
        // Update agent count
        const agentCount = session.agent_tasks ? session.agent_tasks.length : 0;
        document.getElementById('metricAgents').textContent =
            parseInt(document.getElementById('metricAgents').textContent || '0') + agentCount;

        // Update workflow count
        let workflowCount = 0;
        if (session.agent_tasks) {
            session.agent_tasks.forEach(task => {
                if (task.workflow_executions) {
                    workflowCount += task.workflow_executions.length;
                }
            });
        }
        document.getElementById('metricWorkflows').textContent =
            parseInt(document.getElementById('metricWorkflows').textContent || '0') + workflowCount;

        // Update time saved
        const timeSaved = agentCount * 2; // 2 hours per agent
        document.getElementById('metricTimeSaved').textContent =
            parseInt(document.getElementById('metricTimeSaved').textContent || '0') + timeSaved;
    }

    updateSessionDetail(session) {
        const sessionContent = document.getElementById('sessionContent');
        if (!sessionContent) return;

        const intent = session.intent_analysis || {};
        const entities = intent.entities || {};
        const agentTasks = session.agent_tasks || [];

        const statusColor = session.status === 'success' ? 'green' :
                           session.status === 'awaiting_approval' ? 'amber' : 'blue';
        const statusText = session.status === 'success' ? '执行成功' :
                          session.status === 'awaiting_approval' ? '等待审批' : session.status;

        sessionContent.innerHTML = `
            <div class="space-y-3">
                <!-- Session Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                        </div>
                        <span class="text-xs font-medium">会话 ${session.session_id}</span>
                    </div>
                    <span id="sessionStatusBadge" class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-${statusColor}-100 dark:bg-${statusColor}-900/30 text-${statusColor}-600 dark:text-${statusColor}-400">
                        ${statusText}
                    </span>
                </div>

                <!-- User Input -->
                <div class="bg-gray-50 dark:bg-dark-hover rounded-lg p-2">
                    <div class="text-[10px] text-gray-500 mb-1">用户输入</div>
                    <div class="text-xs font-medium">${this.escapeHtml(session.original_input || '')}</div>
                </div>

                <!-- Intent Analysis -->
                <div class="grid grid-cols-2 gap-2">
                    <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-2">
                        <div class="text-[10px] text-purple-600 dark:text-purple-400 mb-1">识别意图</div>
                        <div class="text-xs font-medium text-purple-700 dark:text-purple-300">${intent.intent_type || '未知'}</div>
                        <div class="text-[10px] text-gray-500 mt-0.5">置信度: ${((intent.confidence || 0) * 100).toFixed(0)}%</div>
                    </div>
                    <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2">
                        <div class="text-[10px] text-blue-600 dark:text-blue-400 mb-1">路由Agent</div>
                        <div class="text-xs font-medium text-blue-700 dark:text-blue-300">${agentTasks.length > 0 ? agentTasks[0].agent_name : '-'}</div>
                        <div class="text-[10px] text-gray-500 mt-0.5">共 ${agentTasks.length} 个Agent</div>
                    </div>
                </div>

                <!-- Extracted Entities -->
                ${Object.keys(entities).length > 0 ? `
                <div class="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-2">
                    <div class="text-[10px] text-amber-600 dark:text-amber-400 mb-1">提取实体</div>
                    <div class="flex flex-wrap gap-1">
                        ${Object.entries(entities).map(([key, value]) => `
                            <span class="px-1.5 py-0.5 text-[10px] rounded bg-white dark:bg-dark-bg border border-amber-200 dark:border-amber-800">
                                <span class="text-gray-500">${key}:</span>
                                <span class="font-medium text-amber-700 dark:text-amber-300">${value}</span>
                            </span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Execution Summary -->
                ${session.final_result ? `
                <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-2">
                    <div class="text-[10px] text-green-600 dark:text-green-400 mb-1">执行结果摘要</div>
                    <div class="text-[10px] text-gray-600 dark:text-gray-400 max-h-20 overflow-y-auto">
                        ${this.escapeHtml(session.final_result).substring(0, 200)}${session.final_result.length > 200 ? '...' : ''}
                    </div>
                </div>
                ` : ''}

                <!-- Approval Actions -->
                ${session.status === 'awaiting_approval' ? `
                <div class="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 border border-amber-200 dark:border-amber-800">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                            </svg>
                            <span class="text-xs font-medium text-amber-700 dark:text-amber-400">需要人工审批</span>
                        </div>
                        <span class="text-[10px] text-gray-500">审批人: 运营总监</span>
                    </div>
                    <div class="text-[10px] text-gray-600 dark:text-gray-400 mb-3">
                        此操作涉及关键业务变更，需要获得授权后才能生效。
                    </div>
                    <div class="flex gap-2">
                        <button onclick="window.app.approveSession('${session.session_id}', true)"
                            class="flex-1 px-3 py-1.5 text-xs font-medium bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors flex items-center justify-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                            批准执行
                        </button>
                        <button onclick="window.app.approveSession('${session.session_id}', false)"
                            class="flex-1 px-3 py-1.5 text-xs font-medium bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors flex items-center justify-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                            拒绝
                        </button>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    updateLayerExecution(session) {
        const layerExecution = document.getElementById('layerExecution');
        if (!layerExecution) return;

        const intentAnalysis = session.intent_analysis || {};
        const agentTasks = session.agent_tasks || [];

        // Build layer cards
        let html = `
            <!-- Layer 1: Master Agent -->
            <div class="mb-2 p-2 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                        <span class="text-[10px] text-white">1</span>
                    </div>
                    <span class="text-xs font-medium text-purple-700 dark:text-purple-400">Master Agent</span>
                    <span class="ml-auto px-1.5 py-0.5 text-[8px] rounded-full bg-green-100 dark:bg-green-900/30 text-green-600">✓ 完成</span>
                </div>
                <div class="ml-7 text-[10px] text-gray-600 dark:text-gray-400 space-y-0.5">
                    <div>意图: <span class="font-medium">${intentAnalysis.intent_type || '未知'}</span> (${((intentAnalysis.confidence || 0) * 100).toFixed(0)}%)</div>
                    ${intentAnalysis.entities ? `<div>实体: ${Object.entries(intentAnalysis.entities).map(([k,v]) => `${k}=${v}`).join(', ')}</div>` : ''}
                </div>
            </div>

            <!-- Layer 2: Sub Agents -->
            <div class="mb-2 p-2 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center">
                        <span class="text-[10px] text-white">2</span>
                    </div>
                    <span class="text-xs font-medium text-blue-700 dark:text-blue-400">子场景Agent</span>
                    <span class="ml-auto px-1.5 py-0.5 text-[8px] rounded-full bg-green-100 dark:bg-green-900/30 text-green-600">✓ ${agentTasks.length}个</span>
                </div>
                <div class="ml-7 space-y-1">
                    ${agentTasks.map(task => `
                        <div class="text-[10px] flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            <span class="font-medium text-gray-700 dark:text-gray-300">${task.agent_name}</span>
                            <span class="text-gray-400">${task.status}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Layer 3: Workflows
        let totalWorkflows = 0;
        let workflowDetails = [];
        agentTasks.forEach(task => {
            if (task.workflow_executions) {
                task.workflow_executions.forEach(wf => {
                    totalWorkflows++;
                    workflowDetails.push(wf);
                });
            }
        });

        html += `
            <!-- Layer 3: Workflows -->
            <div class="mb-2 p-2 rounded-lg bg-gradient-to-r from-cyan-50 to-teal-50 dark:from-cyan-900/20 dark:to-teal-900/20 border border-cyan-200 dark:border-cyan-800">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 flex items-center justify-center">
                        <span class="text-[10px] text-white">3</span>
                    </div>
                    <span class="text-xs font-medium text-cyan-700 dark:text-cyan-400">Workflow编排</span>
                    <span class="ml-auto px-1.5 py-0.5 text-[8px] rounded-full bg-green-100 dark:bg-green-900/30 text-green-600">✓ ${totalWorkflows}个</span>
                </div>
                <div class="ml-7 space-y-1">
                    ${workflowDetails.map(wf => `
                        <div class="text-[10px] flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            <span class="font-medium text-gray-700 dark:text-gray-300">${wf.workflow_name || wf.workflow_id}</span>
                            <span class="text-gray-400">${(wf.node_executions || []).length}节点</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Layer 4: Skills
        let totalSkills = 0;
        let skillDetails = [];
        workflowDetails.forEach(wf => {
            if (wf.node_executions) {
                wf.node_executions.forEach(node => {
                    if (node.skill_execution) {
                        totalSkills++;
                        skillDetails.push(node.skill_execution);
                    }
                });
            }
        });

        // Collect MCP tool calls from skill executions
        let totalMCPCalls = 0;
        let mcpCallDetails = [];
        skillDetails.forEach(skill => {
            if (skill.tool_calls && skill.tool_calls.length > 0) {
                skill.tool_calls.forEach(call => {
                    totalMCPCalls++;
                    mcpCallDetails.push({
                        ...call,
                        skill_name: skill.skill_name,
                        trace_id: skill.trace_id
                    });
                });
            }
        });

        html += `
            <!-- Layer 4: Skills -->
            <div class="mb-2 p-2 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                        <span class="text-[10px] text-white">4</span>
                    </div>
                    <span class="text-xs font-medium text-green-700 dark:text-green-400">Skills执行</span>
                    <span class="ml-auto px-1.5 py-0.5 text-[8px] rounded-full bg-green-100 dark:bg-green-900/30 text-green-600">✓ ${totalSkills}个</span>
                </div>
                <div class="ml-7 space-y-1">
                    ${skillDetails.slice(0, 5).map(skill => `
                        <div class="text-[10px] flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            <span class="font-medium text-gray-700 dark:text-gray-300">${skill.skill_name || skill.skill_id}</span>
                            <span class="text-gray-400">${skill.status}</span>
                            ${skill.tool_calls && skill.tool_calls.length > 0 ? `<span class="text-purple-500">(${skill.tool_calls.length} MCP)</span>` : ''}
                        </div>
                    `).join('')}
                    ${skillDetails.length > 5 ? `<div class="text-[10px] text-gray-400">+${skillDetails.length - 5} 更多...</div>` : ''}
                </div>
            </div>

            <!-- MCP Layer: Tool Calls -->
            <div class="p-2 rounded-lg bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20 border border-purple-200 dark:border-purple-800">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-5 h-5 rounded-full bg-gradient-to-r from-purple-500 to-violet-500 flex items-center justify-center">
                        <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                    </div>
                    <span class="text-xs font-medium text-purple-700 dark:text-purple-400">MCP调用</span>
                    <span class="ml-auto px-1.5 py-0.5 text-[8px] rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600">✓ ${totalMCPCalls}次</span>
                </div>
                <div class="ml-7 space-y-1">
                    ${mcpCallDetails.slice(0, 6).map(call => `
                        <div class="text-[10px] flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full ${call.status === 'success' ? 'bg-green-500' : 'bg-red-500'}"></span>
                            <span class="font-medium text-gray-700 dark:text-gray-300">${call.system}</span>
                            <span class="text-purple-500">${call.operation}</span>
                            ${call.duration_ms ? `<span class="text-gray-400">${call.duration_ms.toFixed(0)}ms</span>` : ''}
                        </div>
                    `).join('')}
                    ${mcpCallDetails.length > 6 ? `<div class="text-[10px] text-gray-400">+${mcpCallDetails.length - 6} 更多...</div>` : ''}
                    ${mcpCallDetails.length === 0 ? `<div class="text-[10px] text-gray-400">暂无MCP调用</div>` : ''}
                </div>
            </div>
        `;

        layerExecution.innerHTML = html;
    }

    showWorkflowTimeline(text) {
        this.removePlaceholder();

        // Create workflow timeline container
        const timelineCard = document.createElement('div');
        timelineCard.id = 'workflow-timeline';
        timelineCard.className = 'animate-slideIn bg-white dark:bg-dark-card rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden';

        timelineCard.innerHTML = `
            <div class="px-3 py-2 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-b border-gray-200 dark:border-dark-border">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-5 h-5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                        </div>
                        <span class="text-xs font-medium text-gray-700 dark:text-gray-300">Workflow 执行流程</span>
                    </div>
                    <span id="workflowStatus" class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 animate-pulse">
                        执行中
                    </span>
                </div>
            </div>
            <div class="p-3">
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mb-2 truncate">
                    <span class="text-gray-400">输入:</span> "${this.escapeHtml(text.substring(0, 50))}${text.length > 50 ? '...' : ''}"
                </div>
                <div id="workflowStages" class="relative space-y-2">
                    <!-- Workflow stages will be added here -->
                </div>
            </div>
        `;

        this.executionResults.insertBefore(timelineCard, this.executionResults.firstChild);

        // Initialize workflow stages
        this.initWorkflowStages();

        // Animate architecture flow
        this.startArchitectureFlow();
    }

    initWorkflowStages() {
        const stages = [
            { id: 'intent', label: '意图识别', icon: '🧠', desc: '分析自然语言输入' },
            { id: 'match', label: 'Skill匹配', icon: '🔍', desc: '匹配最佳执行模板' },
            { id: 'execute', label: '执行步骤', icon: '⚡', desc: '执行业务逻辑' },
            { id: 'systems', label: '系统调用', icon: '🔗', desc: '调用后端API' },
            { id: 'complete', label: '执行完成', icon: '✅', desc: '返回执行结果' }
        ];

        const stagesContainer = document.getElementById('workflowStages');
        stagesContainer.innerHTML = stages.map((stage, index) => `
            <div id="stage-${stage.id}" class="workflow-stage flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-dark-hover transition-all duration-300" data-status="pending">
                <div class="stage-icon w-6 h-6 rounded-full bg-gray-200 dark:bg-dark-border flex items-center justify-center text-xs transition-all duration-300">
                    ${stage.icon}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-medium text-gray-600 dark:text-gray-400">${stage.label}</span>
                        <span class="stage-status text-[10px] text-gray-400">等待中</span>
                    </div>
                    <div class="stage-progress h-1 mt-1 rounded-full bg-gray-200 dark:bg-dark-border overflow-hidden">
                        <div class="stage-bar h-full w-0 bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"></div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateWorkflowStage(stageId, status, detail = '') {
        const stage = document.getElementById(`stage-${stageId}`);
        if (!stage) return;

        const iconEl = stage.querySelector('.stage-icon');
        const statusEl = stage.querySelector('.stage-status');
        const barEl = stage.querySelector('.stage-bar');

        if (status === 'processing') {
            stage.classList.add('bg-purple-50', 'dark:bg-purple-900/20');
            stage.classList.remove('bg-gray-50', 'dark:bg-dark-hover');
            iconEl.classList.add('animate-pulse', 'bg-purple-500', 'text-white');
            iconEl.classList.remove('bg-gray-200', 'dark:bg-dark-border');
            statusEl.textContent = detail || '处理中...';
            statusEl.classList.add('text-purple-500');
            barEl.style.width = '50%';
        } else if (status === 'complete') {
            stage.classList.add('bg-green-50', 'dark:bg-green-900/20');
            stage.classList.remove('bg-purple-50', 'dark:bg-purple-900/20', 'bg-gray-50', 'dark:bg-dark-hover');
            iconEl.classList.remove('animate-pulse', 'bg-purple-500');
            iconEl.classList.add('bg-green-500', 'text-white');
            statusEl.textContent = detail || '完成';
            statusEl.classList.remove('text-purple-500');
            statusEl.classList.add('text-green-500');
            barEl.style.width = '100%';
            barEl.classList.remove('from-purple-500', 'to-pink-500');
            barEl.classList.add('from-green-500', 'to-emerald-500');
        } else if (status === 'error') {
            stage.classList.add('bg-red-50', 'dark:bg-red-900/20');
            iconEl.classList.add('bg-red-500', 'text-white');
            statusEl.textContent = detail || '失败';
            statusEl.classList.add('text-red-500');
        }
    }

    showAgentThinking(text) {
        // This is now replaced by showWorkflowTimeline
        // Keeping for backward compatibility
    }

    showSkillMatched(skill, text) {
        const thinkingCard = document.getElementById('thinking-card');
        if (thinkingCard) {
            const catInfo = this.getCategoryInfo(skill.category);
            thinkingCard.innerHTML = `
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                        <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <span class="text-xs font-medium text-purple-700 dark:text-purple-400">意图识别完成</span>
                </div>
                <div class="flex items-center gap-2 text-[10px]">
                    <span class="text-gray-500">匹配Skill:</span>
                    <span class="px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 font-medium">
                        ${catInfo.icon} ${skill.name}
                    </span>
                    <span class="text-gray-400">→ ${skill.description.substring(0, 30)}...</span>
                </div>
            `;

            // Show active skill badge
            const badge = document.getElementById('activeSkillBadge');
            badge.classList.remove('hidden');
            badge.querySelector('span').textContent = skill.name;
        }
    }

    startArchitectureFlow() {
        // Show flow arrows between layers
        document.getElementById('flowArrow1')?.classList.remove('hidden');
        document.getElementById('flowArrow2')?.classList.remove('hidden');
        document.getElementById('flowArrow3')?.classList.remove('hidden');

        // Highlight 4 layers in sequence
        const layers = ['layer1', 'layer2', 'layer3', 'layer4'];
        layers.forEach((id, i) => {
            setTimeout(() => {
                document.getElementById(id)?.classList.add('ring-2', 'ring-purple-500', 'shadow-lg');
            }, i * 300);
        });
    }

    stopArchitectureFlow() {
        // Hide flow arrows
        document.getElementById('flowArrow1')?.classList.add('hidden');
        document.getElementById('flowArrow2')?.classList.add('hidden');
        document.getElementById('flowArrow3')?.classList.add('hidden');

        // Remove highlights from all layers
        ['layer1', 'layer2', 'layer3', 'layer4'].forEach(id => {
            document.getElementById(id)?.classList.remove('ring-2', 'ring-purple-500', 'shadow-lg');
        });
        document.getElementById('activeAgentBadge')?.classList.add('hidden');
    }

    async executeSkillWithStreaming(skillId, args) {
        const skill = this.skills.find(s => s.id === skillId);
        if (!skill) return;

        // Update workflow stage
        this.updateWorkflowStage('execute', 'processing');
        this.addLog(`开始执行 Skill: ${skill.name}`, 'system');

        // Create streaming result card
        const streamCard = document.createElement('div');
        streamCard.id = 'stream-card';
        streamCard.className = 'animate-slideIn bg-white dark:bg-dark-card rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden mt-2';

        const catInfo = this.getCategoryInfo(skill.category);

        streamCard.innerHTML = `
            <div class="flex justify-between items-center px-3 py-2 border-b border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-hover">
                <div class="flex items-center gap-2">
                    <span class="text-sm">${catInfo.icon}</span>
                    <h4 class="font-medium text-xs">${skill.name}</h4>
                    <span class="text-[10px] text-gray-400">执行详情</span>
                </div>
                <span id="streamStatus" class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 animate-pulse">
                    执行中...
                </span>
            </div>
            <div class="px-3 py-2 border-b border-gray-200 dark:border-dark-border bg-gray-50/50 dark:bg-dark-hover/50">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-[10px] text-gray-500">涉及系统</span>
                    <span id="systemProgress" class="text-[10px] text-gray-400">0/${(skill.affected_systems || []).length}</span>
                </div>
                <div class="flex flex-wrap gap-1" id="streamSystems"></div>
            </div>
            <div class="px-3 py-2 border-b border-gray-200 dark:border-dark-border">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-[10px] text-gray-500">执行进度</span>
                    <span id="stepProgress" class="text-[10px] text-gray-400">准备中...</span>
                </div>
                <div class="h-1.5 rounded-full bg-gray-200 dark:bg-dark-border overflow-hidden">
                    <div id="progressBar" class="h-full w-0 bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"></div>
                </div>
            </div>
            <div id="streamSteps" class="p-3 space-y-2 max-h-60 overflow-y-auto"></div>
            <div id="streamResult" class="hidden"></div>
        `;

        // Insert after workflow timeline
        const workflowTimeline = document.getElementById('workflow-timeline');
        if (workflowTimeline) {
            workflowTimeline.after(streamCard);
        } else {
            this.executionResults.insertBefore(streamCard, this.executionResults.firstChild);
        }

        // Activate system badges
        this.activateSystemBadges(skill.affected_systems || []);

        // Show affected systems in stream card
        const streamSystems = document.getElementById('streamSystems');
        (skill.affected_systems || []).forEach(sys => {
            const sysEl = document.createElement('span');
            sysEl.className = 'inline-flex items-center px-1.5 py-0.5 text-[10px] rounded bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 transition-all duration-300';
            sysEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-yellow-500 mr-1 animate-pulse"></span>${this.getSystemName(sys)}`;
            sysEl.dataset.system = sys;
            streamSystems.appendChild(sysEl);
        });

        // Update workflow stage for systems
        this.updateWorkflowStage('systems', 'processing');

        try {
            this.addLog('调用执行API...', 'api');

            // Make actual API call
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ skill_id: skillId, args: args })
            });

            const result = await response.json();
            this.addLog(`API返回 ${result.steps.length} 个执行步骤`, 'success');

            // Update step progress display
            const stepProgressEl = document.getElementById('stepProgress');
            const progressBar = document.getElementById('progressBar');
            let completedSystems = new Set();

            // Animate steps appearing one by one
            const streamSteps = document.getElementById('streamSteps');
            for (let i = 0; i < result.steps.length; i++) {
                const step = result.steps[i];
                const progress = ((i + 1) / result.steps.length) * 100;

                await this.sleep(200); // Animation delay

                // Update progress
                stepProgressEl.textContent = `${i + 1}/${result.steps.length}`;
                progressBar.style.width = `${progress}%`;

                // Log step
                this.addLog(`步骤 ${i + 1}: ${step.action}`, 'info');

                // Create enhanced step element
                const stepEl = document.createElement('div');
                stepEl.className = 'step-card animate-slideIn bg-gray-50 dark:bg-dark-hover rounded-lg p-2 border border-gray-100 dark:border-dark-border';

                // Build system operations HTML
                let sysOpsHtml = '';
                if (step.system_operations && step.system_operations.length > 0) {
                    sysOpsHtml = `
                        <div class="mt-1.5 pt-1.5 border-t border-gray-200 dark:border-dark-border">
                            <div class="flex flex-wrap gap-1">
                                ${step.system_operations.map(op => `
                                    <span class="op-complete inline-flex items-center px-1.5 py-0.5 text-[10px] rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                                        <svg class="w-2.5 h-2.5 mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                        </svg>
                                        ${op.system} → ${op.operation}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    `;

                    // Log system operations
                    step.system_operations.forEach(op => {
                        this.addLog(`  ↳ ${op.system}.${op.operation}()`, 'api');
                        completedSystems.add(op.system);
                    });
                }

                stepEl.innerHTML = `
                    <div class="flex items-start gap-2">
                        <div class="w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between">
                                <div class="text-xs font-medium text-gray-700 dark:text-gray-300">${this.escapeHtml(step.action)}</div>
                                <span class="text-[10px] text-gray-400">${step.duration_ms || Math.floor(Math.random() * 50 + 20)}ms</span>
                            </div>
                            ${step.result ? `<div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">${this.escapeHtml(step.result)}</div>` : ''}
                            ${sysOpsHtml}
                        </div>
                    </div>
                `;
                streamSteps.appendChild(stepEl);
                streamSteps.scrollTop = streamSteps.scrollHeight;

                // Update system badges in stream card
                if (step.system_operations) {
                    step.system_operations.forEach(op => {
                        const sysBadge = streamSystems.querySelector(`[data-system="${op.system}"]`);
                        if (sysBadge) {
                            const dot = sysBadge.querySelector('span');
                            if (dot) {
                                dot.className = 'w-1.5 h-1.5 rounded-full bg-green-500 mr-1';
                                dot.classList.remove('animate-pulse');
                            }
                            sysBadge.classList.add('bg-green-100', 'dark:bg-green-900/30', 'text-green-700', 'dark:text-green-400');
                            sysBadge.classList.remove('bg-gray-100', 'dark:bg-dark-border', 'text-gray-600', 'dark:text-gray-400');
                        }
                    });

                    // Update system progress
                    document.getElementById('systemProgress').textContent = `${completedSystems.size}/${(skill.affected_systems || []).length}`;
                }
            }

            // Update workflow stages
            this.updateWorkflowStage('execute', 'complete', `${result.steps.length}步骤`);
            this.updateWorkflowStage('systems', 'complete', `${completedSystems.size}系统`);

            // Update all system badges to success
            streamSystems.querySelectorAll('span[data-system]').forEach(el => {
                const dot = el.querySelector('span');
                if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-green-500 mr-1';
            });

            // Show final result
            await this.sleep(300);
            this.showStreamResult(streamCard, result);

            // Update workflow completion
            if (result.status === 'awaiting_approval') {
                this.updateWorkflowStage('complete', 'processing', '等待审批');
                this.addLog('执行完成，等待人工审批', 'warning');
                this.updateWorkflowStatus('awaiting_approval');
            } else {
                this.updateWorkflowStage('complete', 'complete', '执行成功');
                this.addLog('执行成功完成!', 'success');
                this.updateWorkflowStatus('complete');
            }

            // Stop timer
            this.stopTimer();
            const elapsed = ((Date.now() - this.executionStartTime) / 1000).toFixed(2);
            this.addLog(`总耗时: ${elapsed}s`, 'info');

            // Update metrics
            this.updateMetrics(skill.affected_systems || [], result.total_duration_ms);

            // Stop architecture flow
            this.stopArchitectureFlow();
            this.deactivateSystemBadges();

            // Update comparison panel
            this.updateComparisonPanel(skill);

        } catch (error) {
            console.error('执行失败:', error);
            this.addLog(`执行失败: ${error.message}`, 'error');
            this.updateWorkflowStage('execute', 'error', '失败');
            this.updateWorkflowStatus('error');
            this.stopTimer();
            this.stopArchitectureFlow();
            this.deactivateSystemBadges();
        }
    }

    updateWorkflowStatus(status) {
        const statusEl = document.getElementById('workflowStatus');
        if (!statusEl) return;

        const statusConfig = {
            'complete': { text: '已完成', bg: 'bg-green-100 dark:bg-green-900/30', color: 'text-green-600 dark:text-green-400' },
            'awaiting_approval': { text: '等待审批', bg: 'bg-amber-100 dark:bg-amber-900/30', color: 'text-amber-600 dark:text-amber-400' },
            'error': { text: '执行失败', bg: 'bg-red-100 dark:bg-red-900/30', color: 'text-red-600 dark:text-red-400' }
        };

        const config = statusConfig[status] || statusConfig.complete;
        statusEl.className = `px-2 py-0.5 text-[10px] font-medium rounded-full ${config.bg} ${config.color}`;
        statusEl.textContent = config.text;
        statusEl.classList.remove('animate-pulse');
    }

    showStreamResult(card, result) {
        const statusEl = card.querySelector('#streamStatus');
        if (statusEl) {
            statusEl.classList.remove('animate-pulse');
            if (result.status === 'awaiting_approval') {
                statusEl.className = 'px-2 py-0.5 text-[10px] font-semibold rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
                statusEl.textContent = '待审批';
            } else {
                statusEl.className = 'px-2 py-0.5 text-[10px] font-semibold rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
                statusEl.textContent = '已完成';
            }
        }

        const streamResult = card.querySelector('#streamResult');
        streamResult.classList.remove('hidden');
        streamResult.className = 'px-3 py-2 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-t border-green-200 dark:border-green-800';
        streamResult.innerHTML = `
            <div class="text-[10px] text-green-600 dark:text-green-400 font-medium mb-1">执行结果</div>
            <div class="text-xs font-mono p-2 bg-white dark:bg-dark-bg rounded border border-green-200 dark:border-green-800 whitespace-pre-wrap max-h-40 overflow-auto">${this.escapeHtml(result.final_result)}</div>
            ${result.status === 'awaiting_approval' ? `
                <div class="flex items-center justify-between mt-2 pt-2 border-t border-green-200 dark:border-green-800">
                    <span class="text-[10px] text-amber-600 dark:text-amber-400 font-medium">需要人工审批确认</span>
                    <div class="flex gap-1">
                        <button onclick="window.app.approveExecution('${result.execution_id}', true)" class="px-2 py-1 text-[10px] font-medium bg-green-500 hover:bg-green-600 text-white rounded transition-colors">批准</button>
                        <button onclick="window.app.approveExecution('${result.execution_id}', false)" class="px-2 py-1 text-[10px] font-medium bg-red-500 hover:bg-red-600 text-white rounded transition-colors">拒绝</button>
                    </div>
                </div>
            ` : ''}
        `;
    }

    updateMetrics(systems, durationMs) {
        // Calculate time saved (assume manual process takes 4 hours per system)
        const hoursSaved = systems.length * 4;
        this.metrics.timeSaved += hoursSaved;
        this.metrics.systems += systems.length;
        this.metrics.tasks += 1;

        // Animate counter updates
        this.animateCounter('metricTimeSaved', this.metrics.timeSaved);
        this.animateCounter('metricSystems', this.metrics.systems);
        this.animateCounter('metricTasks', this.metrics.tasks);
    }

    animateCounter(elementId, targetValue) {
        const el = document.getElementById(elementId);
        el.classList.add('animate-countUp');
        el.textContent = targetValue;
        setTimeout(() => el.classList.remove('animate-countUp'), 500);
    }

    updateComparisonPanel(skill) {
        const systemCount = (skill.affected_systems || []).length;
        const manualHours = systemCount * 1.5; // 1.5 hours per system manually

        document.getElementById('manualTime').textContent = `${manualHours}-${manualHours + 2}小时`;
        document.getElementById('manualSystems').textContent = `${systemCount}个`;
        document.getElementById('agentSystems').textContent = `${systemCount}个系统`;
        document.getElementById('efficiency').textContent = `${Math.round((1 - 0.5/60/manualHours) * 100)}%+`;
    }

    getCategoryInfo(category) {
        const categories = {
            menu: { label: '菜单', color: 'orange', icon: '🍔' },
            pricing: { label: '定价', color: 'green', icon: '💰' },
            launch: { label: '上市', color: 'blue', icon: '🚀' },
            campaign: { label: '活动', color: 'pink', icon: '🎉' },
            audit: { label: '巡检', color: 'yellow', icon: '📋' },
            report: { label: '报告', color: 'cyan', icon: '📊' },
            general: { label: '其他', color: 'gray', icon: '⚙️' },
            // 后端使用的类别
            product: { label: '产品', color: 'emerald', icon: '📦' },
            marketing: { label: '营销', color: 'pink', icon: '🎯' },
            training: { label: '培训', color: 'indigo', icon: '📚' },
            notification: { label: '通知', color: 'blue', icon: '🔔' },
            analytics: { label: '分析', color: 'cyan', icon: '📊' }
        };
        return categories[category] || categories.general;
    }

    renderSkillsList() {
        if (!this.skillsList || !this.skills) return;

        const filteredSkills = this.currentCategory === 'all'
            ? this.skills
            : this.skills.filter(s => s.category === this.currentCategory);

        this.skillsList.innerHTML = filteredSkills.map(skill => {
            const catInfo = this.getCategoryInfo(skill.category);
            const isSelected = skill.id === this.currentSkillId;
            const targetSystems = skill.target_systems || skill.affected_systems || [];

            return `
                <div class="skill-card p-2 rounded cursor-pointer border transition-all
                    ${isSelected
                        ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700'
                        : 'border-transparent hover:bg-gray-100 dark:hover:bg-dark-hover'}"
                     data-id="${skill.id}">
                    <div class="flex items-center gap-1.5 mb-0.5">
                        <div class="w-5 h-5 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                            <span class="text-[10px] text-white">${catInfo.icon}</span>
                        </div>
                        <h3 class="text-[11px] font-medium text-green-600 dark:text-green-400 flex-1 truncate">${skill.name}</h3>
                    </div>
                    <p class="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1">${skill.description}</p>
                    <div class="flex flex-wrap gap-0.5 mt-1">
                        ${targetSystems.slice(0, 3).map(sys => `
                            <span class="px-1 py-0.5 text-[8px] rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">${this.getSystemName(sys)}</span>
                        `).join('')}
                        ${targetSystems.length > 3 ? `<span class="px-1 py-0.5 text-[8px] text-gray-400">+${targetSystems.length - 3}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.skillsList.querySelectorAll('.skill-card').forEach(item => {
            item.addEventListener('click', () => {
                this.selectSkill(item.dataset.id);
                this.previewSkill(item.dataset.id);
            });
        });
    }

    getSystemName(systemCode) {
        const systems = { 'POS': 'POS', 'APP': 'App', 'MENU_BOARD': '菜单屏', 'INVENTORY': '库存', 'PRICING': '定价', 'CRM': '会员', 'MARKETING': '营销', 'TRAINING': '培训' };
        return systems[systemCode] || systemCode;
    }

    // ==================== 预览功能 ====================

    previewAgent(agentId) {
        const agent = this.agents.find(a => a.id === agentId);
        if (!agent) return;

        const sessionContent = document.getElementById('sessionContent');
        if (!sessionContent) return;

        // Handle capabilities
        const caps = (agent.capabilities || []).map(cap => {
            if (typeof cap === 'string') return cap;
            if (cap && cap.name) return cap.name;
            return '';
        }).filter(c => c);

        sessionContent.innerHTML = `
            <div class="space-y-3 animate-fadeIn">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center">
                            <span class="text-sm text-white">🤖</span>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">${agent.display_name || agent.id}</h3>
                            <span class="text-[10px] text-gray-400">Layer 2: Sub Agent</span>
                        </div>
                    </div>
                    <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                        Agent
                    </span>
                </div>

                <!-- Description -->
                <div class="bg-gray-50 dark:bg-dark-hover rounded-lg p-3">
                    <div class="text-[10px] text-gray-500 mb-1">描述</div>
                    <div class="text-xs text-gray-700 dark:text-gray-300">${agent.description || '子场景Agent，负责特定业务场景的处理'}</div>
                </div>

                <!-- Capabilities -->
                ${caps.length > 0 ? `
                <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-blue-600 dark:text-blue-400 mb-2">能力列表</div>
                    <div class="flex flex-wrap gap-1.5">
                        ${caps.map(cap => `
                            <span class="px-2 py-1 text-[10px] rounded-full bg-white dark:bg-dark-bg border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">${cap}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Workflows -->
                ${agent.workflows && agent.workflows.length > 0 ? `
                <div class="bg-cyan-50 dark:bg-cyan-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-cyan-600 dark:text-cyan-400 mb-2">关联工作流</div>
                    <div class="space-y-1">
                        ${agent.workflows.map(wf => `
                            <div class="flex items-center gap-2 text-xs">
                                <span class="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                                <span class="text-gray-700 dark:text-gray-300">${typeof wf === 'string' ? wf : wf.name || wf}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Meta Info -->
                <div class="grid grid-cols-2 gap-2 text-[10px]">
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-blue-600 dark:text-blue-400">${caps.length}</div>
                        <div class="text-gray-500">能力数</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-blue-600 dark:text-blue-400">${(agent.workflows || []).length}</div>
                        <div class="text-gray-500">工作流</div>
                    </div>
                </div>
            </div>
        `;

        this.addLog(`预览 Agent: ${agent.display_name || agent.id}`, 'api');
    }

    previewWorkflow(workflowId) {
        const workflow = this.workflows.find(w => w.id === workflowId);
        if (!workflow) return;

        const sessionContent = document.getElementById('sessionContent');
        if (!sessionContent) return;

        const nodes = workflow.nodes || [];
        const skills = workflow.involved_skills || [];

        sessionContent.innerHTML = `
            <div class="space-y-3 animate-fadeIn">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 flex items-center justify-center">
                            <span class="text-sm text-white">⚙️</span>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">${workflow.name}</h3>
                            <span class="text-[10px] text-gray-400">Layer 3: Workflow</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-1">
                        ${workflow.requires_approval ? `<span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">需审批</span>` : ''}
                        <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400">
                            Workflow
                        </span>
                    </div>
                </div>

                <!-- Description -->
                <div class="bg-gray-50 dark:bg-dark-hover rounded-lg p-3">
                    <div class="text-[10px] text-gray-500 mb-1">描述</div>
                    <div class="text-xs text-gray-700 dark:text-gray-300">${workflow.description || '工作流编排'}</div>
                </div>

                <!-- Nodes / Steps -->
                ${nodes.length > 0 ? `
                <div class="bg-cyan-50 dark:bg-cyan-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-cyan-600 dark:text-cyan-400 mb-2">执行节点 (${nodes.length})</div>
                    <div class="space-y-2">
                        ${nodes.map((node, idx) => `
                            <div class="flex items-start gap-2">
                                <div class="w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span class="text-[10px] text-white font-medium">${idx + 1}</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="text-xs font-medium text-gray-700 dark:text-gray-300">${node.name || node.skill_id || node}</div>
                                    ${node.description ? `<div class="text-[10px] text-gray-500 truncate">${node.description}</div>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Involved Skills -->
                ${skills.length > 0 ? `
                <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-green-600 dark:text-green-400 mb-2">涉及技能 (${skills.length})</div>
                    <div class="flex flex-wrap gap-1.5">
                        ${skills.map(skill => `
                            <span class="px-2 py-1 text-[10px] rounded-full bg-white dark:bg-dark-bg border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300">${typeof skill === 'string' ? skill : skill.name || skill}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Meta Info -->
                <div class="grid grid-cols-3 gap-2 text-[10px]">
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-cyan-600 dark:text-cyan-400">${nodes.length}</div>
                        <div class="text-gray-500">节点数</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-green-600 dark:text-green-400">${skills.length}</div>
                        <div class="text-gray-500">技能数</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold ${workflow.requires_approval ? 'text-amber-600 dark:text-amber-400' : 'text-gray-400'}">
                            ${workflow.requires_approval ? '是' : '否'}
                        </div>
                        <div class="text-gray-500">需审批</div>
                    </div>
                </div>
            </div>
        `;

        this.addLog(`预览 Workflow: ${workflow.name}`, 'api');
    }

    previewSkill(skillId) {
        console.log('previewSkill called with:', skillId, 'skills count:', this.skills?.length);

        const skill = this.skills?.find(s => s.id === skillId);
        if (!skill) {
            console.warn('Skill not found:', skillId);
            this.addLog(`未找到技能: ${skillId}`, 'warning');
            return;
        }

        const sessionContent = document.getElementById('sessionContent');
        if (!sessionContent) return;

        const catInfo = this.getCategoryInfo(skill.category);
        const targetSystems = skill.target_systems || skill.affected_systems || [];

        this.addLog(`预览技能: ${skill.name}`, 'api');

        sessionContent.innerHTML = `
            <div class="space-y-3 animate-fadeIn">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                            <span class="text-sm text-white">${catInfo.icon}</span>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">${skill.name}</h3>
                            <span class="text-[10px] text-gray-400">Layer 4: Skill</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-1">
                        ${skill.requires_approval ? `<span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">需审批</span>` : ''}
                        <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                            ${catInfo.label}
                        </span>
                    </div>
                </div>

                <!-- Description -->
                <div class="bg-gray-50 dark:bg-dark-hover rounded-lg p-3">
                    <div class="text-[10px] text-gray-500 mb-1">描述</div>
                    <div class="text-xs text-gray-700 dark:text-gray-300">${skill.description}</div>
                </div>

                <!-- Target Systems -->
                ${targetSystems.length > 0 ? `
                <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-green-600 dark:text-green-400 mb-2">目标系统 (${targetSystems.length})</div>
                    <div class="flex flex-wrap gap-1.5">
                        ${targetSystems.map(sys => `
                            <span class="px-2 py-1 text-[10px] rounded-full bg-white dark:bg-dark-bg border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300">${this.getSystemName(sys)}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Prompt -->
                ${skill.prompt ? `
                <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3">
                    <div class="text-[10px] text-purple-600 dark:text-purple-400 mb-2">执行步骤</div>
                    <div class="text-[10px] text-gray-600 dark:text-gray-400 space-y-1 font-mono">
                        ${skill.prompt.split('\n').filter(l => l.trim()).map(line => `
                            <div class="flex items-start gap-1">
                                <span class="text-purple-400">›</span>
                                <span>${this.escapeHtml(line.trim())}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Meta Info -->
                <div class="grid grid-cols-3 gap-2 text-[10px]">
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-green-600 dark:text-green-400">${targetSystems.length}</div>
                        <div class="text-gray-500">系统数</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold text-purple-600 dark:text-purple-400">${catInfo.label}</div>
                        <div class="text-gray-500">类别</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-dark-hover rounded p-2 text-center">
                        <div class="font-bold ${skill.requires_approval ? 'text-amber-600 dark:text-amber-400' : 'text-gray-400'}">
                            ${skill.requires_approval ? '是' : '否'}
                        </div>
                        <div class="text-gray-500">需审批</div>
                    </div>
                </div>
            </div>
        `;
    }

    selectSkill(skillId) {
        this.currentSkillId = skillId;
        const skill = this.skills.find(s => s.id === skillId);

        if (skill) {
            // 这些表单元素可能不存在于新模板中，使用可选链
            if (this.skillId) this.skillId.value = skill.id;
            if (this.skillName) this.skillName.value = skill.name;
            if (this.skillDesc) this.skillDesc.value = skill.description;
            if (this.skillPrompt) this.skillPrompt.value = skill.prompt || '';
            if (this.skillCategory) this.skillCategory.value = skill.category || 'general';
            if (this.requiresApproval) this.requiresApproval.checked = skill.requires_approval || false;

            document.querySelectorAll('.system-checkbox').forEach(cb => {
                const systems = skill.target_systems || skill.affected_systems || [];
                cb.checked = systems.includes(cb.value);
            });

            const catInfo = this.getCategoryInfo(skill.category);
            const systems = skill.target_systems || skill.affected_systems || [];
            if (this.skillMeta) this.skillMeta.textContent = `${catInfo.icon} ${catInfo.label} | ${systems.length}个系统`;
        }

        this.renderSkillsList();
    }

    newSkill() {
        this.currentSkillId = null;
        this.skillId.value = '';
        this.skillName.value = '';
        this.skillDesc.value = '';
        this.skillPrompt.value = '';
        this.skillCategory.value = 'general';
        this.requiresApproval.checked = false;
        document.querySelectorAll('.system-checkbox').forEach(cb => cb.checked = false);
        this.skillMeta.textContent = '定义Agent执行逻辑';
        this.renderSkillsList();
        this.skillName.focus();
    }

    getSelectedSystems() {
        return Array.from(document.querySelectorAll('.system-checkbox:checked')).map(cb => cb.value);
    }

    async saveSkill() {
        const skillData = {
            name: this.skillName.value,
            description: this.skillDesc.value,
            prompt: this.skillPrompt.value,
            category: this.skillCategory.value,
            requires_approval: this.requiresApproval.checked,
            affected_systems: this.getSelectedSystems()
        };

        if (!skillData.name || !skillData.description || !skillData.prompt) {
            alert('请填写所有必填字段');
            return;
        }

        try {
            const url = this.currentSkillId ? `/api/skills/${this.currentSkillId}` : '/api/skills';
            const method = this.currentSkillId ? 'PUT' : 'POST';
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(skillData)
            });
            const result = await response.json();
            this.currentSkillId = result.id;
            await this.loadSkills();
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    }

    async deleteSkill() {
        if (!this.currentSkillId || !confirm('确定要删除这个Skill吗？')) return;

        try {
            await fetch(`/api/skills/${this.currentSkillId}`, { method: 'DELETE' });
            this.currentSkillId = null;
            this.newSkill();
            await this.loadSkills();
        } catch (error) {
            console.error('删除失败:', error);
        }
    }

    async executeSkill() {
        if (!this.currentSkillId) {
            alert('请先选择一个Skill');
            return;
        }
        await this.executeSkillWithStreaming(this.currentSkillId, this.executeArgs.value || null);
    }

    activateSystemBadges(systems) {
        systems.forEach(sys => {
            const badge = this.systemBadges.querySelector(`[data-system="${sys}"]`);
            if (badge) badge.classList.add('active', 'ring-1', 'ring-offset-1');
        });
    }

    deactivateSystemBadges() {
        this.systemBadges.querySelectorAll('.system-badge').forEach(badge => {
            badge.classList.remove('active', 'ring-1', 'ring-offset-1');
        });
    }

    removePlaceholder() {
        const placeholder = this.executionResults.querySelector('#placeholder');
        if (placeholder) placeholder.remove();
    }

    async approveExecution(executionId, approved) {
        try {
            const response = await fetch(`/api/executions/${executionId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved })
            });
            const result = await response.json();

            if (approved) {
                // Show approval flow animation
                await this.showApprovalFlow(result);
            } else {
                this.showRejectionResult(result);
            }
        } catch (error) {
            console.error('审批失败:', error);
        }
    }

    async approveSession(sessionId, approved) {
        this.addLog(`审批操作: ${approved ? '批准' : '拒绝'} 会话 ${sessionId}`, 'warning');

        try {
            const response = await fetch(`/api/sessions/${sessionId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved, approved_by: '运营总监' })
            });
            const result = await response.json();

            if (approved) {
                await this.showSessionApprovalFlow(sessionId, result);
            } else {
                await this.showSessionRejection(sessionId, result);
            }
        } catch (error) {
            console.error('审批失败:', error);
            this.addLog(`审批失败: ${error.message}`, 'error');
        }
    }

    async showSessionApprovalFlow(sessionId, result) {
        this.addLog('开始执行审批后操作...', 'success');

        // Update status badge
        const statusBadge = document.getElementById('sessionStatusBadge');
        if (statusBadge) {
            statusBadge.textContent = '审批通过';
            statusBadge.className = 'px-2 py-0.5 text-[10px] font-medium rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400';
        }

        // Update session detail panel
        const sessionContent = document.getElementById('sessionContent');
        if (sessionContent) {
            const approvalSection = sessionContent.querySelector('.bg-amber-50');
            if (approvalSection) {
                approvalSection.innerHTML = `
                    <div class="flex items-center gap-2 mb-2">
                        <div class="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                        </div>
                        <span class="text-xs font-medium text-green-700 dark:text-green-400">已批准</span>
                        <span class="ml-auto text-[10px] text-gray-500">审批人: 运营总监</span>
                    </div>
                    <div id="approvalSteps" class="space-y-1.5"></div>
                `;
                approvalSection.className = 'bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800';
            }
        }

        // Animate approval steps
        const approvalSteps = document.getElementById('approvalSteps');
        if (approvalSteps) {
            const steps = [
                '验证审批权限...',
                '锁定配置数据...',
                '批量推送至所有门店...',
                '同步App和菜单屏...',
                '发送变更通知...',
                '记录变更日志...',
                '变更已全面生效 ✓'
            ];

            for (let i = 0; i < steps.length; i++) {
                await this.sleep(300);
                this.addLog(`  ${steps[i]}`, 'api');
                const stepEl = document.createElement('div');
                stepEl.className = 'animate-slideIn flex items-center gap-2';
                stepEl.innerHTML = `
                    <div class="w-4 h-4 rounded-full ${i === steps.length - 1 ? 'bg-green-500' : 'bg-blue-500'} flex items-center justify-center">
                        ${i === steps.length - 1
                            ? '<svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
                            : '<svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
                        }
                    </div>
                    <span class="text-[10px] ${i === steps.length - 1 ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-600 dark:text-gray-400'}">${steps[i]}</span>
                `;
                approvalSteps.appendChild(stepEl);
            }

            // Add summary
            await this.sleep(300);
            const summaryEl = document.createElement('div');
            summaryEl.className = 'animate-slideIn mt-3 pt-2 border-t border-green-200 dark:border-green-800';
            summaryEl.innerHTML = `
                <div class="grid grid-cols-3 gap-2 text-[10px]">
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">2,847</div>
                        <div class="text-gray-500">门店已同步</div>
                    </div>
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">100%</div>
                        <div class="text-gray-500">成功率</div>
                    </div>
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">已发送</div>
                        <div class="text-gray-500">通知</div>
                    </div>
                </div>
            `;
            approvalSteps.appendChild(summaryEl);
        }

        // Update workflow stage
        this.updateWorkflowStage('complete', 'complete', '审批通过');
        this.updateWorkflowStatus('complete');

        this.addLog('审批流程完成，变更已全面生效！', 'success');

        // Hide approval section after a brief delay
        await this.sleep(2000);
        const sessionContent2 = document.getElementById('sessionContent');
        if (sessionContent2) {
            const approvalSection2 = sessionContent2.querySelector('.bg-green-50');
            if (approvalSection2) {
                approvalSection2.style.transition = 'opacity 0.3s, max-height 0.3s';
                approvalSection2.style.opacity = '0';
                approvalSection2.style.maxHeight = '0';
                approvalSection2.style.overflow = 'hidden';
                approvalSection2.style.padding = '0';
                approvalSection2.style.marginTop = '0';
                await this.sleep(300);
                approvalSection2.remove();
            }
        }
    }

    async showSessionRejection(sessionId, result) {
        this.addLog('审批已拒绝，变更已取消', 'error');

        // Update status badge
        const statusBadge = document.getElementById('sessionStatusBadge');
        if (statusBadge) {
            statusBadge.textContent = '已拒绝';
            statusBadge.className = 'px-2 py-0.5 text-[10px] font-medium rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400';
        }

        // Update session detail panel
        const sessionContent = document.getElementById('sessionContent');
        if (sessionContent) {
            const approvalSection = sessionContent.querySelector('.bg-amber-50');
            if (approvalSection) {
                approvalSection.innerHTML = `
                    <div class="flex items-center gap-2 mb-2">
                        <div class="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </div>
                        <span class="text-xs font-medium text-red-700 dark:text-red-400">已拒绝</span>
                        <span class="ml-auto text-[10px] text-gray-500">审批人: 运营总监</span>
                    </div>
                    <div class="text-[10px] text-gray-600 dark:text-gray-400 space-y-1">
                        <div class="flex items-center gap-1">
                            <span class="w-1 h-1 rounded-full bg-red-400"></span>
                            变更请求已取消，不会影响任何系统
                        </div>
                        <div class="flex items-center gap-1">
                            <span class="w-1 h-1 rounded-full bg-red-400"></span>
                            相关人员已收到拒绝通知
                        </div>
                        <div class="flex items-center gap-1">
                            <span class="w-1 h-1 rounded-full bg-gray-400"></span>
                            如需重新申请，请修改后再次提交
                        </div>
                    </div>
                `;
                approvalSection.className = 'bg-red-50 dark:bg-red-900/20 rounded-lg p-3 border border-red-200 dark:border-red-800';

                // Hide approval section after a brief delay
                await this.sleep(2000);
                approvalSection.style.transition = 'opacity 0.3s, max-height 0.3s';
                approvalSection.style.opacity = '0';
                approvalSection.style.maxHeight = '0';
                approvalSection.style.overflow = 'hidden';
                approvalSection.style.padding = '0';
                approvalSection.style.marginTop = '0';
                await this.sleep(300);
                approvalSection.remove();
            }
        }

        // Update workflow stage
        this.updateWorkflowStage('complete', 'error', '已拒绝');
        this.updateWorkflowStatus('error');
    }

    async showApprovalFlow(result) {
        // Create approval flow card
        const flowCard = document.createElement('div');
        flowCard.className = 'animate-slideIn bg-white dark:bg-dark-card rounded-lg border border-green-300 dark:border-green-700 overflow-hidden mb-2';

        flowCard.innerHTML = `
            <div class="px-3 py-2 bg-green-50 dark:bg-green-900/20 border-b border-green-200 dark:border-green-800">
                <div class="flex items-center gap-2">
                    <div class="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                        <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <span class="text-xs font-medium text-green-700 dark:text-green-400">审批通过 - 变更正在生效</span>
                    <span class="ml-auto text-[10px] text-gray-500">审批人: ${result.approved_by || '运营总监'}</span>
                </div>
            </div>
            <div class="p-3">
                <div id="approvalSteps" class="space-y-2"></div>
            </div>
        `;

        this.executionResults.insertBefore(flowCard, this.executionResults.firstChild);

        // Animate approval steps
        const approvalSteps = flowCard.querySelector('#approvalSteps');
        const steps = this.getApprovalSteps(result.skill_name);

        for (let i = 0; i < steps.length; i++) {
            await this.sleep(400);
            const stepEl = document.createElement('div');
            stepEl.className = 'animate-slideIn flex items-center gap-2';
            stepEl.innerHTML = `
                <div class="w-4 h-4 rounded-full ${i === steps.length - 1 ? 'bg-green-500' : 'bg-blue-500'} flex items-center justify-center">
                    ${i === steps.length - 1
                        ? '<svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
                        : '<svg class="w-2.5 h-2.5 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>'
                    }
                </div>
                <span class="text-xs ${i === steps.length - 1 ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-600 dark:text-gray-400'}">${steps[i]}</span>
            `;
            approvalSteps.appendChild(stepEl);

            // Update previous step to completed
            if (i > 0) {
                const prevStep = approvalSteps.children[i - 1];
                const prevIcon = prevStep.querySelector('.rounded-full');
                prevIcon.classList.remove('bg-blue-500');
                prevIcon.classList.add('bg-green-500');
                prevIcon.innerHTML = '<svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            }
        }

        // Add final summary
        await this.sleep(300);
        const summaryEl = document.createElement('div');
        summaryEl.className = 'animate-slideIn mt-3 pt-3 border-t border-green-200 dark:border-green-800';
        summaryEl.innerHTML = `
            <div class="bg-green-50 dark:bg-green-900/30 rounded-lg p-2">
                <div class="flex items-center gap-2 mb-2">
                    <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="text-xs font-medium text-green-700 dark:text-green-400">变更已全部生效</span>
                </div>
                <div class="grid grid-cols-3 gap-2 text-[10px]">
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">2,847</div>
                        <div class="text-gray-500">门店已同步</div>
                    </div>
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">100%</div>
                        <div class="text-gray-500">成功率</div>
                    </div>
                    <div class="text-center p-1.5 bg-white dark:bg-dark-bg rounded">
                        <div class="font-bold text-green-600 dark:text-green-400">已发送</div>
                        <div class="text-gray-500">通知</div>
                    </div>
                </div>
            </div>
            <div class="mt-2 text-[10px] text-gray-500 dark:text-gray-400">
                <span class="text-green-600 dark:text-green-400">●</span> 所有相关人员已收到变更通知
            </div>
        `;
        approvalSteps.parentNode.appendChild(summaryEl);

        // Update metrics
        this.metrics.tasks += 1;
        this.animateCounter('metricTasks', this.metrics.tasks);
    }

    getApprovalSteps(skillName) {
        const stepsBySkill = {
            'menu-config': [
                '验证审批权限...',
                '锁定菜单配置...',
                '批量推送至所有POS终端...',
                '同步App商品状态...',
                '更新菜单屏显示内容...',
                '发送变更通知至相关人员...',
                '记录变更日志...',
                '变更已全面生效 ✓'
            ],
            'price-adjust': [
                '验证审批权限...',
                '检查价格规则合规性...',
                '更新定价引擎配置...',
                '批量同步POS价格表...',
                '刷新App价格缓存...',
                '推送菜单屏价格更新...',
                '通知区域经理和财务...',
                '价格调整已全面生效 ✓'
            ],
            'product-launch': [
                '验证上市审批链...',
                '激活库存SKU状态...',
                '开放POS新品点单按钮...',
                'App商品页设为可见...',
                '启动菜单屏宣传素材...',
                '触发培训系统推送...',
                '激活营销活动关联...',
                '新品已正式上线 ✓'
            ]
        };
        return stepsBySkill[skillName] || [
            '验证审批权限...',
            '准备变更数据...',
            '同步至各业务系统...',
            '验证数据一致性...',
            '发送变更通知...',
            '变更已生效 ✓'
        ];
    }

    showRejectionResult(result) {
        const card = document.createElement('div');
        card.className = 'animate-slideIn bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 p-3 mb-2';
        card.innerHTML = `
            <div class="flex items-center gap-2 mb-2">
                <div class="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                    <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </div>
                <span class="text-xs font-medium text-red-700 dark:text-red-400">审批已拒绝</span>
                <span class="ml-auto text-[10px] text-gray-500">审批人: ${result.approved_by || '运营总监'}</span>
            </div>
            <div class="text-[10px] text-gray-600 dark:text-gray-400 space-y-1">
                <div class="flex items-center gap-1">
                    <span class="w-1 h-1 rounded-full bg-red-400"></span>
                    变更请求已取消，不会影响任何系统
                </div>
                <div class="flex items-center gap-1">
                    <span class="w-1 h-1 rounded-full bg-red-400"></span>
                    相关人员已收到拒绝通知
                </div>
                <div class="flex items-center gap-1">
                    <span class="w-1 h-1 rounded-full bg-gray-400"></span>
                    如需重新申请，请修改后再次提交
                </div>
            </div>
        `;
        this.executionResults.insertBefore(card, this.executionResults.firstChild);
    }

    showMessage(message) {
        const card = document.createElement('div');
        card.className = 'animate-slideIn bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-3 mb-2';
        card.innerHTML = `<p class="text-xs text-blue-700 dark:text-blue-400">${this.escapeHtml(message)}</p>`;
        this.executionResults.insertBefore(card, this.executionResults.firstChild);
    }

    clearResults() {
        this.executionResults.innerHTML = `
            <div id="placeholder" class="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500 text-xs py-16">
                <svg class="w-10 h-10 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
                <p>输入自然语言指令</p>
                <p class="text-[10px] mt-0.5">或选择Skill执行</p>
            </div>
        `;
        // Also clear log and reset timer
        this.clearLog();
        this.stopTimer();
        this.executionTimer.classList.add('hidden');
        this.timerValue.textContent = '0.0s';
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==================== Tech PPT Modal ====================

    currentPptSlide = 0;
    pptSlides = [
        // Slide 1: 封面
        {
            title: '',
            content: `
                <div class="h-full flex flex-col items-center justify-center text-center">
                    <div class="mb-8">
                        <h1 class="text-5xl font-bold text-cyan-400 mb-4">Agent Skills</h1>
                        <p class="text-2xl text-white mb-2">企业运营智能化转型</p>
                        <p class="text-base text-gray-200">从人工运营到AI Agent驱动的智能运营新范式</p>
                    </div>
                    <div class="flex items-center gap-6 mt-6">
                        <div class="text-center">
                            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-2 mx-auto shadow-lg">
                                <span class="text-2xl">🧠</span>
                            </div>
                            <div class="text-xs text-gray-200">自然语言</div>
                        </div>
                        <div class="text-purple-400">→</div>
                        <div class="text-center">
                            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center mb-2 mx-auto shadow-lg">
                                <span class="text-2xl">🤖</span>
                            </div>
                            <div class="text-xs text-gray-200">Agent编排</div>
                        </div>
                        <div class="text-blue-400">→</div>
                        <div class="text-center">
                            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center mb-2 mx-auto shadow-lg">
                                <span class="text-2xl">⚡</span>
                            </div>
                            <div class="text-xs text-gray-200">Skills执行</div>
                        </div>
                        <div class="text-cyan-400">→</div>
                        <div class="text-center">
                            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mb-2 mx-auto shadow-lg">
                                <span class="text-2xl">🏢</span>
                            </div>
                            <div class="text-xs text-gray-200">系统落地</div>
                        </div>
                    </div>
                    <div class="mt-10 text-xs text-gray-300">
                        技术架构与实践指南 · 使用 ← → 键翻页
                    </div>
                </div>
            `
        },
        // Slide 2: 传统运营面临的挑战
        {
            title: '传统运营面临的挑战',
            content: `
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="p-4 rounded-xl bg-cyan-900/30 border-l-4 border-cyan-400">
                        <div class="text-white font-bold mb-2">人力成本高</div>
                        <div class="text-sm text-gray-300 space-y-1">
                            <div>重复性工作占比 60%+</div>
                            <div>人员培训周期长达数月</div>
                            <div>人才流失导致知识断层</div>
                        </div>
                        <div class="text-xl font-bold text-red-400 mt-3">成本持续攀升</div>
                    </div>
                    <div class="p-4 rounded-xl bg-cyan-900/30 border-l-4 border-cyan-400">
                        <div class="text-white font-bold mb-2">效率瓶颈</div>
                        <div class="text-sm text-gray-300 space-y-1">
                            <div>跨部门协作响应慢</div>
                            <div>信息孤岛严重</div>
                            <div>流程冗长易出错</div>
                        </div>
                        <div class="text-xl font-bold text-red-400 mt-3">效率损耗 40%</div>
                    </div>
                    <div class="p-4 rounded-xl bg-cyan-900/30 border-l-4 border-cyan-400">
                        <div class="text-white font-bold mb-2">响应滞后</div>
                        <div class="text-sm text-gray-300 space-y-1">
                            <div>市场变化快</div>
                            <div>人工决策链路长</div>
                            <div>错失商机成本高</div>
                        </div>
                        <div class="text-xl font-bold text-red-400 mt-3">决策周期 3-5天</div>
                    </div>
                </div>
                <div class="p-4 rounded-xl bg-cyan-500/20 border border-cyan-400/30 text-center">
                    <div class="text-cyan-400 font-bold text-lg">Agent Skills 将彻底改变这一现状</div>
                </div>
            `
        },
        // Slide 3: Agent Skills 重塑企业运营
        {
            title: 'Agent Skills 重塑企业运营',
            content: `
                <div class="grid grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div class="p-4 rounded-lg bg-slate-700/50 border border-slate-600">
                            <div class="text-gray-300 text-xs mb-1">阶段一</div>
                            <div class="text-white font-bold">传统人工运营</div>
                        </div>
                        <div class="text-center text-gray-300">↓</div>
                        <div class="p-4 rounded-lg bg-cyan-900/30 border border-cyan-500">
                            <div class="text-cyan-400 text-xs mb-1">阶段二</div>
                            <div class="text-white font-bold">Agent 赋能运营</div>
                        </div>
                        <div class="text-center text-gray-300">↓</div>
                        <div class="p-4 rounded-lg bg-emerald-900/30 border border-emerald-500">
                            <div class="text-emerald-400 text-xs mb-1">未来</div>
                            <div class="text-white font-bold">全自动智能运营</div>
                        </div>
                    </div>
                    <div class="p-5 rounded-xl bg-cyan-900/20 border border-cyan-500/30">
                        <div class="text-cyan-400 font-bold mb-4">核心价值</div>
                        <div class="space-y-3">
                            <div class="flex items-center gap-3">
                                <span class="text-emerald-400">✓</span>
                                <span class="text-white">运营效率提升 <b class="text-emerald-400">10x</b></span>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-emerald-400">✓</span>
                                <span class="text-white">人力成本降低 <b class="text-emerald-400">70%</b></span>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-emerald-400">✓</span>
                                <span class="text-white"><b class="text-emerald-400">7x24</b> 小时不间断运营</span>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-emerald-400">✓</span>
                                <span class="text-white">决策响应从<b>小时级</b>到<b class="text-emerald-400">秒级</b></span>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-emerald-400">✓</span>
                                <span class="text-white">跨系统<b class="text-emerald-400">无缝协作</b></span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 4: 实战案例引入
        {
            title: '实战案例：川香麻辣鸡腿堡全国上市',
            content: `
                <div class="flex flex-col items-center">
                    <div class="text-6xl mb-4">🍔</div>
                    <div class="text-xl text-cyan-400 font-bold mb-2">川香麻辣鸡腿堡</div>
                    <div class="text-gray-200 mb-6">新品全国2847家门店同步上市</div>
                    <div class="w-full max-w-2xl p-4 rounded-xl bg-slate-800/50 border border-slate-600 mb-6">
                        <div class="text-white text-sm leading-relaxed">
                            <span class="text-cyan-400 font-bold">"</span>
                            上线川香麻辣鸡腿堡，定价25元，华东区加价8%，配置满30减5的新品促销，下周一全国门店同步发布
                            <span class="text-cyan-400 font-bold">"</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-4 w-full max-w-2xl">
                        <div class="p-3 rounded-lg bg-purple-900/30 border border-purple-500/50 text-center">
                            <div class="text-2xl font-bold text-purple-400">3</div>
                            <div class="text-xs text-gray-200">个子任务</div>
                        </div>
                        <div class="p-3 rounded-lg bg-cyan-900/30 border border-cyan-500/50 text-center">
                            <div class="text-2xl font-bold text-cyan-400">12</div>
                            <div class="text-xs text-gray-200">个Skills调用</div>
                        </div>
                        <div class="p-3 rounded-lg bg-emerald-900/30 border border-emerald-500/50 text-center">
                            <div class="text-2xl font-bold text-emerald-400">2847</div>
                            <div class="text-xs text-gray-200">家门店同步</div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 5: Before vs After 对比
        {
            title: '传统方式 vs Agent Skills',
            content: `
                <div class="grid grid-cols-2 gap-6">
                    <div class="p-5 rounded-xl bg-red-900/20 border border-red-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-lg bg-red-500 flex items-center justify-center">
                                <span class="text-xl">👤</span>
                            </div>
                            <div>
                                <div class="text-white font-bold">传统人工运营</div>
                                <div class="text-red-400 text-sm">Before</div>
                            </div>
                        </div>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">上市周期</span>
                                <span class="font-bold text-red-400">3-5 天</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">涉及人员</span>
                                <span class="font-bold text-red-400">5-8 人</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">系统操作</span>
                                <span class="font-bold text-red-400">10+ 次登录</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">出错概率</span>
                                <span class="font-bold text-red-400">~15%</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">可追溯性</span>
                                <span class="font-bold text-red-400">困难</span>
                            </div>
                        </div>
                    </div>
                    <div class="p-5 rounded-xl bg-emerald-900/20 border border-emerald-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
                                <span class="text-xl">🤖</span>
                            </div>
                            <div>
                                <div class="text-white font-bold">Agent Skills</div>
                                <div class="text-emerald-400 text-sm">After</div>
                            </div>
                        </div>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">上市周期</span>
                                <span class="font-bold text-emerald-400">30 分钟</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">涉及人员</span>
                                <span class="font-bold text-emerald-400">1 人审批</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">系统操作</span>
                                <span class="font-bold text-emerald-400">全自动</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">出错概率</span>
                                <span class="font-bold text-emerald-400">~0.1%</span>
                            </div>
                            <div class="flex justify-between items-center p-2 rounded bg-slate-800/50">
                                <span class="text-gray-300 text-sm">可追溯性</span>
                                <span class="font-bold text-emerald-400">全链路</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mt-6 flex justify-center gap-8">
                    <div class="text-center">
                        <div class="text-3xl font-bold text-cyan-400">144x</div>
                        <div class="text-xs text-gray-200">速度提升</div>
                    </div>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-cyan-400">150x</div>
                        <div class="text-xs text-gray-200">错误减少</div>
                    </div>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-cyan-400">87%</div>
                        <div class="text-xs text-gray-200">人力节省</div>
                    </div>
                </div>
            `
        },
        // Slide 6: 四层架构 v2.0 (合并精简版)
        {
            title: '四层架构 v2.0',
            content: `
                <div class="flex items-center justify-center gap-2 mb-5">
                    <div class="px-3 py-2 rounded-lg bg-purple-500/30 border-2 border-purple-500 text-center">
                        <div class="text-white font-bold text-sm">Master Agent</div>
                    </div>
                    <span class="text-purple-400">→</span>
                    <div class="px-3 py-2 rounded-lg bg-cyan-500/20 border-2 border-cyan-400 text-center">
                        <div class="text-white font-bold text-sm">子场景Agent</div>
                    </div>
                    <span class="text-cyan-400">→</span>
                    <div class="px-3 py-2 rounded-lg bg-amber-500/20 border-2 border-amber-500 text-center">
                        <div class="text-white font-bold text-sm">Workflow</div>
                    </div>
                    <span class="text-amber-400">→</span>
                    <div class="px-3 py-2 rounded-lg bg-emerald-500/20 border-2 border-emerald-500 text-center">
                        <div class="text-white font-bold text-sm">Skills</div>
                    </div>
                    <span class="text-emerald-400">→</span>
                    <div class="px-3 py-2 rounded-lg bg-blue-500/20 border-2 border-blue-500 text-center">
                        <div class="text-white font-bold text-sm">MCP Tools</div>
                    </div>
                </div>
                <div class="grid grid-cols-5 gap-3">
                    <div class="p-3 rounded-lg bg-purple-900/30 border-t-2 border-purple-500">
                        <div class="text-purple-400 font-bold text-xs mb-2">🧠 Master Agent</div>
                        <ul class="text-white text-[10px] space-y-1">
                            <li>• 自然语言理解</li>
                            <li>• 意图识别分发</li>
                            <li>• 结果汇总反馈</li>
                        </ul>
                    </div>
                    <div class="p-3 rounded-lg bg-cyan-900/30 border-t-2 border-cyan-400">
                        <div class="text-cyan-400 font-bold text-xs mb-2">🤖 子场景Agent</div>
                        <ul class="text-white text-[10px] space-y-1">
                            <li>• 新品上市Agent</li>
                            <li>• 定价调整Agent</li>
                            <li>• 促销配置Agent</li>
                        </ul>
                    </div>
                    <div class="p-3 rounded-lg bg-amber-900/30 border-t-2 border-amber-500">
                        <div class="text-amber-400 font-bold text-xs mb-2">⚙️ Workflow</div>
                        <ul class="text-white text-[10px] space-y-1">
                            <li>• DAG流程编排</li>
                            <li>• 并行/串行控制</li>
                            <li>• 审批节点拦截</li>
                        </ul>
                    </div>
                    <div class="p-3 rounded-lg bg-emerald-900/30 border-t-2 border-emerald-500">
                        <div class="text-emerald-400 font-bold text-xs mb-2">⚡ Skills</div>
                        <ul class="text-white text-[10px] space-y-1">
                            <li>• 业务逻辑封装</li>
                            <li>• 幂等性保证</li>
                            <li>• 结果可追溯</li>
                        </ul>
                    </div>
                    <div class="p-3 rounded-lg bg-blue-900/30 border-t-2 border-blue-500">
                        <div class="text-blue-400 font-bold text-xs mb-2">🔌 MCP Tools</div>
                        <ul class="text-white text-[10px] space-y-1">
                            <li>• 原子能力调用</li>
                            <li>• 统一接口协议</li>
                            <li>• 系统集成层</li>
                        </ul>
                    </div>
                </div>
                <div class="mt-4 grid grid-cols-4 gap-2">
                    <div class="p-2 rounded-lg bg-slate-800/50 text-center">
                        <div class="text-xs text-cyan-300">异步消息队列</div>
                        <div class="text-[10px] text-gray-300">层间解耦</div>
                    </div>
                    <div class="p-2 rounded-lg bg-slate-800/50 text-center">
                        <div class="text-xs text-cyan-300">状态回传机制</div>
                        <div class="text-[10px] text-gray-300">实时追踪</div>
                    </div>
                    <div class="p-2 rounded-lg bg-slate-800/50 text-center">
                        <div class="text-xs text-cyan-300">错误处理</div>
                        <div class="text-[10px] text-gray-300">重试+熔断</div>
                    </div>
                    <div class="p-2 rounded-lg bg-slate-800/50 text-center">
                        <div class="text-xs text-cyan-300">人工审批</div>
                        <div class="text-[10px] text-gray-300">关键节点</div>
                    </div>
                </div>
            `
        },
        // Slide 5: Master Agent - 意图路由层
        {
            title: 'Master Agent - 意图路由层',
            content: `
                <div class="grid grid-cols-2 gap-6">
                    <div class="p-5 rounded-xl bg-purple-900/30 border border-purple-500">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center">
                                <span class="text-2xl">🧠</span>
                            </div>
                            <div>
                                <div class="text-white font-bold text-lg">Master Agent</div>
                                <div class="text-purple-300 text-sm">运营智能中枢</div>
                            </div>
                        </div>
                        <div class="space-y-2 text-sm">
                            <div class="flex items-center gap-2 text-white">
                                <span class="text-purple-400">▸</span> 自然语言理解与意图识别
                            </div>
                            <div class="flex items-center gap-2 text-white">
                                <span class="text-purple-400">▸</span> 任务分解与子Agent调度
                            </div>
                            <div class="flex items-center gap-2 text-white">
                                <span class="text-purple-400">▸</span> 执行结果汇总与反馈
                            </div>
                            <div class="flex items-center gap-2 text-white">
                                <span class="text-purple-400">▸</span> 异常处理与人工升级
                            </div>
                        </div>
                    </div>
                    <div class="space-y-3">
                        <div class="text-white text-sm mb-2">管理的子场景Agent</div>
                        <div class="p-3 rounded-lg bg-cyan-900/30 border border-cyan-500/50">
                            <div class="text-cyan-400 font-bold">新品上市 Agent</div>
                            <div class="text-gray-200 text-xs">产品创建、SKU配置、渠道发布</div>
                        </div>
                        <div class="p-3 rounded-lg bg-amber-900/30 border border-amber-500/50">
                            <div class="text-amber-400 font-bold">价格调整 Agent</div>
                            <div class="text-gray-200 text-xs">区域定价、批量调价、促销价格</div>
                        </div>
                        <div class="p-3 rounded-lg bg-emerald-900/30 border border-emerald-500/50">
                            <div class="text-emerald-400 font-bold">促销配置 Agent</div>
                            <div class="text-gray-200 text-xs">满减活动、折扣规则、优惠券</div>
                        </div>
                        <div class="p-3 rounded-lg bg-blue-900/30 border border-blue-500/50">
                            <div class="text-blue-400 font-bold">数据分析 Agent</div>
                            <div class="text-gray-200 text-xs">销售报表、趋势分析、异常预警</div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 8: Workflow 可视化
        {
            title: '新品上市 Workflow 执行流程',
            content: `
                <div class="grid grid-cols-4 gap-6">
                    <!-- 左侧：流程说明 -->
                    <div class="col-span-1 space-y-4">
                        <div class="p-4 rounded-xl bg-purple-900/30 border border-purple-500/50">
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-3 h-3 rounded-full bg-purple-500"></div>
                                <span class="text-purple-400 font-bold text-sm">开始/结束</span>
                            </div>
                            <div class="text-gray-300 text-xs">流程起点与终点</div>
                        </div>
                        <div class="p-4 rounded-xl bg-cyan-900/30 border border-cyan-500/50">
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-3 h-3 rounded bg-cyan-500"></div>
                                <span class="text-cyan-400 font-bold text-sm">Skills 节点</span>
                            </div>
                            <div class="text-gray-300 text-xs">自动化执行步骤</div>
                        </div>
                        <div class="p-4 rounded-xl bg-amber-900/30 border border-amber-500/50">
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-3 h-3 rotate-45 bg-amber-500"></div>
                                <span class="text-amber-400 font-bold text-sm">审批节点</span>
                            </div>
                            <div class="text-gray-300 text-xs">人工审批决策点</div>
                        </div>
                        <div class="p-4 rounded-xl bg-emerald-900/30 border border-emerald-500/50">
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-3 h-3 rounded bg-emerald-500"></div>
                                <span class="text-emerald-400 font-bold text-sm">并行执行</span>
                            </div>
                            <div class="text-gray-300 text-xs">多系统同步更新</div>
                        </div>
                    </div>
                    <!-- 右侧：流程图 -->
                    <div class="col-span-3 flex items-center justify-center p-4 rounded-xl bg-slate-800/30 border border-slate-700">
                        <svg width="680" height="340" viewBox="0 0 680 340">
                            <defs>
                                <linearGradient id="wfGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:#a855f7"/>
                                    <stop offset="100%" style="stop-color:#ec4899"/>
                                </linearGradient>
                                <linearGradient id="wfGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:#06b6d4"/>
                                    <stop offset="100%" style="stop-color:#3b82f6"/>
                                </linearGradient>
                                <linearGradient id="wfGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:#f59e0b"/>
                                    <stop offset="100%" style="stop-color:#ef4444"/>
                                </linearGradient>
                                <linearGradient id="wfGrad4" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:#10b981"/>
                                    <stop offset="100%" style="stop-color:#22c55e"/>
                                </linearGradient>
                                <filter id="glow">
                                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                                    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
                                </filter>
                                <marker id="wfArrowCyan" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                                    <polygon points="0 0, 8 3, 0 6" fill="#22d3ee"/>
                                </marker>
                                <marker id="wfArrowGreen" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                                    <polygon points="0 0, 8 3, 0 6" fill="#34d399"/>
                                </marker>
                            </defs>

                            <!-- 背景网格 -->
                            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#334155" stroke-width="0.5"/>
                            </pattern>
                            <rect width="100%" height="100%" fill="url(#grid)" opacity="0.3"/>

                            <!-- Start node -->
                            <circle cx="50" cy="170" r="28" fill="url(#wfGrad1)" filter="url(#glow)"/>
                            <text x="50" y="175" text-anchor="middle" fill="white" font-size="13" font-weight="bold">开始</text>

                            <!-- Node 1: Create SKU -->
                            <rect x="110" y="140" width="95" height="60" rx="10" fill="url(#wfGrad2)" filter="url(#glow)"/>
                            <text x="157" y="165" text-anchor="middle" fill="white" font-size="12" font-weight="bold">创建SKU</text>
                            <text x="157" y="183" text-anchor="middle" fill="#a5f3fc" font-size="9">inventory.sku</text>

                            <!-- Node 2: Create BOM -->
                            <rect x="110" y="230" width="95" height="60" rx="10" fill="url(#wfGrad2)" filter="url(#glow)"/>
                            <text x="157" y="255" text-anchor="middle" fill="white" font-size="12" font-weight="bold">配置BOM</text>
                            <text x="157" y="273" text-anchor="middle" fill="#a5f3fc" font-size="9">inventory.bom</text>

                            <!-- Node 3: Pricing -->
                            <rect x="240" y="140" width="95" height="60" rx="10" fill="url(#wfGrad2)" filter="url(#glow)"/>
                            <text x="287" y="165" text-anchor="middle" fill="white" font-size="12" font-weight="bold">计算定价</text>
                            <text x="287" y="183" text-anchor="middle" fill="#a5f3fc" font-size="9">pricing.calc</text>

                            <!-- Approval Node -->
                            <polygon points="390,170 430,135 470,170 430,205" fill="url(#wfGrad3)" filter="url(#glow)"/>
                            <text x="430" y="165" text-anchor="middle" fill="white" font-size="11" font-weight="bold">审批</text>
                            <text x="430" y="182" text-anchor="middle" fill="#fef3c7" font-size="9">¥>20</text>

                            <!-- Parallel zone -->
                            <rect x="495" y="55" width="130" height="235" rx="12" fill="none" stroke="#34d399" stroke-width="2" stroke-dasharray="6"/>
                            <text x="560" y="45" text-anchor="middle" fill="#34d399" font-size="11" font-weight="bold">并行执行区</text>

                            <!-- Node 4: POS Sync -->
                            <rect x="505" y="70" width="110" height="55" rx="10" fill="url(#wfGrad4)" filter="url(#glow)"/>
                            <text x="560" y="93" text-anchor="middle" fill="white" font-size="12" font-weight="bold">POS同步</text>
                            <text x="560" y="110" text-anchor="middle" fill="#a7f3d0" font-size="9">pos.product</text>

                            <!-- Node 5: App Sync -->
                            <rect x="505" y="140" width="110" height="55" rx="10" fill="url(#wfGrad4)" filter="url(#glow)"/>
                            <text x="560" y="163" text-anchor="middle" fill="white" font-size="12" font-weight="bold">App上架</text>
                            <text x="560" y="180" text-anchor="middle" fill="#a7f3d0" font-size="9">app.sync</text>

                            <!-- Node 6: Menu Board -->
                            <rect x="505" y="210" width="110" height="55" rx="10" fill="url(#wfGrad4)" filter="url(#glow)"/>
                            <text x="560" y="233" text-anchor="middle" fill="white" font-size="12" font-weight="bold">菜单屏更新</text>
                            <text x="560" y="250" text-anchor="middle" fill="#a7f3d0" font-size="9">menuboard</text>

                            <!-- End node -->
                            <circle cx="640" cy="170" r="28" fill="url(#wfGrad1)" filter="url(#glow)"/>
                            <text x="640" y="175" text-anchor="middle" fill="white" font-size="13" font-weight="bold">完成</text>

                            <!-- Arrows with glow -->
                            <path d="M78 170 L108 170" stroke="#22d3ee" stroke-width="3" marker-end="url(#wfArrowCyan)"/>
                            <path d="M157 200 L157 228" stroke="#22d3ee" stroke-width="3" marker-end="url(#wfArrowCyan)"/>
                            <path d="M205 170 L238 170" stroke="#22d3ee" stroke-width="3" marker-end="url(#wfArrowCyan)"/>
                            <path d="M205 260 L222 260 L222 170 L238 170" stroke="#22d3ee" stroke-width="2" fill="none"/>
                            <path d="M335 170 L388 170" stroke="#22d3ee" stroke-width="3" marker-end="url(#wfArrowCyan)"/>

                            <!-- After approval - green arrows -->
                            <path d="M470 170 L485 170 L485 97 L503 97" stroke="#34d399" stroke-width="3" fill="none" marker-end="url(#wfArrowGreen)"/>
                            <path d="M470 170 L503 167" stroke="#34d399" stroke-width="3" marker-end="url(#wfArrowGreen)"/>
                            <path d="M470 170 L485 170 L485 237 L503 237" stroke="#34d399" stroke-width="3" fill="none" marker-end="url(#wfArrowGreen)"/>

                            <!-- To end -->
                            <path d="M615 97 L625 97 L625 142" stroke="#34d399" stroke-width="2" fill="none"/>
                            <path d="M615 167 L612 170" stroke="#34d399" stroke-width="2" fill="none"/>
                            <path d="M615 237 L625 237 L625 198" stroke="#34d399" stroke-width="2" fill="none"/>
                            <circle cx="625" cy="170" r="4" fill="#34d399"/>
                        </svg>
                    </div>
                </div>
            `
        },
        // Slide 8: Skills + MCP Tools 能力层
        {
            title: 'Skills + MCP Tools 能力层',
            content: `
                <div class="mb-3 p-3 rounded-lg bg-gradient-to-r from-emerald-900/30 to-blue-900/30 border border-emerald-500/50">
                    <div class="text-sm font-bold text-emerald-400">Skills编排自动化步骤 | MCP提供原子能力</div>
                </div>
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <div class="p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/50 mb-3">
                            <div class="text-sm font-bold text-emerald-400 mb-3">Skills（业务逻辑封装）</div>
                            <div class="grid grid-cols-2 gap-2">
                                <div class="p-2 rounded bg-slate-800/50 text-xs">
                                    <div class="font-bold text-emerald-400 mb-1">产品 Skills</div>
                                    <div class="space-y-1 text-[10px] text-gray-200 font-mono">
                                        <div>inventory.sku</div>
                                        <div>inventory.bom</div>
                                        <div>product.publish</div>
                                    </div>
                                </div>
                                <div class="p-2 rounded bg-slate-800/50 text-xs">
                                    <div class="font-bold text-emerald-400 mb-1">价格 Skills</div>
                                    <div class="space-y-1 text-[10px] text-gray-200 font-mono">
                                        <div>pricing.calc</div>
                                        <div>pricing.batch</div>
                                        <div>pricing.region</div>
                                    </div>
                                </div>
                                <div class="p-2 rounded bg-slate-800/50 text-xs">
                                    <div class="font-bold text-emerald-400 mb-1">营销 Skills</div>
                                    <div class="space-y-1 text-[10px] text-gray-200 font-mono">
                                        <div>promo.create</div>
                                        <div>promo.discount</div>
                                        <div>campaign.push</div>
                                    </div>
                                </div>
                                <div class="p-2 rounded bg-slate-800/50 text-xs">
                                    <div class="font-bold text-emerald-400 mb-1">渠道 Skills</div>
                                    <div class="space-y-1 text-[10px] text-gray-200 font-mono">
                                        <div>pos.sync</div>
                                        <div>app.publish</div>
                                        <div>menu.update</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="p-4 rounded-xl bg-blue-900/20 border border-blue-500/50">
                            <div class="text-sm font-bold text-blue-400 mb-3">MCP Tools（底层原子能力）</div>
                            <div class="flex flex-wrap gap-2">
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">pos.product</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">app.sync</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">menuboard.push</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">erp.api</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">db.query</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">price.engine</span>
                                <span class="px-2 py-1 rounded bg-slate-800/50 text-[10px] font-mono text-blue-400">promo.engine</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="p-4 rounded-xl bg-amber-900/20 border border-amber-500/50 mb-3">
                            <div class="text-sm font-bold text-amber-400 mb-2">层级关系</div>
                            <div class="flex items-center gap-3">
                                <div class="px-3 py-2 rounded-lg bg-emerald-500 text-white text-xs font-bold">Skills</div>
                                <div class="text-gray-200 text-xs">业务逻辑封装</div>
                            </div>
                            <div class="text-center text-gray-300 my-1">↓ 调用</div>
                            <div class="flex items-center gap-3">
                                <div class="px-3 py-2 rounded-lg bg-blue-500 text-white text-xs font-bold">MCP</div>
                                <div class="text-gray-200 text-xs">原子操作执行</div>
                            </div>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-600 mb-3">
                            <div class="text-sm font-bold text-white mb-2">Skill 接口规范</div>
                            <div class="text-[10px] font-mono text-cyan-300 space-y-1">
                                <div>class Skill:</div>
                                <div class="pl-3">name: str</div>
                                <div class="pl-3">input_schema: dict</div>
                                <div class="pl-3">output_schema: dict</div>
                                <div class="pl-3">def execute(ctx)</div>
                            </div>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-800/50">
                            <div class="text-sm font-bold text-white mb-2">执行保障</div>
                            <div class="grid grid-cols-3 gap-2 text-xs">
                                <div class="flex items-center gap-1"><span class="text-emerald-400">✓</span><span class="text-gray-200">幂等性保证</span></div>
                                <div class="flex items-center gap-1"><span class="text-emerald-400">✓</span><span class="text-gray-200">超时自动重试</span></div>
                                <div class="flex items-center gap-1"><span class="text-emerald-400">✓</span><span class="text-gray-200">结果可追溯</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 9: 简化执行时序图
        {
            title: '执行时序图',
            content: `
                <div class="grid grid-cols-3 gap-6">
                    <div class="col-span-2">
                        <div class="space-y-3">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-purple-500 flex items-center justify-center text-white text-sm">1</div>
                                <div class="flex-1 p-3 rounded-lg bg-purple-900/30 border border-purple-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-purple-400 font-bold text-sm">用户 → Master Agent</span>
                                        <span class="text-purple-300 text-xs">0ms</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">"上市川香麻辣鸡腿堡，定价25元..."</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center text-white text-sm">2</div>
                                <div class="flex-1 p-3 rounded-lg bg-cyan-900/30 border border-cyan-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-cyan-400 font-bold text-sm">Master → 子场景Agent</span>
                                        <span class="text-cyan-300 text-xs">50ms</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">任务分解 → 产品Agent、定价Agent、促销Agent</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center text-white text-sm">3</div>
                                <div class="flex-1 p-3 rounded-lg bg-amber-900/30 border border-amber-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-amber-400 font-bold text-sm">Agent → Workflow</span>
                                        <span class="text-amber-300 text-xs">100ms</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">生成DAG执行计划，启动并行任务</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white text-sm">4</div>
                                <div class="flex-1 p-3 rounded-lg bg-emerald-900/30 border border-emerald-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-emerald-400 font-bold text-sm">Workflow → Skills → MCP</span>
                                        <span class="text-emerald-300 text-xs">150-500ms</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">执行12个Skills，调用28个MCP Tools</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-orange-500 flex items-center justify-center text-white text-sm">5</div>
                                <div class="flex-1 p-3 rounded-lg bg-orange-900/30 border border-orange-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-orange-400 font-bold text-sm">审批节点</span>
                                        <span class="text-orange-300 text-xs">等待人工</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">价格>20元触发审批 → 审批通过后继续</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center text-white text-sm">✓</div>
                                <div class="flex-1 p-3 rounded-lg bg-green-900/30 border border-green-500/50">
                                    <div class="flex items-center justify-between">
                                        <span class="text-green-400 font-bold text-sm">执行完成</span>
                                        <span class="text-green-300 text-xs">~30min</span>
                                    </div>
                                    <div class="text-white text-xs mt-1">2847家门店同步上线，全链路可追溯</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <div class="p-4 rounded-xl bg-slate-800/50">
                            <div class="text-sm font-bold text-white mb-3">执行统计</div>
                            <div class="space-y-2 text-xs">
                                <div class="flex justify-between"><span class="text-gray-200">总耗时</span><span class="text-cyan-400">~30分钟</span></div>
                                <div class="flex justify-between"><span class="text-gray-200">自动化步骤</span><span class="text-cyan-400">47步</span></div>
                                <div class="flex justify-between"><span class="text-gray-200">人工介入</span><span class="text-amber-400">1次审批</span></div>
                            </div>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-800/50">
                            <div class="text-sm font-bold text-white mb-3">关键特性</div>
                            <div class="space-y-2 text-xs text-gray-200">
                                <div class="flex items-center gap-2"><span class="text-emerald-400">✓</span>异步消息队列</div>
                                <div class="flex items-center gap-2"><span class="text-emerald-400">✓</span>并行任务执行</div>
                                <div class="flex items-center gap-2"><span class="text-emerald-400">✓</span>状态实时回传</div>
                                <div class="flex items-center gap-2"><span class="text-emerald-400">✓</span>错误自动重试</div>
                                <div class="flex items-center gap-2"><span class="text-emerald-400">✓</span>断点续传支持</div>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 10: MCP集成
        {
            title: 'MCP (Model Context Protocol) 集成',
            content: `
                <div class="grid grid-cols-3 gap-6">
                    <div class="col-span-2">
                        <div class="grid grid-cols-5 gap-3 mb-6">
                            ${['POS系统', 'App后台', '库存系统', '定价引擎', 'CRM'].map((name, i) => `
                                <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-600 text-center">
                                    <div class="text-2xl mb-1">${['🏪', '📱', '📦', '💰', '👥'][i]}</div>
                                    <div class="text-xs font-medium text-white">${name}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="grid grid-cols-5 gap-3">
                            ${['营销平台', '菜单屏', '培训系统', '数据分析', '供应链'].map((name, i) => `
                                <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-600 text-center">
                                    <div class="text-2xl mb-1">${['📢', '🖥️', '📚', '📊', '🚛'][i]}</div>
                                    <div class="text-xs font-medium text-white">${name}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="mt-6 p-4 rounded-xl bg-blue-900/20 border border-blue-500/50">
                            <div class="text-sm font-bold text-blue-400 mb-2">MCP工具调用流程</div>
                            <div class="flex items-center gap-2 text-xs text-gray-200">
                                <span class="px-2 py-1 bg-emerald-500/20 border border-emerald-500/50 rounded text-emerald-400">Skill</span>
                                <span class="text-gray-300">→</span>
                                <span class="px-2 py-1 bg-slate-700 rounded text-white">MCP Client</span>
                                <span class="text-gray-300">→</span>
                                <span class="px-2 py-1 bg-slate-700 rounded text-white">Tool Registry</span>
                                <span class="text-gray-300">→</span>
                                <span class="px-2 py-1 bg-blue-500/20 border border-blue-500/50 rounded text-blue-400">Server</span>
                                <span class="text-gray-300">→</span>
                                <span class="px-2 py-1 bg-green-900/30 border border-green-500/50 rounded text-green-400">执行</span>
                            </div>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <div class="p-4 rounded-xl bg-blue-900/20 border border-blue-500/50">
                            <div class="text-3xl font-bold text-blue-400">10</div>
                            <div class="text-sm text-gray-200">核心业务系统</div>
                        </div>
                        <div class="p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/50">
                            <div class="text-3xl font-bold text-emerald-400">28+</div>
                            <div class="text-sm text-gray-200">MCP工具</div>
                        </div>
                        <div class="p-4 rounded-xl bg-purple-900/20 border border-purple-500/50">
                            <div class="text-3xl font-bold text-purple-400">14</div>
                            <div class="text-sm text-gray-200">原子技能</div>
                        </div>
                        <div class="p-4 rounded-xl bg-amber-900/20 border border-amber-500/50">
                            <div class="text-3xl font-bold text-amber-400">4</div>
                            <div class="text-sm text-gray-200">预置工作流</div>
                        </div>
                    </div>
                </div>
            `
        },
        // Slide 11: 核心能力
        {
            title: '核心能力矩阵',
            content: `
                <div class="grid grid-cols-2 gap-6">
                    <div class="p-5 rounded-2xl bg-purple-900/20 border border-purple-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-xl bg-purple-500 flex items-center justify-center">
                                <span class="text-xl">🧠</span>
                            </div>
                            <div>
                                <div class="font-bold text-white">自然语言理解</div>
                                <div class="text-xs text-purple-300">NLU + 实体提取</div>
                            </div>
                        </div>
                        <ul class="space-y-1.5 text-sm text-gray-200">
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 复杂指令解析</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 相对日期识别 (下周一、月初)</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 竞品参照定价 (比竞品低2元)</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 产品系列/区域识别</li>
                        </ul>
                    </div>
                    <div class="p-5 rounded-2xl bg-amber-900/20 border border-amber-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center">
                                <span class="text-xl">⚡</span>
                            </div>
                            <div>
                                <div class="font-bold text-white">智能任务编排</div>
                                <div class="text-xs text-amber-300">Workflow Engine</div>
                            </div>
                        </div>
                        <ul class="space-y-1.5 text-sm text-gray-200">
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 自动拆解子任务</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 多Agent协同</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 审批节点控制</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 并行执行 + 异常重试</li>
                        </ul>
                    </div>
                    <div class="p-5 rounded-2xl bg-blue-900/20 border border-blue-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center">
                                <span class="text-xl">🔌</span>
                            </div>
                            <div>
                                <div class="font-bold text-white">MCP系统集成</div>
                                <div class="text-xs text-blue-300">统一接口协议</div>
                            </div>
                        </div>
                        <ul class="space-y-1.5 text-sm text-gray-200">
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 10大核心系统对接</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 标准化工具注册</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 调用链路追踪</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 执行结果聚合</li>
                        </ul>
                    </div>
                    <div class="p-5 rounded-2xl bg-cyan-900/20 border border-cyan-500/50">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-xl bg-cyan-500 flex items-center justify-center">
                                <span class="text-xl">📊</span>
                            </div>
                            <div>
                                <div class="font-bold text-white">实时预览 & 监控</div>
                                <div class="text-xs text-cyan-300">执行影响评估</div>
                            </div>
                        </div>
                        <ul class="space-y-1.5 text-sm text-gray-200">
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 影响范围预估</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 执行步骤可视化</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 审批需求提示</li>
                            <li class="flex items-center gap-2"><span class="text-emerald-400">✓</span> 业务报表自动生成</li>
                        </ul>
                    </div>
                </div>
            `
        },
        // Slide 12: 价值总结与未来路线图
        {
            title: '价值总结与未来路线图',
            content: `
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <div class="text-sm font-bold mb-3 text-white">业务价值</div>
                        <div class="grid grid-cols-2 gap-3 mb-4">
                            <div class="p-3 rounded-xl bg-purple-900/30 border border-purple-500/50 text-center">
                                <div class="text-2xl font-bold text-purple-400">96h+</div>
                                <div class="text-xs text-gray-200">月节省工时</div>
                            </div>
                            <div class="p-3 rounded-xl bg-emerald-900/30 border border-emerald-500/50 text-center">
                                <div class="text-2xl font-bold text-emerald-400">144x</div>
                                <div class="text-xs text-gray-200">执行效率提升</div>
                            </div>
                            <div class="p-3 rounded-xl bg-blue-900/30 border border-blue-500/50 text-center">
                                <div class="text-2xl font-bold text-blue-400">87%</div>
                                <div class="text-xs text-gray-200">人力成本节省</div>
                            </div>
                            <div class="p-3 rounded-xl bg-amber-900/30 border border-amber-500/50 text-center">
                                <div class="text-2xl font-bold text-amber-400">99.9%</div>
                                <div class="text-xs text-gray-200">执行准确率</div>
                            </div>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-600">
                            <div class="text-xs font-bold mb-2 text-white">ROI 分析</div>
                            <div class="space-y-2 text-xs text-gray-200">
                                <div class="flex justify-between"><span>运营人力节省</span><span class="font-bold text-emerald-400">¥50万/年</span></div>
                                <div class="flex justify-between"><span>错误减少损失</span><span class="font-bold text-emerald-400">¥30万/年</span></div>
                                <div class="flex justify-between"><span>响应速度提升价值</span><span class="font-bold text-emerald-400">¥20万/年</span></div>
                                <div class="border-t border-slate-600 pt-2 flex justify-between font-bold">
                                    <span class="text-white">年化投资回报</span><span class="text-cyan-400">¥100万+</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="text-sm font-bold mb-3 text-white">未来路线图</div>
                        <div class="space-y-3">
                            <div class="p-3 rounded-xl bg-emerald-900/20 border-l-4 border-emerald-500">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500 text-white">当前</span>
                                    <span class="font-bold text-sm text-white">辅助运营阶段</span>
                                </div>
                                <div class="text-xs text-gray-200">自然语言驱动、一键执行、人工审批</div>
                            </div>
                            <div class="p-3 rounded-xl bg-blue-900/20 border-l-4 border-blue-500">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="text-xs px-2 py-0.5 rounded-full bg-blue-500 text-white">Q2</span>
                                    <span class="font-bold text-sm text-white">自主运营阶段</span>
                                </div>
                                <div class="text-xs text-gray-200">主动发现运营机会、自动生成策略建议</div>
                            </div>
                            <div class="p-3 rounded-xl bg-purple-900/20 border-l-4 border-purple-500">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="text-xs px-2 py-0.5 rounded-full bg-purple-500 text-white">Q4</span>
                                    <span class="font-bold text-sm text-white">智能决策阶段</span>
                                </div>
                                <div class="text-xs text-gray-200">预测性运营、跨场景协同、自学习优化</div>
                            </div>
                            <div class="p-3 rounded-xl bg-amber-900/20 border-l-4 border-amber-500">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="text-xs px-2 py-0.5 rounded-full bg-amber-500 text-white">未来</span>
                                    <span class="font-bold text-sm text-white">全自动运营</span>
                                </div>
                                <div class="text-xs text-gray-200">Agent成为「数字员工」，人只做例外处理</div>
                            </div>
                        </div>
                        <div class="mt-4 p-3 rounded-xl bg-gradient-to-r from-purple-900/30 via-pink-900/30 to-amber-900/30 border border-purple-500/30 text-center">
                            <div class="text-sm font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-amber-400 bg-clip-text text-transparent">
                                让 AI Agent 成为运营团队的「数字员工」
                            </div>
                        </div>
                    </div>
                </div>
            `
        }
    ];

    openTechPptModal() {
        const modal = document.getElementById('techPptModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.currentPptSlide = 0;
            this.renderPptSlide();
        }
    }

    closeTechPptModal() {
        const modal = document.getElementById('techPptModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    pptPrevSlide() {
        if (this.currentPptSlide > 0) {
            this.currentPptSlide--;
            this.renderPptSlide();
        }
    }

    pptNextSlide() {
        if (this.currentPptSlide < this.pptSlides.length - 1) {
            this.currentPptSlide++;
            this.renderPptSlide();
        }
    }

    renderPptSlide() {
        const content = document.getElementById('pptContent');
        const pageNum = document.getElementById('pptPageNum');
        const totalPages = document.getElementById('pptTotalPages');

        if (!content) return;

        const slide = this.pptSlides[this.currentPptSlide];

        content.innerHTML = `
            <div class="h-full">
                ${slide.title ? `<h2 class="text-2xl font-bold mb-6 text-white">${slide.title}</h2>` : ''}
                ${slide.content}
            </div>
        `;

        if (pageNum) pageNum.textContent = this.currentPptSlide + 1;
        if (totalPages) totalPages.textContent = this.pptSlides.length;
    }

    // ==================== Business Impact Modal ====================

    openBusinessImpactModal() {
        const modal = document.getElementById('businessImpactModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.loadExecutionHistory();
        }
    }

    closeBusinessImpactModal() {
        const modal = document.getElementById('businessImpactModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async loadExecutionHistory() {
        const container = document.getElementById('agentExecutionHistory');
        if (!container) return;

        // 模拟执行历史数据
        const demoHistory = [
            {
                id: 'session-001',
                time: '2025-01-15 14:32',
                input: '上线新品川香麻辣鸡腿堡，定价25元',
                intent: 'product_launch',
                agents: ['产品管理Agent', '定价Agent'],
                workflows: 3,
                skills: 7,
                mcpCalls: 12,
                status: 'success',
                impact: '7天销售额 ¥2.4M，超预期18%'
            },
            {
                id: 'session-002',
                time: '2025-01-14 10:15',
                input: '华东区汉堡类产品涨价8%',
                intent: 'price_adjust',
                agents: ['定价Agent'],
                workflows: 1,
                skills: 4,
                mcpCalls: 8,
                status: 'success',
                impact: '销量+12.5%，弹性系数-0.42'
            },
            {
                id: 'session-003',
                time: '2025-01-12 09:00',
                input: '配置新年满30减5活动',
                intent: 'campaign_setup',
                agents: ['营销Agent'],
                workflows: 1,
                skills: 5,
                mcpCalls: 10,
                status: 'success',
                impact: 'ROI 385%，新增会员2.3万'
            },
            {
                id: 'session-004',
                time: '2025-01-10 16:45',
                input: '生成上周华东区销售报告',
                intent: 'report_generate',
                agents: ['报告Agent'],
                workflows: 1,
                skills: 2,
                mcpCalls: 4,
                status: 'success',
                impact: '节省分析师3小时工作'
            },
            {
                id: 'session-005',
                time: '2025-01-08 11:20',
                input: '川香系列产品库存预警检查',
                intent: 'inventory_check',
                agents: ['供应链Agent'],
                workflows: 1,
                skills: 3,
                mcpCalls: 6,
                status: 'success',
                impact: '及时补货，避免断货损失¥85K'
            }
        ];

        container.innerHTML = demoHistory.map(record => `
            <div class="p-3 rounded-lg bg-white dark:bg-dark-card border border-gray-100 dark:border-dark-border hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-[10px] text-gray-400">${record.time}</span>
                            <span class="px-1.5 py-0.5 text-[8px] rounded-full ${
                                record.intent === 'product_launch' ? 'bg-green-100 text-green-600 dark:bg-green-900/30' :
                                record.intent === 'price_adjust' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30' :
                                record.intent === 'campaign_setup' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30' :
                                'bg-gray-100 text-gray-600 dark:bg-gray-800'
                            }">${
                                record.intent === 'product_launch' ? '新品上市' :
                                record.intent === 'price_adjust' ? '价格调整' :
                                record.intent === 'campaign_setup' ? '营销活动' :
                                record.intent === 'report_generate' ? '报告生成' :
                                record.intent === 'inventory_check' ? '库存检查' : record.intent
                            }</span>
                            <span class="px-1.5 py-0.5 text-[8px] rounded-full bg-green-100 text-green-600 dark:bg-green-900/30">✓ 成功</span>
                        </div>
                        <div class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">${record.input}</div>
                        <div class="flex items-center gap-3 text-[10px] text-gray-500">
                            <span>👥 ${record.agents.join(', ')}</span>
                            <span>⚡ ${record.workflows}工作流</span>
                            <span>🔧 ${record.skills}技能</span>
                            <span class="text-purple-500">🔌 ${record.mcpCalls}次MCP</span>
                        </div>
                    </div>
                    <div class="text-right ml-4">
                        <div class="text-[10px] text-gray-400 mb-1">业务影响</div>
                        <div class="text-xs font-medium text-green-600 dark:text-green-400">${record.impact}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new SkillsApp();
});
