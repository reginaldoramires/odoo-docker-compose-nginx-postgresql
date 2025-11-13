# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import json

_logger = logging.getLogger(__name__)


class ChatwootWebhook(models.Model):
    _name = 'chatwoot.webhook'
    _description = 'Chatwoot Webhook Log'
    _order = 'create_date desc'

    name = fields.Char(string='Event', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account', ondelete='cascade')

    event_type = fields.Selection([
        ('conversation_created', 'Conversation Created'),
        ('conversation_updated', 'Conversation Updated'),
        ('conversation_status_changed', 'Conversation Status Changed'),
        ('message_created', 'Message Created'),
        ('message_updated', 'Message Updated'),
        ('contact_created', 'Contact Created'),
        ('contact_updated', 'Contact Updated'),
        ('conversation_resolved', 'Conversation Resolved'),
        ('conversation_opened', 'Conversation Opened'),
    ], string='Event Type', required=True)

    # Payload
    payload = fields.Text(string='Payload', required=True)
    processed = fields.Boolean(string='Processed', default=False)
    error = fields.Text(string='Error Message')

    # Metadata
    conversation_id = fields.Many2one('chatwoot.conversation', string='Conversation')
    contact_id = fields.Many2one('chatwoot.contact', string='Contact')
    message_id = fields.Many2one('chatwoot.message', string='Message')

    @api.model
    def process_webhook(self, account, event_type, payload):
        """Processa webhook recebido do Chatwoot"""
        webhook = self.create({
            'name': event_type,
            'account_id': account.id if account else False,
            'event_type': event_type,
            'payload': json.dumps(payload),
        })

        try:
            _logger.info(f"Processando webhook: {event_type}")

            if event_type in ['conversation_created', 'conversation_updated',
                             'conversation_status_changed', 'conversation_resolved',
                             'conversation_opened']:
                webhook._process_conversation_event(account, payload)

            elif event_type in ['message_created', 'message_updated']:
                webhook._process_message_event(account, payload)

            elif event_type in ['contact_created', 'contact_updated']:
                webhook._process_contact_event(account, payload)

            webhook.processed = True
            _logger.info(f"Webhook {event_type} processado com sucesso")

        except Exception as e:
            webhook.error = str(e)
            _logger.error(f"Erro ao processar webhook {event_type}: {str(e)}")

        return webhook

    def _process_conversation_event(self, account, payload):
        """Processa evento de conversa"""
        conv_data = payload.get('conversation')
        if not conv_data:
            return

        conversation = self.env['chatwoot.conversation'].create_or_update_from_chatwoot(
            account, conv_data
        )

        self.conversation_id = conversation.id

        # Processa mensagens se incluídas
        if conv_data.get('messages'):
            for msg_data in conv_data['messages']:
                self.env['chatwoot.message'].create_or_update_from_chatwoot(
                    account, conversation, msg_data
                )

    def _process_message_event(self, account, payload):
        """Processa evento de mensagem"""
        msg_data = payload.get('message')
        if not msg_data:
            return

        # Busca ou cria conversa
        conv_id = payload.get('conversation', {}).get('id')
        if not conv_id:
            return

        conversation = self.env['chatwoot.conversation'].search([
            ('conversation_id', '=', conv_id),
            ('account_id', '=', account.id)
        ], limit=1)

        if not conversation:
            # Sincroniza conversa
            conv_data = payload.get('conversation')
            if conv_data:
                conversation = self.env['chatwoot.conversation'].create_or_update_from_chatwoot(
                    account, conv_data
                )

        if conversation:
            message = self.env['chatwoot.message'].create_or_update_from_chatwoot(
                account, conversation, msg_data
            )
            self.message_id = message.id
            self.conversation_id = conversation.id

    def _process_contact_event(self, account, payload):
        """Processa evento de contato"""
        contact_data = payload.get('contact')
        if not contact_data:
            return

        contact = self.env['chatwoot.contact'].create_or_update_from_chatwoot(
            account, contact_data
        )

        self.contact_id = contact.id

    def action_reprocess(self):
        """Reprocessa webhook"""
        self.ensure_one()
        if not self.account_id:
            return

        try:
            payload = json.loads(self.payload)
            self.processed = False
            self.error = False

            if self.event_type in ['conversation_created', 'conversation_updated',
                                  'conversation_status_changed']:
                self._process_conversation_event(self.account_id, payload)

            elif self.event_type in ['message_created', 'message_updated']:
                self._process_message_event(self.account_id, payload)

            elif self.event_type in ['contact_created', 'contact_updated']:
                self._process_contact_event(self.account_id, payload)

            self.processed = True

        except Exception as e:
            self.error = str(e)
            _logger.error(f"Erro ao reprocessar webhook: {str(e)}")
