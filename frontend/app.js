// Configuração da API - Usa window.APP_CONFIG se disponível
const API_URL = window.APP_CONFIG?.API_URL || (
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000/api'
        : `${window.location.protocol}//${window.location.hostname}:8000/api`
);

console.log('🚀 Sistema inicializado');
console.log('📡 API URL:', API_URL);

// Estado global
let clientesSelecionados = new Set();
let todosClientes = [];
let clientesCache = {}; // Cache para manter dados dos clientes selecionados

// ========== SISTEMA DE TOASTS ==========
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'check-circle',
        error: 'x-circle',
        info: 'info'
    };
    
    toast.innerHTML = `
        <i data-lucide="${iconMap[type]}"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    lucide.createIcons();
    
    // Auto remover após 5 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    carregarTemplates();
    carregarDashboard();
    showToast('Sistema Pronto', 'Bem-vindo ao Sistema de Mensagens WhatsApp', 'success');
    // Render de ícones caso o script já esteja disponível
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
    
    // Fechar modais ao clicar fora
    window.onclick = function(event) {
        const modalTemplate = document.getElementById('modalTemplate');
        const modalClientes = document.getElementById('modalClientesSelecionados');
        
        if (event.target === modalTemplate) {
            fecharModalTemplate();
        }
        if (event.target === modalClientes) {
            fecharModalClientesSelecionados();
        }
    };
});

// Inserir variável no textarea da mensagem no cursor
function insertVar(varName) {
    const textarea = document.getElementById('mensagemPadrao');
    const snippet = '${' + varName + '}';
    const start = textarea.selectionStart ?? textarea.value.length;
    const end = textarea.selectionEnd ?? textarea.value.length;
    const before = textarea.value.substring(0, start);
    const after = textarea.value.substring(end);
    textarea.value = before + snippet + after;
    // reposiciona o cursor após o snippet
    const pos = (before + snippet).length;
    textarea.focus();
    textarea.setSelectionRange(pos, pos);
}

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
    event.target.closest('.tab').classList.add('active');
    
    // Reinicializar ícones (seguro)
    setTimeout(() => {
        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }, 50);
    
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
    lista.innerHTML = '<div class="loading"><div class="spinner"></div><p>Carregando clientes...</p></div>';
    
    try {
        const response = await fetch(`${API_URL}/clientes/?limit=200`);
        const clientes = await response.json();
        
        todosClientes = clientes;
        renderizarClientes(clientes);
        showToast('Sucesso', `${clientes.length} clientes carregados`, 'success');
    } catch (error) {
        lista.innerHTML = `<div class="empty-state">
            <i data-lucide="alert-circle" style="width: 48px; height: 48px; color: var(--danger-500);"></i>
            <p>Erro ao carregar clientes: ${error.message}</p>
        </div>`;
        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
        showToast('Erro', 'Não foi possível carregar os clientes', 'error');
    }
}

// (Versão antiga de buscarClientes removida; usando versão com debounce abaixo)
function renderizarClientes(clientes) {
    const lista = document.getElementById('clientesLista');
    
    if (clientes.length === 0) {
        lista.innerHTML = `<div class="empty-state">
            <i data-lucide="users" style="width: 48px; height: 48px;"></i>
            <p>Nenhum cliente encontrado</p>
        </div>`;
        lucide.createIcons();
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
    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function toggleCliente(clienteId) {
    if (clientesSelecionados.has(clienteId)) {
        clientesSelecionados.delete(clienteId);
        delete clientesCache[clienteId]; // Remove do cache
    } else {
        clientesSelecionados.add(clienteId);
        // Adiciona ao cache
        const cliente = todosClientes.find(c => c.id === clienteId);
        if (cliente) {
            clientesCache[clienteId] = cliente;
        }
    }
    
    renderizarClientes(todosClientes);
}

function atualizarContador() {
    const contador = document.getElementById('selectedCount');
    const count = clientesSelecionados.size;
    
    if (count > 0) {
        contador.style.display = 'inline-flex';
        contador.innerHTML = `
            <i data-lucide="check-circle"></i>
            <span>${count} cliente${count > 1 ? 's' : ''} selecionado${count > 1 ? 's' : ''}</span>
        `;
        lucide.createIcons();
    } else {
        contador.style.display = 'none';
    }
}

// ========== MODAL CLIENTES SELECIONADOS ==========
function abrirModalClientesSelecionados() {
    const modal = document.getElementById('modalClientesSelecionados');
    const lista = document.getElementById('listaClientesSelecionados');
    
    if (clientesSelecionados.size === 0) {
        showToast('Aviso', 'Nenhum cliente selecionado', 'info');
        return;
    }
    
    // Busca os dados dos clientes selecionados usando o cache
    const clientesSelecionadosArray = Array.from(clientesSelecionados);
    const clientesDetalhes = clientesSelecionadosArray
        .map(id => clientesCache[id])
        .filter(c => c !== undefined); // Remove clientes não encontrados
    
    // Renderiza a lista
    lista.innerHTML = clientesDetalhes.map(cliente => {
        const iniciais = cliente.nome.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        const telefone = cliente.telefone || 'Sem telefone';
        const email = cliente.email || 'Sem email';
        
        return `
            <div class="cliente-selecionado-item">
                <div class="cliente-selecionado-info">
                    <div class="cliente-selecionado-avatar">${iniciais}</div>
                    <div class="cliente-selecionado-detalhes">
                        <div class="cliente-selecionado-nome">${cliente.nome}</div>
                        <div class="cliente-selecionado-contato">
                            <i data-lucide="phone"></i>
                            <span>${telefone}</span>
                            ${email !== 'Sem email' ? `<i data-lucide="mail" style="margin-left: 12px;"></i><span>${email}</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="cliente-selecionado-actions">
                    <button class="btn-icon danger" onclick="removerClienteDaSelecao(${cliente.id})" title="Remover da seleção">
                        <i data-lucide="x" style="width: 16px; height: 16px;"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    lucide.createIcons();
    modal.style.display = 'flex';
}

function fecharModalClientesSelecionados() {
    document.getElementById('modalClientesSelecionados').style.display = 'none';
}

function removerClienteDaSelecao(clienteId) {
    clientesSelecionados.delete(clienteId);
    delete clientesCache[clienteId];
    atualizarContador();
    renderizarClientes(todosClientes);
    
    // Atualiza o conteúdo do modal sem reabrir
    if (clientesSelecionados.size > 0) {
        const lista = document.getElementById('listaClientesSelecionados');
        const clientesSelecionadosArray = Array.from(clientesSelecionados);
        const clientesDetalhes = clientesSelecionadosArray
            .map(id => clientesCache[id])
            .filter(c => c !== undefined);
        
        lista.innerHTML = clientesDetalhes.map(cliente => {
            const iniciais = cliente.nome.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
            const telefone = cliente.telefone || 'Sem telefone';
            const email = cliente.email || 'Sem email';
            
            return `
                <div class="cliente-selecionado-item">
                    <div class="cliente-selecionado-info">
                        <div class="cliente-selecionado-avatar">${iniciais}</div>
                        <div class="cliente-selecionado-detalhes">
                            <div class="cliente-selecionado-nome">${cliente.nome}</div>
                            <div class="cliente-selecionado-contato">
                                <i data-lucide="phone"></i>
                                <span>${telefone}</span>
                                ${email !== 'Sem email' ? `<i data-lucide="mail" style="margin-left: 12px;"></i><span>${email}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="cliente-selecionado-actions">
                        <button class="btn-icon danger" onclick="removerClienteDaSelecao(${cliente.id})" title="Remover da seleção">
                            <i data-lucide="x" style="width: 16px; height: 16px;"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        lucide.createIcons();
    } else {
        fecharModalClientesSelecionados();
        showToast('Aviso', 'Todos os clientes foram removidos da seleção', 'info');
    }
}

function limparSelecao() {
    if (confirm('Tem certeza que deseja remover todos os clientes da seleção?')) {
        clientesSelecionados.clear();
        clientesCache = {}; // Limpa o cache
        atualizarContador();
        renderizarClientes(todosClientes);
        fecharModalClientesSelecionados();
        showToast('Sucesso', 'Seleção limpa', 'success');
    }
}

// ========== TEMPLATES ==========
async function carregarTemplates() {
    try {
        const response = await fetch(`${API_URL}/templates/`);
        const templates = await response.json();
        
        const select = document.getElementById('templateSelect');
        select.innerHTML = '<option value="">Usar mensagem personalizada</option>' +
            templates.filter(t => t.ativo).map(t => `<option value="${t.nome}">${t.nome}</option>`).join('');
    } catch (error) {
        console.error('Erro ao carregar templates:', error);
    }
}

async function carregarListaTemplates() {
    const lista = document.getElementById('templatesList');
    lista.innerHTML = '<div class="loading"><div class="spinner"></div>Carregando...</div>';
    
    try {
        // Busca todos os templates (ativos e inativos)
        const response = await fetch(`${API_URL}/templates/`);
        const templates = await response.json();
        
        if (templates.length === 0) {
            lista.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="file-text" style="width: 48px; height: 48px;"></i>
                    <p>Nenhum template cadastrado</p>
                    <button class="btn btn-primary" onclick="abrirModalNovoTemplate()" style="margin-top: 16px;">
                        <i data-lucide="plus"></i>
                        <span>Criar Primeiro Template</span>
                    </button>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        lista.innerHTML = templates.map(t => `
            <div class="template-card">
                <div class="template-card-header">
                    <h3 class="template-card-title">${t.nome}</h3>
                    <div class="template-card-actions">
                        <button class="btn-icon" onclick="editarTemplate('${t.nome}')" title="Editar">
                            <i data-lucide="edit-2" style="width: 16px; height: 16px;"></i>
                        </button>
                        <button class="btn-icon danger" onclick="confirmarDeletarTemplate('${t.nome}')" title="Excluir">
                            <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
                        </button>
                    </div>
                </div>
                <div class="template-card-body">${t.template_text}</div>
                <div class="template-card-footer">
                    <span>Variáveis: ${t.variaveis || 'nome, valor, dia_vencimento, data_vencimento, descricao'}</span>
                    <span class="template-status ${t.ativo ? 'ativo' : 'inativo'}">
                        <i data-lucide="${t.ativo ? 'check-circle' : 'circle'}" style="width: 14px; height: 14px;"></i>
                        ${t.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </div>
            </div>
        `).join('');
        
        lucide.createIcons();
    } catch (error) {
        lista.innerHTML = `<div class="result-box error">Erro: ${error.message}</div>`;
        showToast('Erro', 'Não foi possível carregar os templates', 'error');
    }
}

// CRUD Functions
function abrirModalNovoTemplate() {
    document.getElementById('modalTemplateTitle').textContent = 'Novo Template';
    document.getElementById('templateIdEdit').value = '';
    document.getElementById('templateNomeOriginal').value = '';
    document.getElementById('templateNome').value = '';
    document.getElementById('templateTexto').value = '';
    document.getElementById('templateVariaveis').value = '';
    document.getElementById('templateAtivo').checked = true;
    document.getElementById('templateAtivoGroup').style.display = 'none';
    document.getElementById('modalTemplate').style.display = 'flex';
    lucide.createIcons();
}

async function editarTemplate(nomeTemplate) {
    try {
        const response = await fetch(`${API_URL}/templates/${encodeURIComponent(nomeTemplate)}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showToast('Erro', 'Template não encontrado no banco de dados', 'error');
                carregarListaTemplates(); // Recarrega a lista
                return;
            }
            throw new Error('Erro ao carregar template');
        }
        
        const template = await response.json();
        
        document.getElementById('modalTemplateTitle').textContent = 'Editar Template';
        document.getElementById('templateIdEdit').value = template.id;
        document.getElementById('templateNomeOriginal').value = template.nome;
        document.getElementById('templateNome').value = template.nome;
        document.getElementById('templateNome').disabled = true; // Não permite editar o nome
        document.getElementById('templateTexto').value = template.template_text;
        document.getElementById('templateVariaveis').value = template.variaveis || '';
        document.getElementById('templateAtivo').checked = template.ativo;
        document.getElementById('templateAtivoGroup').style.display = 'block';
        document.getElementById('modalTemplate').style.display = 'flex';
        lucide.createIcons();
    } catch (error) {
        console.error('Erro ao carregar template:', error);
        showToast('Erro', error.message || 'Não foi possível carregar o template', 'error');
    }
}

