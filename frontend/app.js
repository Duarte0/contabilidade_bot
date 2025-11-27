// Configuração da API
const API_URL = 'http://localhost:8000/api';

// Estado global
let clientesSelecionados = new Set();
let todosClientes = [];

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    carregarTemplates();
    carregarDashboard();
});

// ========== NAVEGAÇÃO DE TABS ==========
function showTab(tabName) {
    // Esconder todos os tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remover active de todos os botões
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar tab selecionada
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
    
    // Carregar dados específicos
    if (tabName === 'dashboard') {
        carregarDashboard();
    } else if (tabName === 'templates') {
        carregarListaTemplates();
    }
}

// ========== CLIENTES ==========
async function carregarClientes() {
    const lista = document.getElementById('clientesLista');
    lista.innerHTML = '<div class="loading"><div class="spinner"></div>Carregando clientes...</div>';
    
    try {
        const response = await fetch(`${API_URL}/clientes/?limit=200`);
        const clientes = await response.json();
        
        todosClientes = clientes;
        renderizarClientes(clientes);
    } catch (error) {
        lista.innerHTML = `<div class="result-box error">Erro ao carregar clientes: ${error.message}</div>`;
    }
}

async function buscarClientes() {
    const busca = document.getElementById('searchClientes').value.trim();
    
    if (busca.length < 2) {
        // Se não tem busca, não faz nada
        return;
    }
    
    const lista = document.getElementById('clientesLista');
    lista.innerHTML = '<div class="loading"><div class="spinner"></div>Buscando...</div>';
    
    try {
        const response = await fetch(`${API_URL}/clientes/?nome=${encodeURIComponent(busca)}&limit=200`);
        const clientes = await response.json();
        
        todosClientes = clientes;
        renderizarClientes(clientes);
    } catch (error) {
        lista.innerHTML = `<div class="result-box error">Erro ao buscar: ${error.message}</div>`;
    }
}

