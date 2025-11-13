# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootAgent(models.Model):
    _name = 'chatwoot.agent'
    _description = 'Chatwoot Agent'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    agent_id = fields.Integer(string='Agent ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account', required=True, ondelete='cascade')

    # Informações do agente
    email = fields.Char(string='Email')
    avatar_url = fields.Char(string='Avatar URL')
    role = fields.Selection([
        ('agent', 'Agent'),
        ('administrator', 'Administrator'),
    ], string='Role', default='agent')
    availability_status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
    ], string='Availability', default='offline')

    active = fields.Boolean(string='Active', default=True)
    confirmed = fields.Boolean(string='Confirmed', default=True)

    # Estatísticas
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')
    open_conversation_count = fields.Integer(string='Open Conversations', compute='_compute_counts')

    # Relacionamentos
    conversation_ids = fields.One2many('chatwoot.conversation', 'assignee_id', string='Assigned Conversations')
    team_ids = fields.Many2many('chatwoot.team', 'team_agent_rel', 'agent_id', 'team_id', string='Teams')
    inbox_ids = fields.Many2many('chatwoot.inbox', 'inbox_agent_rel', 'agent_id', 'inbox_id',
                                  string='Inboxes')

    # Integração Odoo
    user_id = fields.Many2one('res.users', string='Odoo User',
                              help='Usuário Odoo vinculado a este agente')

    _sql_constraints = [
        ('agent_id_account_unique', 'unique(agent_id, account_id)',
         'Agent ID must be unique per account!'),
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
        """Cria ou atualiza agente a partir de dados do Chatwoot"""
        agent_id = data.get('id')
        existing = self.search([
            ('agent_id', '=', agent_id),
            ('account_id', '=', account.id)
        ], limit=1)

        values = {
            'name': data.get('name') or data.get('email'),
            'agent_id': agent_id,
            'account_id': account.id,
            'email': data.get('email'),
            'avatar_url': data.get('avatar_url') or data.get('thumbnail'),
            'role': data.get('role', 'agent'),
            'availability_status': data.get('availability_status', 'offline'),
            'confirmed': data.get('confirmed', True),
        }

        # Tenta vincular com usuário Odoo pelo email
        if data.get('email') and not existing:
            user = self.env['res.users'].search([
                ('email', '=', data.get('email'))
            ], limit=1)
            if user:
                values['user_id'] = user.id

        if existing:
            existing.write(values)
            return existing
        else:
            return self.create(values)

    def action_view_conversations(self):
        """Abre visualização de conversas atribuídas"""
        self.ensure_one()
        return {
            'name': _('My Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('assignee_id', '=', self.id)],
            'context': {'default_assignee_id': self.id},
        }

    def action_set_availability(self, status):
        """Define status de disponibilidade"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)
            result = api.update_agent(self.agent_id, {
                'availability': status
            })

            self.availability_status = status

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Status atualizado para %s') % status,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Erro ao atualizar status: {str(e)}")
            raise

    def action_online(self):
        """Define agente como online"""
        return self.action_set_availability('online')

    def action_offline(self):
        """Define agente como offline"""
        return self.action_set_availability('offline')

    def action_busy(self):
        """Define agente como ocupado"""
        return self.action_set_availability('busy')
