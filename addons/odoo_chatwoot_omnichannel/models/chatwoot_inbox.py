# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootInbox(models.Model):
    _name = 'chatwoot.inbox'
    _description = 'Chatwoot Inbox'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    inbox_id = fields.Integer(string='Inbox ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account', required=True, ondelete='cascade')

    # Configurações
    channel_type = fields.Selection([
        ('web', 'Website'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('twilio', 'Twilio SMS'),
        ('whatsapp', 'WhatsApp'),
        ('api', 'API'),
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('line', 'Line'),
        ('sms', 'SMS'),
    ], string='Channel Type', required=True)

    active = fields.Boolean(string='Active', default=True)
    avatar_url = fields.Char(string='Avatar URL')
    greeting_enabled = fields.Boolean(string='Greeting Enabled')
    greeting_message = fields.Text(string='Greeting Message')
    email_address = fields.Char(string='Email Address')
    phone_number = fields.Char(string='Phone Number')
    website_url = fields.Char(string='Website URL')

    # Configurações de canal
    enable_auto_assignment = fields.Boolean(string='Auto Assignment', default=True)
    allow_messages_after_resolved = fields.Boolean(string='Allow Messages After Resolved', default=True)
    enable_email_collect = fields.Boolean(string='Enable Email Collect Box', default=True)
    csat_survey_enabled = fields.Boolean(string='CSAT Survey Enabled', default=True)

    # Configurações de widget
    widget_color = fields.Char(string='Widget Color', default='#1f93ff')
    website_token = fields.Char(string='Website Token')
    hmac_token = fields.Char(string='HMAC Token')

    # Estatísticas
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')
    open_conversation_count = fields.Integer(string='Open Conversations', compute='_compute_counts')

    # Relacionamentos
    conversation_ids = fields.One2many('chatwoot.conversation', 'inbox_id', string='Conversations')
    agent_ids = fields.Many2many('chatwoot.agent', 'inbox_agent_rel', 'inbox_id', 'agent_id',
                                  string='Agents')

    # Odoo integration
    odoo_team_id = fields.Many2one('crm.team', string='Sales Team')

    _sql_constraints = [
        ('inbox_id_account_unique', 'unique(inbox_id, account_id)',
         'Inbox ID must be unique per account!'),
    ]

    @api.depends('conversation_ids')
    def _compute_counts(self):
        """Computa contadores"""
        for record in self:
            record.conversation_count = len(record.conversation_ids)
            record.open_conversation_count = len(
                record.conversation_ids.filtered(lambda c: c.status == 'open')
            )

    @api.model
    def create_or_update_from_chatwoot(self, account, data):
        """Cria ou atualiza inbox a partir de dados do Chatwoot"""
        inbox_id = data.get('id')
        existing = self.search([
            ('inbox_id', '=', inbox_id),
            ('account_id', '=', account.id)
        ], limit=1)

        values = {
            'name': data.get('name'),
            'inbox_id': inbox_id,
            'account_id': account.id,
            'channel_type': data.get('channel_type'),
            'avatar_url': data.get('avatar_url'),
            'greeting_enabled': data.get('greeting_enabled', False),
            'greeting_message': data.get('greeting_message'),
            'email_address': data.get('email_address'),
            'phone_number': data.get('phone_number'),
            'website_url': data.get('website_url'),
            'enable_auto_assignment': data.get('enable_auto_assignment', True),
            'allow_messages_after_resolved': data.get('allow_messages_after_resolved', True),
            'enable_email_collect': data.get('enable_email_collect', True),
            'csat_survey_enabled': data.get('csat_survey_enabled', True),
            'widget_color': data.get('widget_color', '#1f93ff'),
            'website_token': data.get('website_token'),
            'hmac_token': data.get('hmac_token'),
        }

        if existing:
            existing.write(values)
            return existing
        else:
            return self.create(values)

    def action_sync_conversations(self):
        """Sincroniza conversas desta inbox"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self.account_id)

        # Sincroniza conversas abertas
        open_conversations = api.get_conversations(status='open')
        for conv_data in open_conversations:
            if conv_data.get('inbox_id') == self.inbox_id:
                self.env['chatwoot.conversation'].create_or_update_from_chatwoot(
                    self.account_id, conv_data
                )

        # Sincroniza conversas resolvidas
        resolved_conversations = api.get_conversations(status='resolved')
        for conv_data in resolved_conversations:
            if conv_data.get('inbox_id') == self.inbox_id:
                self.env['chatwoot.conversation'].create_or_update_from_chatwoot(
                    self.account_id, conv_data
                )

        _logger.info(f"Sincronizadas conversas da inbox {self.name}")

    def action_view_conversations(self):
        """Abre visualização de conversas"""
        self.ensure_one()
        return {
            'name': _('Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('inbox_id', '=', self.id)],
            'context': {'default_inbox_id': self.id},
        }