function renderizarClientes(clientes) {
    const lista = document.getElementById('clientesLista');
    
    if (clientes.length === 0) {
        lista.innerHTML = '<div class="loading">Nenhum cliente encontrado</div>';
        return;
    }
    
    lista.innerHTML = clientes.map(cliente => `
        <div class="cliente-item ${clientesSelecionados.has(cliente.id) ? 'selected' : ''}" 
             onclick="toggleCliente(${cliente.id})">
            <input type="checkbox" 
                   class="cliente-checkbox" 
                   ${clientesSelecionados.has(cliente.id) ? 'checked' : ''}
                   onclick="event.stopPropagation()">
            <div class="cliente-info">
                <div class="cliente-nome">${cliente.nome}</div>
                <div class="cliente-detalhes">
                    Tel: ${cliente.telefone || 'Sem telefone'} | 
                    Email: ${cliente.email || 'Sem email'} |
                    <span class="badge badge-${cliente.status === 'ativo' ? 'success' : 'warning'}">
                        ${cliente.status || 'ativo'}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
    
    atualizarContador();
}

function toggleCliente(clienteId) {
    if (clientesSelecionados.has(clienteId)) {
        clientesSelecionados.delete(clienteId);
    } else {
        clientesSelecionados.add(clienteId);
    }
    
    renderizarClientes(todosClientes);
}

function atualizarContador() {
    const contador = document.getElementById('selectedCount');
    const count = clientesSelecionados.size;
    
    if (count > 0) {
        contador.style.display = 'inline-block';
        contador.textContent = `${count} cliente${count > 1 ? 's' : ''} selecionado${count > 1 ? 's' : ''}`;
    } else {
        contador.style.display = 'none';
    }
}

// ========== TEMPLATES ==========
async function carregarTemplates() {
    try {
        const response = await fetch(`${API_URL}/templates/`);
        const templates = await response.json();
        
        const select = document.getElementById('templateSelect');
        select.innerHTML = '<option value="">Usar mensagem personalizada</option>' +
            templates.map(t => `<option value="${t.nome}">${t.nome}</option>`).join('');
    } catch (error) {
        console.error('Erro ao carregar templates:', error);
    }
}

async function carregarListaTemplates() {
    const lista = document.getElementById('templatesList');
    lista.innerHTML = '<div class="loading"><div class="spinner"></div>Carregando...</div>';
    
    try {
        const response = await fetch(`${API_URL}/templates/`);
        const templates = await response.json();
        
        lista.innerHTML = templates.map(t => `
            <div class="card" style="margin-bottom: 15px; padding: 15px;">
                <h3 style="margin-bottom: 10px;">${t.nome}</h3>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto;">${t.template_text}</pre>
                <div style="margin-top: 10px; color: #7f8c8d; font-size: 13px;">
                    Variáveis: ${t.variaveis || 'nome, valor, dia_vencimento, data_vencimento, descricao'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        lista.innerHTML = `<div class="result-box error">Erro: ${error.message}</div>`;
    }
}

function atualizarTemplates() {
    // Pode adicionar lógica para filtrar templates por tipo
}

async function previewTemplate() {
    const templateName = document.getElementById('templateSelect').value;
    const previewBox = document.getElementById('previewBox');
    const previewContent = document.getElementById('previewContent');
    
    if (!templateName) {
        alert('Selecione um template primeiro');
        return;
    }
    
    if (clientesSelecionados.size === 0) {
        alert('Selecione pelo menos um cliente para preview');
        return;
    }
    
    const primeiroClienteId = Array.from(clientesSelecionados)[0];
    
    // Coletar variáveis extras
    const variaveisExtras = {};
    const valor = document.getElementById('var_valor').value.trim();
    const diaVencimento = document.getElementById('var_dia_vencimento').value.trim();
    const dataVencimento = document.getElementById('var_data_vencimento').value.trim();
    const descricao = document.getElementById('var_descricao').value.trim();
    
    if (valor) variaveisExtras.valor = valor;
    if (diaVencimento) variaveisExtras.dia_vencimento = diaVencimento;
    if (dataVencimento) variaveisExtras.data_vencimento = dataVencimento;
    if (descricao) variaveisExtras.descricao = descricao;
    
    try {
        const response = await fetch(`${API_URL}/cobrancas/preview`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                template_name: templateName,
                cliente_id: primeiroClienteId,
                variaveis_extras: variaveisExtras
            })
        });
        
        const preview = await response.json();
        previewContent.textContent = preview.mensagem_renderizada;
        previewBox.style.display = 'block';
    } catch (error) {
        alert('Erro ao gerar preview: ' + error.message);
    }
}

