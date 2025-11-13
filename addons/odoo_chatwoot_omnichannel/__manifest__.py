# -*- coding: utf-8 -*-
{
    'name': 'Odoo Chatwoot Omnichannel',
    'version': '1.0.0',
    'category': 'Customer Relationship',
    'summary': 'Integração completa de omnichannel com Chatwoot',
    'description': """
        Odoo Chatwoot Omnichannel Integration
        ======================================

        Solução completa de omnichannel integrando Odoo e Chatwoot via API REST.

        Funcionalidades Principais:
        ---------------------------
        * Gerenciamento unificado de conversas
        * Suporte a múltiplos canais (chat, e-mail, redes sociais)
        * Atribuição automática de tickets
        * Painel de controle do agente
        * Histórico completo de interações
        * Sincronização em tempo real
        * Autenticação segura entre serviços
        * Monitoramento de desempenho

        Requisitos:
        -----------
        * Chatwoot instalado e configurado
        * Acesso à API do Chatwoot
        * Redis para sincronização em tempo real (opcional)
    """,
    'author': 'Odoo Chatwoot Integration Team',
    'website': 'https://github.com/reginaldoramires/odoo-docker-compose-nginx-postgresql',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'crm',
        'contacts',
        'website',
        'portal',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/chatwoot_channel_data.xml',
        'data/ir_cron_data.xml',
        'views/chatwoot_account_views.xml',
        'views/chatwoot_inbox_views.xml',
        'views/chatwoot_agent_views.xml',
        'views/chatwoot_conversation_views.xml',
        'views/chatwoot_message_views.xml',
        'views/chatwoot_contact_views.xml',
        'views/chatwoot_label_views.xml',
        'views/chatwoot_team_views.xml',
        'views/chatwoot_dashboard_views.xml',
        'views/chatwoot_settings_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/menu_views.xml',
        'wizard/chatwoot_sync_wizard_views.xml',
        'wizard/chatwoot_assign_conversation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_chatwoot_omnichannel/static/src/css/chatwoot_dashboard.css',
            'odoo_chatwoot_omnichannel/static/src/css/chatwoot_conversation.css',
            'odoo_chatwoot_omnichannel/static/src/js/chatwoot_dashboard.js',
            'odoo_chatwoot_omnichannel/static/src/js/chatwoot_conversation_widget.js',
            'odoo_chatwoot_omnichannel/static/src/js/chatwoot_realtime.js',
        ],
        'web.assets_frontend': [
            'odoo_chatwoot_omnichannel/static/src/css/chatwoot_widget.css',
            'odoo_chatwoot_omnichannel/static/src/js/chatwoot_widget.js',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
