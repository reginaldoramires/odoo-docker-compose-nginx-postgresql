# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ChatwootAssignConversationWizard(models.TransientModel):
    _name = 'chatwoot.assign.conversation.wizard'
    _description = 'Assign Conversation Wizard'

    conversation_ids = fields.Many2many('chatwoot.conversation', string='Conversations')

    assign_type = fields.Selection([
        ('agent', 'Assign to Agent'),
        ('team', 'Assign to Team'),
    ], string='Assign Type', required=True, default='agent')

    agent_id = fields.Many2one('chatwoot.agent', string='Agent')
    team_id = fields.Many2one('chatwoot.team', string='Team')

    @api.model
    def default_get(self, fields_list):
        """Define valores padrão"""
        res = super().default_get(fields_list)

        # Pega conversas do contexto
        if self.env.context.get('active_model') == 'chatwoot.conversation':
            conversation_ids = self.env.context.get('active_ids', [])
            res['conversation_ids'] = [(6, 0, conversation_ids)]

        return res

    def action_assign(self):
        """Executa atribuição"""
        self.ensure_one()

        if not self.conversation_ids:
            raise UserError(_('Selecione pelo menos uma conversa'))

        if self.assign_type == 'agent' and not self.agent_id:
            raise UserError(_('Selecione um agente'))

        if self.assign_type == 'team' and not self.team_id:
            raise UserError(_('Selecione um time'))

        success_count = 0
        error_count = 0

        for conversation in self.conversation_ids:
            try:
                if self.assign_type == 'agent':
                    conversation.action_assign_agent(self.agent_id.id)
                else:
                    conversation.action_assign_team(self.team_id.id)

                success_count += 1

            except Exception as e:
                error_count += 1
                continue

        message = _('%s conversas atribuídas com sucesso') % success_count
        if error_count > 0:
            message += _(', %s erros') % error_count

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': False,
            }
        }