function fecharModalTemplate() {
    document.getElementById('modalTemplate').style.display = 'none';
    document.getElementById('templateNome').disabled = false;
}

async function salvarTemplate() {
    const templateId = document.getElementById('templateIdEdit').value;
    const nomeOriginal = document.getElementById('templateNomeOriginal').value;
    const nome = document.getElementById('templateNome').value.trim();
    const texto = document.getElementById('templateTexto').value.trim();
    const variaveis = document.getElementById('templateVariaveis').value.trim();
    const ativo = document.getElementById('templateAtivo').checked;
    
    // Validações
    if (!nome) {
        showToast('Atenção', 'Digite o nome do template', 'info');
        document.getElementById('templateNome').focus();
        return;
    }
    
    if (!texto) {
        showToast('Atenção', 'Digite o texto do template', 'info');
        document.getElementById('templateTexto').focus();
        return;
    }
    
    try {
        let response;
        
        if (templateId) {
            // Atualizar template existente
            console.log('Atualizando template:', nomeOriginal);
            response = await fetch(`${API_URL}/templates/${encodeURIComponent(nomeOriginal)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_text: texto,
                    variaveis: variaveis || null,
                    ativo: ativo
                })
            });
        } else {
            // Criar novo template
            console.log('Criando novo template:', nome);
            response = await fetch(`${API_URL}/templates/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nome: nome,
                    template_text: texto,
                    variaveis: variaveis || null
                })
            });
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao salvar template');
        }
        
        const resultado = await response.json();
        console.log('Template salvo:', resultado);
        
        showToast('Sucesso', `Template ${templateId ? 'atualizado' : 'criado'} com sucesso!`, 'success');
        fecharModalTemplate();
        carregarListaTemplates();
        carregarTemplates(); // Atualiza o select também
    } catch (error) {
        console.error('Erro ao salvar template:', error);
        showToast('Erro', error.message, 'error');
    }
}

