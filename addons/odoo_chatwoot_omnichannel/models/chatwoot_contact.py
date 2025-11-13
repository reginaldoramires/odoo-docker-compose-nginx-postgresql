# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootContact(models.Model):
    _name = 'chatwoot.contact'
    _description = 'Chatwoot Contact'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    contact_id = fields.Integer(string='Contact ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account',
                                  required=True, ondelete='cascade')

    # Informações de contato
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='Phone Number')
    avatar_url = fields.Char(string='Avatar URL')
    thumbnail = fields.Char(string='Thumbnail')

    # Informações adicionais
    identifier = fields.Char(string='Identifier')
    additional_attributes = fields.Text(string='Additional Attributes')
    custom_attributes = fields.Text(string='Custom Attributes')

    # Social profiles
    social_profiles = fields.Text(string='Social Profiles')

    # Timestamps
    created_at = fields.Datetime(string='Created At')
    last_activity_at = fields.Datetime(string='Last Activity At')

    # Estatísticas
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')

    # Relacionamentos
    conversation_ids = fields.One2many('chatwoot.conversation', 'contact_id',
                                       string='Conversations')

    # Integração Odoo
    partner_id = fields.Many2one('res.partner', string='Odoo Partner',
                                  help='Parceiro Odoo vinculado')

    _sql_constraints = [
        ('contact_id_account_unique', 'unique(contact_id, account_id)',
         'Contact ID must be unique per account!'),
    ]

    @api.depends('conversation_ids')
    def _compute_counts(self):
        """Computa contadores"""
        for record in self:
            record.conversation_count = len(record.conversation_ids)

    @api.model
    def create_or_update_from_chatwoot(self, account, data):
        """Cria ou atualiza contato a partir de dados do Chatwoot"""
        contact_id = data.get('id')
        existing = self.search([
            ('contact_id', '=', contact_id),
            ('account_id', '=', account.id)
        ], limit=1)

        # Nome padrão se não fornecido
        name = data.get('name') or data.get('email') or data.get('phone_number') or f"Contact {contact_id}"

        values = {
            'name': name,
            'contact_id': contact_id,
            'account_id': account.id,
            'email': data.get('email'),
            'phone_number': data.get('phone_number'),
            'avatar_url': data.get('avatar_url'),
            'thumbnail': data.get('thumbnail'),
            'identifier': data.get('identifier'),
            'additional_attributes': str(data.get('additional_attributes', {})),
            'custom_attributes': str(data.get('custom_attributes', {})),
            'social_profiles': str(data.get('social_profiles', {})),
            'created_at': data.get('created_at'),
            'last_activity_at': data.get('last_activity_at'),
        }

        if existing:
            existing.write(values)
            contact = existing
        else:
            contact = self.create(values)

        # Auto-cria partner se configurado
        if account.auto_create_partner and not contact.partner_id:
            contact._create_partner()

        return contact

    def _create_partner(self):
        """Cria parceiro no Odoo"""
        self.ensure_one()

        # Verifica se já existe parceiro com mesmo email
        partner = None
        if self.email:
            partner = self.env['res.partner'].search([
                ('email', '=', self.email)
            ], limit=1)

        if not partner and self.phone_number:
            partner = self.env['res.partner'].search([
                ('phone', '=', self.phone_number)
            ], limit=1)

        if not partner:
            # Cria novo parceiro
            partner_vals = {
                'name': self.name,
                'email': self.email,
                'phone': self.phone_number,
                'comment': f"Criado automaticamente via Chatwoot (Contact ID: {self.contact_id})",
            }

            partner = self.env['res.partner'].create(partner_vals)
            _logger.info(f"Parceiro {partner.id} criado para contato Chatwoot {self.contact_id}")

        self.partner_id = partner.id
        return partner

    def action_sync_conversations(self):
        """Sincroniza conversas deste contato"""
        self.ensure_one()
        # Implementar se necessário
        pass

    def action_view_conversations(self):
        """Abre visualização de conversas"""
        self.ensure_one()
        return {
            'name': _('Conversations'),
            'type': 'ir.actions.act_window',
            'res_model': 'chatwoot.conversation',
            'view_mode': 'tree,form',
            'domain': [('contact_id', '=', self.id)],
            'context': {'default_contact_id': self.id},
        }

    def action_open_partner(self):
        """Abre o parceiro Odoo"""
        self.ensure_one()
        if not self.partner_id:
            self._create_partner()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
