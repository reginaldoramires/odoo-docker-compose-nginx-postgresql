# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Integração Chatwoot
    chatwoot_conversation_ids = fields.One2many('chatwoot.conversation', 'lead_id',
                                                string='Chatwoot Conversations')
    chatwoot_conversation_count = fields.Integer(string='Chatwoot Conversations',
                                                 compute='_compute_chatwoot_count')

    @api.depends('chatwoot_conversation_ids')
    def _compute_chatwoot_count(self):
        """Computa contadores Chatwoot"""
        for lead in self:
            lead.chatwoot_conversation_count = len(lead.chatwoot_conversation_ids)

    def action_view_chatwoot_conversations(self):
        """Visualiza conversas Chatwoot"""
        self.ensure_one()

        return {
            'name': _('Chatwoot Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id, 'create': False},
        }