async function confirmarDeletarTemplate(nomeTemplate) {
    if (!confirm(`Tem certeza que deseja excluir o template "${nomeTemplate}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/templates/${encodeURIComponent(nomeTemplate)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao excluir template');
        }
        
        showToast('Sucesso', 'Template excluído com sucesso!', 'success');
        
        // Remove o card da tela imediatamente
        const templateCards = document.querySelectorAll('.template-card');
        templateCards.forEach(card => {
            if (card.querySelector('.template-card-title').textContent === nomeTemplate) {
                card.style.opacity = '0';
                card.style.transform = 'translateX(-20px)';
                setTimeout(() => card.remove(), 300);
            }
        });
        
        carregarTemplates(); // Atualiza o select
    } catch (error) {
        showToast('Erro', error.message, 'error');
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
        showToast('Atenção', 'Selecione um template primeiro', 'info');
        return;
    }
    
    if (clientesSelecionados.size === 0) {
        showToast('Atenção', 'Selecione pelo menos um cliente para preview', 'info');
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
        showToast('Preview gerado', 'Confira a mensagem abaixo', 'success');
    } catch (error) {
        showToast('Erro', 'Não foi possível gerar o preview: ' + error.message, 'error');
    }
}

// ========== ENVIO EM LOTE ==========
// Controle de debounce da busca
// ========== BUSCA DE CLIENTES (DEBOUNCE) ==========
let buscaTimer = null;
let ultimaQueryBuscada = '';

function buscarClientesDebounced() {
    const input = document.getElementById('searchClientes');
    const termo = input.value.trim();

    // Limpa resultados se apagou tudo ou menos de 2 chars
    if (termo.length < 2) {
        document.getElementById('clientesLista').innerHTML = `<div class="empty-state">\n            <i data-lucide="users" style="width:48px;height:48px;"></i>\n            <p>Digite ao menos 2 letras para buscar</p>\n        </div>`;
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        return;
    }

    // Debounce
    if (buscaTimer) clearTimeout(buscaTimer);
    document.getElementById('clientesLista').innerHTML = '<div class="loading"><div class="spinner"></div><p>Buscando...</p></div>';

    buscaTimer = setTimeout(async () => {
        // Evita requisição repetida igual à última
        if (termo === ultimaQueryBuscada) return;
        ultimaQueryBuscada = termo;

        try {
            const resp = await fetch(`${API_URL}/clientes/?nome=${encodeURIComponent(termo)}&limit=200`);
            const clientes = await resp.json();
            todosClientes = clientes;
            renderizarClientes(clientes);

            // Atualiza indicador discreto (sem toasts)
            atualizaBadgeResultadoBusca(clientes.length, termo);
        } catch (e) {
            document.getElementById('clientesLista').innerHTML = `<div class=\"empty-state\">\n                <i data-lucide=\"alert-circle\" style=\"width:48px;height:48px;color:var(--danger-500);\"></i>\n                <p>Erro ao buscar: ${e.message}</p>\n            </div>`;
            if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        }
    }, 400); // 400ms debounce
}

