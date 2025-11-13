# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootLabel(models.Model):
    _name = 'chatwoot.label'
    _description = 'Chatwoot Label'
    _order = 'title'

    title = fields.Char(string='Title', required=True)
    label_id = fields.Integer(string='Label ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account',
                                  required=True, ondelete='cascade')

    description = fields.Text(string='Description')
    color = fields.Char(string='Color', default='#1f93ff')
    show_on_sidebar = fields.Boolean(string='Show on Sidebar', default=True)

    # Estatísticas
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')

    # Relacionamentos
    conversation_ids = fields.Many2many('chatwoot.conversation', 'conversation_label_rel',
                                        'label_id', 'conversation_id', string='Conversations')

    _sql_constraints = [
        ('label_id_account_unique', 'unique(label_id, account_id)',
         'Label ID must be unique per account!'),
        ('title_account_unique', 'unique(title, account_id)',
         'Label title must be unique per account!'),
    ]

    @api.depends('conversation_ids')
    def _compute_counts(self):
        """Computa contadores"""
        for record in self:
            record.conversation_count = len(record.conversation_ids)

    @api.model
    def create_or_update_from_chatwoot(self, account, data):
        """Cria ou atualiza label a partir de dados do Chatwoot"""
        label_id = data.get('id')
        existing = self.search([
            ('label_id', '=', label_id),
            ('account_id', '=', account.id)
        ], limit=1)

        values = {
            'title': data.get('title'),
            'label_id': label_id,
            'account_id': account.id,
            'description': data.get('description'),
            'color': data.get('color', '#1f93ff'),
            'show_on_sidebar': data.get('show_on_sidebar', True),
        }

        if existing:
            existing.write(values)
            return existing
        else:
            return self.create(values)

    def action_view_conversations(self):
        """Abre visualização de conversas com esta label"""
        self.ensure_one()
        return {
            'name': _('Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('label_ids', 'in', self.id)],
        }