// ========== ENVIO EM LOTE ==========
async function enviarLote() {
    if (clientesSelecionados.size === 0) {
        alert('Selecione pelo menos um cliente!');
        return;
    }
    
    const mensagemPadrao = document.getElementById('mensagemPadrao').value.trim();
    const templateName = document.getElementById('templateSelect').value;
    const tipo = document.getElementById('tipoCobranca').value;
    
    if (!mensagemPadrao && !templateName) {
        alert('Digite uma mensagem ou selecione um template!');
        return;
    }
    
    // Coletar variáveis extras
    const variaveisExtras = {};
    const valor = document.getElementById('var_valor').value.trim();
    const diaVencimento = document.getElementById('var_dia_vencimento').value.trim();
    const dataVencimento = document.getElementById('var_data_vencimento').value.trim();
    const descricao = document.getElementById('var_descricao').value.trim();
    
    if (valor) variaveisExtras.valor = valor;
    if (diaVencimento) variaveisExtras.dia_vencimento = diaVencimento;
    if (dataVencimento) variaveisExtras.data_vencimento = dataVencimento;
    if (descricao) variaveisExtras.descricao = descricao;
    
    if (!confirm(`Confirma envio para ${clientesSelecionados.size} cliente(s)?`)) {
        return;
    }
    
    const resultBox = document.getElementById('resultBox');
    resultBox.innerHTML = '<div class="loading"><div class="spinner"></div>Enviando mensagens...</div>';
    resultBox.style.display = 'block';
    
    try {
        const payload = {
            clientes_ids: Array.from(clientesSelecionados),
            tipo: tipo,
            mensagem_padrao: mensagemPadrao || null,
            template_name: templateName || null,
            variaveis_extras: variaveisExtras,
            mensagens_customizadas: {},
            enviar_agora: true
        };
        
        const response = await fetch(`${API_URL}/cobrancas/enviar-lote`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const resultado = await response.json();
        
        // Mostrar resultado
        resultBox.className = 'result-box ' + (resultado.erros === 0 ? 'success' : 'error');
        resultBox.innerHTML = `
            <h3>Resultado do Envio</h3>
            <p><strong>Total:</strong> ${resultado.total_clientes} clientes</p>
            <p><strong>Enviados:</strong> ${resultado.enviados}</p>
            <p><strong>Erros:</strong> ${resultado.erros}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="max-height: 300px; overflow-y: auto;">
                ${resultado.detalhes.map(d => `
                    <div class="result-item">
                        <strong>${d.cliente_nome}</strong>
                        <span class="badge badge-${d.status === 'enviado' ? 'success' : 'error'}">
                            ${d.status}
                        </span>
                        ${d.erro ? `<br><small style="color: #721c24;">Erro: ${d.erro}</small>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Limpar seleção se sucesso total
        if (resultado.erros === 0) {
            setTimeout(() => {
                limparFormulario();
            }, 3000);
        }
        
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <h3>Erro no Envio</h3>
            <p>${error.message}</p>
        `;
    }
}

function limparFormulario() {
    clientesSelecionados.clear();
    document.getElementById('mensagemPadrao').value = '';
    document.getElementById('templateSelect').value = '';
    document.getElementById('var_valor').value = '';
    document.getElementById('var_dia_vencimento').value = '';
    document.getElementById('var_data_vencimento').value = '';
    document.getElementById('var_descricao').value = '';
    document.getElementById('previewBox').style.display = 'none';
    document.getElementById('resultBox').style.display = 'none';
    renderizarClientes(todosClientes);
}

// ========== DASHBOARD ==========
async function carregarDashboard() {
    const statsGrid = document.getElementById('statsGrid');
    const atividadesDiv = document.getElementById('atividadesRecentes');
    
    try {
        // Carregar estatísticas
        const statsResponse = await fetch(`${API_URL}/dashboard/stats`);
        const stats = await statsResponse.json();
        
        statsGrid.innerHTML = `
            <div class="stat-card blue">
                <div class="stat-value">${stats.total_clientes}</div>
                <div class="stat-label">Total de Clientes</div>
            </div>
            <div class="stat-card green">
                <div class="stat-value">${stats.clientes_ativos}</div>
                <div class="stat-label">Clientes Ativos</div>
            </div>
            <div class="stat-card red">
                <div class="stat-value">${stats.clientes_inadimplentes}</div>
                <div class="stat-label">Inadimplentes</div>
            </div>
            <div class="stat-card orange">
                <div class="stat-value">${stats.cobrancas_mes}</div>
                <div class="stat-label">Cobranças este Mês</div>
            </div>
        `;
        
        // Carregar atividades
        const atividadesResponse = await fetch(`${API_URL}/dashboard/atividades-recentes?limit=10`);
        const atividades = await atividadesResponse.json();
        
        atividadesDiv.innerHTML = atividades.atividades.map(a => `
            <div class="result-item">
                <span class="badge badge-${a.status === 'enviado' ? 'success' : 'warning'}">
                    ${a.tipo}
                </span>
                <strong>${a.cliente}</strong> - ${a.preview}
                <br><small style="color: #7f8c8d;">${new Date(a.data).toLocaleString('pt-BR')}</small>
            </div>
        `).join('');
        
    } catch (error) {
        statsGrid.innerHTML = `<div class="result-box error">Erro: ${error.message}</div>`;
        atividadesDiv.innerHTML = `<div class="result-box error">Erro: ${error.message}</div>`;
    }
}
