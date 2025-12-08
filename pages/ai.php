<div class="flex h-full p-6 gap-6">
    <!-- CHAT AREA -->
    <div class="flex-1 flex flex-col nexus-card p-6">
        <div class="flex justify-between items-center mb-6 border-b border-nexus-border pb-4">
            <div class="flex items-center gap-3">
                <div
                    class="w-10 h-10 rounded-full bg-nexus-blue/20 flex items-center justify-center border border-nexus-blue/30">
                    <i data-lucide="bot" class="text-nexus-blue"></i>
                </div>
                <div>
                    <h2 class="text-xl font-bold">Nexus Brain</h2>
                    <div class="text-xs text-green-400 font-mono flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                        ONLINE - GPT-4o
                    </div>
                </div>
            </div>
            <button class="btn btn-ghost" id="clear-chat"><i data-lucide="trash-2"></i></button>
        </div>

        <div id="chat-history" class="flex-1 overflow-y-auto mb-6 space-y-4 pr-2">
            <!-- MESSAGES WILL APPEAR HERE -->
            <div class="flex flex-col gap-1 items-start animate-fadeIn">
                <span class="text-xs text-nexus-subtext ml-2">Nexus AI</span>
                <div
                    class="bg-white/5 p-4 rounded-2xl rounded-tl-none border border-white/5 max-w-[80%] text-sm leading-relaxed">
                    Hello. I am Nexus AI. I can analyze markets, fix code, and execute trades. How can I assist?
                </div>
            </div>
        </div>

        <div class="relative">
            <div class="input-group flex items-center gap-2 p-2">
                <input type="text" id="ai-input" class="input-field p-2"
                    placeholder="Ask me to buy BTC or analyze EURUSD...">
                <button id="send-btn" class="btn btn-primary p-3 rounded-lg"><i data-lucide="send"></i></button>
            </div>
        </div>
    </div>

    <!-- SIDE PANEL (LOGS) -->
    <div class="w-80 nexus-card p-6 flex flex-col">
        <h3 class="text-sm font-bold text-nexus-subtext uppercase mb-4">System Logs</h3>
        <div class="flex-1 font-mono text-xs text-nexus-subtext overflow-hidden opacity-70" id="system-logs">
            <div class="mb-2 text-green-500">> System Initialized</div>
            <div class="mb-2 text-blue-400">> Connected to Brain</div>
            <div class="mb-2 text-white/50">> Waiting for input...</div>
        </div>
    </div>
</div>

<script src="/assets/js/api.js"></script>
<script>
    $(document).ready(function () {
        // Auto-scroll to bottom
        function scrollToBottom() {
            var chatHistory = document.getElementById("chat-history");
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        // Add User Message
        function addUserMessage(text) {
            $('#chat-history').append(`
                <div class="flex flex-col gap-1 items-end animate-fadeIn">
                    <span class="text-xs text-nexus-subtext mr-2">You</span>
                    <div class="bg-nexus-blue/20 p-4 rounded-2xl rounded-tr-none border border-nexus-blue/30 max-w-[80%] text-sm leading-relaxed">
                        ${text}
                    </div>
                </div>
            `);
            scrollToBottom();
        }

        // Add AI Message (Handles Text or Object)
        function addAIMessage(data) {
            let content = "";
            
            if (typeof data === 'string') {
                content = data.replace(/\n/g, '<br>');
            } else if (data.type === 'trade_proposal') {
                // RENDER TRADE PROPOSAL CARD
                const isBuy = data.action === 'BUY';
                const colorClass = isBuy ? 'text-green-400' : 'text-red-400';
                const bgClass = isBuy ? 'bg-nexus-green/10 border-nexus-green/30' : 'bg-nexus-red/10 border-nexus-red/30';
                const btnClass = isBuy ? 'bg-nexus-green text-black hover:bg-green-400' : 'bg-nexus-red text-white hover:bg-red-500';
                
                content = `
                    <div class="flex flex-col gap-2 ${bgClass} p-4 rounded-xl border animate-pulse">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-sm text-white">⚠️ TRADING OPPORTUNITY</span>
                            <span class="text-xs font-mono opacity-70">CONFIDENCE: 92%</span>
                        </div>
                        <div class="text-2xl font-bold ${colorClass}">${data.action} ${data.symbol}</div>
                        <div class="text-xs font-mono text-white/70">VOLUME: ${data.volume} LOTS</div>
                        <div class="mt-2 text-xs italic text-white/50">"${data.reason}"</div>
                        <div class="flex gap-2 mt-3">
                            <button onclick="executeProposal('${data.symbol}', '${data.action}', ${data.volume})" class="flex-1 py-2 rounded-lg font-bold text-xs ${btnClass} transition-all shadow-lg hover:scale-105">
                                APPROVE
                            </button>
                            <button class="flex-1 py-2 rounded-lg font-bold text-xs bg-white/10 text-white hover:bg-white/20 transition-all">
                                REJECT
                            </button>
                        </div>
                    </div>
                `;
            }

             $('#chat-history').append(`
                <div class="flex flex-col gap-1 items-start animate-fadeIn">
                    <span class="text-xs text-nexus-subtext ml-2">Nexus Brain</span>
                    <div class="bg-white/5 p-4 rounded-2xl rounded-tl-none border border-white/5 max-w-[80%] text-sm leading-relaxed">
                        ${content}
                    </div>
                </div>
            `);
            scrollToBottom();
        }

        // Global function for the Approve button
        window.executeProposal = async function(symbol, action, volume) {
            alert(`🚀 AUTHENTICATING: Executing ${action} ${symbol}...`);
            const res = await NexusAPI.placeTrade(symbol, action, volume);
            if(res.status === 'Trade Executed' || res.ticket) {
                 addAIMessage(`✅ ORDER CONFIRMED: Ticket #${res.ticket}`);
            } else {
                 addAIMessage(`❌ EXECUTION FAILED: ${res.error}`);
            }
        };

        async function sendMessage() {
            const msg = $('#ai-input').val().trim();
            if (!msg) return;

            $('#ai-input').val('');
            addUserMessage(msg);
            $('#system-logs').append(`<div class="mb-1 text-white">> Processing: "${msg.substring(0, 15)}..."</div>`);

            // Disable Input
            $('#ai-input').prop('disabled', true);
            $('#send-btn').html('<i data-lucide="loader" class="animate-spin"></i>');

            // Send to Real Backend
            const res = await NexusAPI.aiChat(msg); // TODO: Pass history if needed

            if (res.response) {
                addAIMessage(res.response);
                $('#system-logs').append(`<div class="mb-1 text-nexus-green">> Response Received</div>`);
            } else if (res.error) {
                addAIMessage("⚠️ Error: " + res.error);
                $('#system-logs').append(`<div class="mb-1 text-nexus-red">> Error: ${res.error}</div>`);
            }

            // Re-enable
            $('#ai-input').prop('disabled', false).focus();
            $('#send-btn').html('<i data-lucide="send"></i>');
            lucide.createIcons();
        }

        $('#send-btn').click(sendMessage);
        $('#ai-input').keypress((e) => { if (e.which == 13) sendMessage(); });
    });
</script>