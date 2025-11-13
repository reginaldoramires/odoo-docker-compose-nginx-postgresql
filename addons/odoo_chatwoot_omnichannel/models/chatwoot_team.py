# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootTeam(models.Model):
    _name = 'chatwoot.team'
    _description = 'Chatwoot Team'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    team_id = fields.Integer(string='Team ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account',
                                  required=True, ondelete='cascade')

    description = fields.Text(string='Description')
    allow_auto_assign = fields.Boolean(string='Allow Auto Assign', default=True)

    # Estatísticas
    agent_count = fields.Integer(string='Agents', compute='_compute_counts')
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')

    # Relacionamentos
    agent_ids = fields.Many2many('chatwoot.agent', 'team_agent_rel',
                                  'team_id', 'agent_id', string='Agents')
    conversation_ids = fields.One2many('chatwoot.conversation', 'team_id',
                                       string='Conversations')

    _sql_constraints = [
        ('team_id_account_unique', 'unique(team_id, account_id)',
         'Team ID must be unique per account!'),
    ]

    @api.depends('agent_ids', 'conversation_ids')
    def _compute_counts(self):
        """Computa contadores"""
        for record in self:
            record.agent_count = len(record.agent_ids)
            record.conversation_count = len(record.conversation_ids)

    @api.model
    def create_or_update_from_chatwoot(self, account, data):
        """Cria ou atualiza time a partir de dados do Chatwoot"""
        team_id = data.get('id')
        existing = self.search([
            ('team_id', '=', team_id),
            ('account_id', '=', account.id)
        ], limit=1)

        values = {
            'name': data.get('name'),
            'team_id': team_id,
            'account_id': account.id,
            'description': data.get('description'),
            'allow_auto_assign': data.get('allow_auto_assign', True),
        }

        if existing:
            existing.write(values)
            return existing
        else:
            return self.create(values)

    def action_view_conversations(self):
        """Abre visualização de conversas do time"""
        self.ensure_one()
        return {
            'name': _('Team Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('team_id', '=', self.id)],
            'context': {'default_team_id': self.id},
        }

    def action_view_agents(self):
        """Abre visualização de agentes do time"""
        self.ensure_one()
        return {
            'name': _('Team Agents'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.agent',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.agent_ids.ids)],
        }
