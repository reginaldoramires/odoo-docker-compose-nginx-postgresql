# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ChatwootMainController(http.Controller):

    @http.route('/chatwoot/dashboard', type='http', auth='user', website=True)
    def chatwoot_dashboard(self, **kwargs):
        """Dashboard principal do Chatwoot"""
        # Busca configuração da conta
        account = request.env['chatwoot.account'].search([('active', '=', True)], limit=1)

        # Estatísticas
        open_conversations = request.env['chatwoot.conversation'].search_count([
            ('status', '=', 'open'),
            ('account_id', '=', account.id) if account else ('id', '=', False)
        ])

        pending_conversations = request.env['chatwoot.conversation'].search_count([
            ('status', '=', 'pending'),
            ('account_id', '=', account.id) if account else ('id', '=', False)
        ])

        total_contacts = request.env['chatwoot.contact'].search_count([
            ('account_id', '=', account.id) if account else ('id', '=', False)
        ])

        values = {
            'account': account,
            'open_conversations': open_conversations,
            'pending_conversations': pending_conversations,
            'total_contacts': total_contacts,
        }

        return request.render('odoo_chatwoot_omnichannel.chatwoot_dashboard_template', values)

    @http.route('/chatwoot/conversation/<int:conversation_id>', type='http', auth='user', website=True)
    def chatwoot_conversation_view(self, conversation_id, **kwargs):
        """Visualização detalhada de conversa"""
        conversation = request.env['chatwoot.conversation'].browse(conversation_id)

        if not conversation.exists():
            return request.not_found()

        values = {
            'conversation': conversation,
            'messages': conversation.message_ids.sorted(key=lambda m: m.created_at),
        }

        return request.render('odoo_chatwoot_omnichannel.chatwoot_conversation_template', values)

    @http.route('/chatwoot/api/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, conversation_id, content, **kwargs):
        """API para enviar mensagem"""
        try:
            conversation = request.env['chatwoot.conversation'].browse(conversation_id)

            if not conversation.exists():
                return {'success': False, 'error': 'Conversation not found'}

            result = conversation.action_send_message(
                content=content,
                message_type='outgoing',
                private=kwargs.get('private', False)
            )

            return {'success': True, 'data': result}

        except Exception as e:
            _logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chatwoot/api/change_status', type='json', auth='user', methods=['POST'])
    def change_conversation_status(self, conversation_id, status, **kwargs):
        """API para alterar status da conversa"""
        try:
            conversation = request.env['chatwoot.conversation'].browse(conversation_id)

            if not conversation.exists():
                return {'success': False, 'error': 'Conversation not found'}

            conversation._change_status(status)

            return {'success': True}

        except Exception as e:
            _logger.error(f"Erro ao alterar status: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/chatwoot/api/assign_agent', type='json', auth='user', methods=['POST'])
    def assign_agent(self, conversation_id, agent_id, **kwargs):
        """API para atribuir agente"""
        try:
            conversation = request.env['chatwoot.conversation'].browse(conversation_id)

            if not conversation.exists():
                return {'success': False, 'error': 'Conversation not found'}

            conversation.action_assign_agent(agent_id)

            return {'success': True}

        except Exception as e:
            _logger.error(f"Erro ao atribuir agente: {str(e)}")
            return {'success': False, 'error': str(e)}
