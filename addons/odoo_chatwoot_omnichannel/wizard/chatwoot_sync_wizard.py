# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChatwootSyncWizard(models.TransientModel):
    _name = 'chatwoot.sync.wizard'
    _description = 'Chatwoot Sync Wizard'

    account_id = fields.Many2one('chatwoot.account', string='Account', required=True)

    sync_inboxes = fields.Boolean(string='Sync Inboxes', default=True)
    sync_agents = fields.Boolean(string='Sync Agents', default=True)
    sync_teams = fields.Boolean(string='Sync Teams', default=True)
    sync_labels = fields.Boolean(string='Sync Labels', default=True)
    sync_contacts = fields.Boolean(string='Sync Contacts', default=True)
    sync_conversations = fields.Boolean(string='Sync Conversations', default=True)

    conversation_status = fields.Selection([
        ('all', 'All'),
        ('open', 'Open Only'),
        ('resolved', 'Resolved Only'),
    ], string='Conversation Status', default='open')

    @api.model
    def default_get(self, fields_list):
        """Define valores padrão"""
        res = super().default_get(fields_list)

        # Pega conta ativa
        account = self.env['chatwoot.account'].search([('active', '=', True)], limit=1)
        if account:
            res['account_id'] = account.id

        return res

    def action_sync(self):
        """Executa sincronização"""
        self.ensure_one()

        if not self.account_id:
            raise UserError(_('Selecione uma conta'))

        try:
            _logger.info(f"Iniciando sincronização manual da conta {self.account_id.name}")

            if self.sync_inboxes:
                self.account_id.action_sync_inboxes()

            if self.sync_agents:
                self.account_id.action_sync_agents()

            if self.sync_teams:
                self.account_id.action_sync_teams()

            if self.sync_labels:
                self.account_id.action_sync_labels()

            if self.sync_contacts:
                self.account_id.action_sync_contacts()

            if self.sync_conversations:
                self.account_id.action_sync_conversations()

            self.account_id.last_sync_date = fields.Datetime.now()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Sincronização concluída com sucesso!'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Erro durante sincronização: {str(e)}")
            raise UserError(_('Erro durante sincronização: %s') % str(e))
