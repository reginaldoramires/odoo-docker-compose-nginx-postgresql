# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Integração Chatwoot
    chatwoot_contact_ids = fields.One2many('chatwoot.contact', 'partner_id',
                                           string='Chatwoot Contacts')
    chatwoot_contact_count = fields.Integer(string='Chatwoot Contacts',
                                            compute='_compute_chatwoot_counts')
    chatwoot_conversation_count = fields.Integer(string='Chatwoot Conversations',
                                                 compute='_compute_chatwoot_counts')

    @api.depends('chatwoot_contact_ids')
    def _compute_chatwoot_counts(self):
        """Computa contadores Chatwoot"""
        for partner in self:
            partner.chatwoot_contact_count = len(partner.chatwoot_contact_ids)
            partner.chatwoot_conversation_count = sum(
                contact.conversation_count for contact in partner.chatwoot_contact_ids
            )

    def action_view_chatwoot_conversations(self):
        """Visualiza conversas Chatwoot"""
        self.ensure_one()
        contact_ids = self.chatwoot_contact_ids.ids

        return {
            'name': _('Chatwoot Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('contact_id', 'in', contact_ids)],
            'context': {'create': False},
        }