// Garante que chamadas antigas a buscarClientes usem a nova função
window.buscarClientes = buscarClientesDebounced;

function atualizaBadgeResultadoBusca(qtd, termo) {
    let badge = document.getElementById('searchFeedbackBadge');
    if (!badge) {
        const grupo = document.querySelector('.form-group .search-box');
        if (!grupo) return;
        badge = document.createElement('div');
        badge.id = 'searchFeedbackBadge';
        badge.style.marginTop = '8px';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = '600';
        badge.style.color = 'var(--gray-600)';
        grupo.parentElement.appendChild(badge);
    }
    if (qtd === 0) {
        badge.innerHTML = `Nenhum resultado para <strong>${termo}</strong>`;
    } else {
        badge.innerHTML = `${qtd} resultado${qtd>1?'s':''} para <strong>${termo}</strong>`;
    }
}

    // ========== ENVIO EM LOTE ==========
    async function enviarLote() {
        if (clientesSelecionados.size === 0) {
            showToast('Atenção', 'Selecione pelo menos um cliente!', 'info');
            return;
        }
        const mensagemPadrao = document.getElementById('mensagemPadrao').value.trim();
        const templateName = document.getElementById('templateSelect').value;
        const tipo = document.getElementById('tipoCobranca').value;
        if (!mensagemPadrao && !templateName) {
            showToast('Atenção', 'Digite uma mensagem ou selecione um template!', 'info');
            return;
        }
        const variaveisExtras = {};
        const valor = document.getElementById('var_valor').value.trim();
        const diaVencimento = document.getElementById('var_dia_vencimento').value.trim();
        const dataVencimento = document.getElementById('var_data_vencimento').value.trim();
        const descricao = document.getElementById('var_descricao').value.trim();
        if (valor) variaveisExtras.valor = valor;
        if (diaVencimento) variaveisExtras.dia_vencimento = diaVencimento;
        if (dataVencimento) variaveisExtras.data_vencimento = dataVencimento;
        if (descricao) variaveisExtras.descricao = descricao;
        if (!confirm(`Confirma envio para ${clientesSelecionados.size} cliente(s)?`)) return;
        const resultBox = document.getElementById('resultBox');
        resultBox.innerHTML = '<div class="loading"><div class="spinner"></div><p>Enviando mensagens...</p></div>';
        resultBox.style.display = 'block';
        showToast('Enviando', `Processando ${clientesSelecionados.size} mensagens...`, 'info');
        try {
            const payload = {
                clientes_ids: Array.from(clientesSelecionados),
                tipo: tipo,
                mensagem_padrao: templateName ? null : (mensagemPadrao || null),
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
                            <span class="badge badge-${d.status === 'enviado' ? 'success' : 'error'}">${d.status}</span>
                            ${d.erro ? `<br><small style="color: #721c24;">Erro: ${d.erro}</small>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
            if (resultado.erros === 0) {
                showToast('Sucesso Total!', `${resultado.enviados} mensagens enviadas com sucesso`, 'success');
                setTimeout(() => {
                    limparFormulario();
                }, 3000);
            } else if (resultado.enviados > 0) {
                showToast('Concluído com Erros', `${resultado.enviados} enviadas, ${resultado.erros} com erro`, 'error');
            } else {
                showToast('Falha no Envio', 'Nenhuma mensagem foi enviada', 'error');
            }
        } catch (error) {
            resultBox.className = 'result-box error';
            resultBox.innerHTML = `<h3>Erro no Envio</h3><p>${error.message}</p>`;
            showToast('Erro Crítico', 'Não foi possível realizar o envio', 'error');
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
    showToast('Formulário limpo', 'Campos resetados com sucesso', 'info');
}

// ========== DASHBOARD ==========
async function carregarDashboard() {
    const statsGrid = document.getElementById('statsGrid');
    const atividadesDiv = document.getElementById('atividadesRecentes');
    const filtroSelect = document.getElementById('filtroTipoAtividades');
    const tipoFiltro = filtroSelect ? filtroSelect.value : 'todos';
    
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
        
        // Carregar atividades com filtro se aplicável
        const queryTipo = tipoFiltro && tipoFiltro !== 'todos' ? `&tipo=${encodeURIComponent(tipoFiltro)}` : '';
        const atividadesResponse = await fetch(`${API_URL}/dashboard/atividades-recentes?limit=10${queryTipo}`);
        const atividades = await atividadesResponse.json();
        
        if (atividades.atividades && atividades.atividades.length > 0) {
            atividadesDiv.innerHTML = atividades.atividades.map(a => `
                <div class="result-item">
                    <span class="badge badge-${a.status === 'enviado' ? 'success' : 'warning'}">
                        ${a.tipo}
                    </span>
                    <strong>${a.cliente}</strong> - ${a.preview}
                    <br><small style="color: #7f8c8d;">${new Date(a.data).toLocaleString('pt-BR')}</small>
                </div>
            `).join('');
        } else {
            atividadesDiv.innerHTML = `<div class="empty-state">
                <i data-lucide="inbox" style="width: 48px; height: 48px;"></i>
                <p>Nenhuma atividade recente</p>
            </div>`;
        }
        
        lucide.createIcons();
        
    } catch (error) {
        statsGrid.innerHTML = `<div class="empty-state">
            <i data-lucide="alert-circle" style="width: 48px; height: 48px; color: var(--danger-500);"></i>
            <p>Erro ao carregar estatísticas: ${error.message}</p>
        </div>`;
        atividadesDiv.innerHTML = `<div class="empty-state">
            <i data-lucide="alert-circle" style="width: 48px; height: 48px; color: var(--danger-500);"></i>
            <p>Erro ao carregar atividades: ${error.message}</p>
        </div>`;
        lucide.createIcons();
        showToast('Erro', 'Não foi possível carregar o dashboard', 'error');
    }
}

// Atualiza somente atividades quando muda o filtro
function atualizarFiltroAtividades() {
    // Recarrega somente a lista de atividades sem refazer stats
    const atividadesDiv = document.getElementById('atividadesRecentes');
    atividadesDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Carregando...</p></div>';
    
    // Obter valores dos filtros
    const filtroTipo = document.getElementById('filtroTipoAtividades').value;
    const filtroMes = document.getElementById('filtroMesAtividades').value;
    const filtroAno = document.getElementById('filtroAnoAtividades').value;
    
    // Construir query string
    let queryParams = 'limit=50';
    if (filtroTipo && filtroTipo !== 'todos') {
        queryParams += `&tipo=${encodeURIComponent(filtroTipo)}`;
    }
    if (filtroMes && filtroAno) {
        queryParams += `&mes=${encodeURIComponent(filtroMes)}&ano=${encodeURIComponent(filtroAno)}`;
    }
    
    fetch(`${API_URL}/dashboard/atividades-recentes?${queryParams}`)
        .then(r => r.json())
        .then(atividades => {
            if (atividades.atividades && atividades.atividades.length > 0) {
                atividadesDiv.innerHTML = atividades.atividades.map(a => `
                    <div class="result-item">
                        <span class="badge badge-${a.status === 'enviado' ? 'success' : 'warning'}">
                            ${a.tipo}
                        </span>
                        <strong>${a.cliente}</strong> - ${a.preview}
                        <br><small style="color:#7f8c8d;">${new Date(a.data).toLocaleString('pt-BR')}</small>
                    </div>
                `).join('');
            } else {
                atividadesDiv.innerHTML = `<div class="empty-state">
                    <i data-lucide="inbox" style="width:48px;height:48px;"></i>
                    <p>Nenhuma atividade encontrada para o período selecionado</p>
                </div>`;
            }
            if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        })
        .catch(err => {
            atividadesDiv.innerHTML = `<div class="empty-state">
                <i data-lucide="alert-circle" style="width:48px;height:48px;color:var(--danger-500);"></i>
                <p>Erro ao carregar atividades: ${err.message}</p>
            </div>`;
            if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        });
}
