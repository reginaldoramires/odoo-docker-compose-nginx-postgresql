# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChatwootConversation(models.Model):
    _name = 'chatwoot.conversation'
    _description = 'Chatwoot Conversation'
    _order = 'last_activity_at desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Subject', compute='_compute_name', store=True)
    conversation_id = fields.Integer(string='Conversation ID', required=True)
    account_id = fields.Many2one('chatwoot.account', string='Account', required=True,
                                  ondelete='cascade', tracking=True)

    # Status e prioridade
    status = fields.Selection([
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('pending', 'Pending'),
        ('snoozed', 'Snoozed'),
    ], string='Status', default='open', required=True, tracking=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium', tracking=True)

    # Relacionamentos principais
    inbox_id = fields.Many2one('chatwoot.inbox', string='Inbox', required=True,
                               ondelete='cascade', tracking=True)
    contact_id = fields.Many2one('chatwoot.contact', string='Contact', required=True,
                                  ondelete='cascade', tracking=True)
    assignee_id = fields.Many2one('chatwoot.agent', string='Assigned To', tracking=True)
    team_id = fields.Many2one('chatwoot.team', string='Team', tracking=True)

    # Informações da conversa
    additional_attributes = fields.Text(string='Additional Attributes')
    can_reply = fields.Boolean(string='Can Reply', default=True)
    channel = fields.Char(string='Channel', related='inbox_id.channel_type', store=True)
    contact_last_seen_at = fields.Datetime(string='Contact Last Seen')
    timestamp = fields.Datetime(string='Created At', required=True)
    last_activity_at = fields.Datetime(string='Last Activity', required=True)

    # Contadores
    unread_count = fields.Integer(string='Unread Count', default=0)
    message_count = fields.Integer(string='Messages', compute='_compute_message_count', store=True)

    # Métricas
    first_reply_created_at = fields.Datetime(string='First Reply At')
    waiting_since = fields.Datetime(string='Waiting Since')

    # Labels e custom attributes
    label_ids = fields.Many2many('chatwoot.label', 'conversation_label_rel',
                                  'conversation_id', 'label_id', string='Labels')
    custom_attributes = fields.Text(string='Custom Attributes')

    # Mensagens
    message_ids = fields.One2many('chatwoot.message', 'conversation_id', string='Messages')

    # Integração com Odoo
    partner_id = fields.Many2one('res.partner', string='Partner',
                                  related='contact_id.partner_id', store=True)
    lead_id = fields.Many2one('crm.lead', string='Opportunity', tracking=True)

    # Rating/CSAT
    csat_rating = fields.Selection([
        ('1', '1 - Very Dissatisfied'),
        ('2', '2 - Dissatisfied'),
        ('3', '3 - Neutral'),
        ('4', '4 - Satisfied'),
        ('5', '5 - Very Satisfied'),
    ], string='CSAT Rating')
    csat_feedback = fields.Text(string='CSAT Feedback')

    _sql_constraints = [
        ('conversation_id_account_unique', 'unique(conversation_id, account_id)',
         'Conversation ID must be unique per account!'),
    ]

    @api.depends('contact_id.name', 'conversation_id')
    def _compute_name(self):
        """Computa nome da conversa"""
        for record in self:
            if record.contact_id:
                record.name = f"Conversation with {record.contact_id.name} (#{record.conversation_id})"
            else:
                record.name = f"Conversation #{record.conversation_id}"

    @api.depends('message_ids')
    def _compute_message_count(self):
        """Computa contagem de mensagens"""
        for record in self:
            record.message_count = len(record.message_ids)

    @api.model
    def create_or_update_from_chatwoot(self, account, data):
        """Cria ou atualiza conversa a partir de dados do Chatwoot"""
        conversation_id = data.get('id')
        existing = self.search([
            ('conversation_id', '=', conversation_id),
            ('account_id', '=', account.id)
        ], limit=1)

        # Busca ou cria inbox
        inbox_id_val = data.get('inbox_id')
        inbox = self.env['chatwoot.inbox'].search([
            ('inbox_id', '=', inbox_id_val),
            ('account_id', '=', account.id)
        ], limit=1)

        if not inbox:
            _logger.warning(f"Inbox {inbox_id_val} não encontrada, pulando conversa")
            return existing or False

        # Busca ou cria contato
        contact_data = data.get('meta', {}).get('sender') or data.get('contact')
        if not contact_data:
            _logger.warning(f"Contato não encontrado na conversa {conversation_id}")
            return existing or False

        contact = self.env['chatwoot.contact'].create_or_update_from_chatwoot(
            account, contact_data
        )

        # Busca agente atribuído
        assignee_id = None
        if data.get('meta', {}).get('assignee'):
            assignee_data = data['meta']['assignee']
            assignee = self.env['chatwoot.agent'].search([
                ('agent_id', '=', assignee_data.get('id')),
                ('account_id', '=', account.id)
            ], limit=1)
            if assignee:
                assignee_id = assignee.id

        # Busca time atribuído
        team_id = None
        if data.get('meta', {}).get('team'):
            team_data = data['meta']['team']
            team = self.env['chatwoot.team'].search([
                ('team_id', '=', team_data.get('id')),
                ('account_id', '=', account.id)
            ], limit=1)
            if team:
                team_id = team.id

        values = {
            'conversation_id': conversation_id,
            'account_id': account.id,
            'inbox_id': inbox.id,
            'contact_id': contact.id,
            'assignee_id': assignee_id,
            'team_id': team_id,
            'status': data.get('status', 'open'),
            'timestamp': data.get('created_at') or fields.Datetime.now(),
            'last_activity_at': data.get('last_activity_at') or data.get('created_at') or fields.Datetime.now(),
            'contact_last_seen_at': data.get('contact_last_seen_at'),
            'unread_count': data.get('unread_count', 0),
            'can_reply': data.get('can_reply', True),
            'additional_attributes': str(data.get('additional_attributes', {})),
            'custom_attributes': str(data.get('custom_attributes', {})),
            'first_reply_created_at': data.get('first_reply_created_at'),
            'waiting_since': data.get('waiting_since'),
        }

        # Processa labels
        if data.get('labels'):
            label_ids = []
            for label_name in data['labels']:
                label = self.env['chatwoot.label'].search([
                    ('title', '=', label_name),
                    ('account_id', '=', account.id)
                ], limit=1)
                if label:
                    label_ids.append(label.id)
            if label_ids:
                values['label_ids'] = [(6, 0, label_ids)]

        if existing:
            existing.write(values)
            conversation = existing
        else:
            conversation = self.create(values)

        # Sincroniza mensagens se necessário
        if data.get('messages'):
            for msg_data in data['messages']:
                self.env['chatwoot.message'].create_or_update_from_chatwoot(
                    account, conversation, msg_data
                )

        # Auto-cria lead se configurado
        if account.auto_create_lead and not conversation.lead_id and conversation.partner_id:
            conversation._create_lead()

        return conversation

    def _create_lead(self):
        """Cria oportunidade no CRM"""
        self.ensure_one()
        if not self.partner_id:
            return False

        lead_vals = {
            'name': f"Conversation {self.conversation_id} - {self.contact_id.name}",
            'partner_id': self.partner_id.id,
            'type': 'opportunity',
            'description': f"Origem: Chatwoot Conversation #{self.conversation_id}\nCanal: {self.channel}",
        }

        if self.inbox_id.odoo_team_id:
            lead_vals['team_id'] = self.inbox_id.odoo_team_id.id

        lead = self.env['crm.lead'].create(lead_vals)
        self.lead_id = lead.id

        _logger.info(f"Lead {lead.id} criado para conversa {self.conversation_id}")
        return lead

    def action_sync_messages(self):
        """Sincroniza mensagens da conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)
            messages = api.get_messages(self.conversation_id)

            for msg_data in messages:
                self.env['chatwoot.message'].create_or_update_from_chatwoot(
                    self.account_id, self, msg_data
                )

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Mensagens sincronizadas!'),
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.error(f"Erro ao sincronizar mensagens: {str(e)}")
            raise UserError(_('Erro ao sincronizar: %s') % str(e))

    def action_send_message(self, content, message_type='outgoing', private=False):
        """Envia mensagem na conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)

            data = {
                'content': content,
                'message_type': message_type,
                'private': private,
            }

            result = api.create_message(self.conversation_id, data)

            # Cria registro local da mensagem
            self.env['chatwoot.message'].create_or_update_from_chatwoot(
                self.account_id, self, result
            )

            return result

        except Exception as e:
            _logger.error(f"Erro ao enviar mensagem: {str(e)}")
            raise UserError(_('Erro ao enviar mensagem: %s') % str(e))

    def action_resolve(self):
        """Resolve a conversa"""
        return self._change_status('resolved')

    def action_reopen(self):
        """Reabre a conversa"""
        return self._change_status('open')

    def action_pending(self):
        """Marca como pendente"""
        return self._change_status('pending')

    def action_snooze(self):
        """Adia a conversa"""
        return self._change_status('snoozed')

    def _change_status(self, new_status):
        """Altera status da conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)
            api.toggle_status(self.conversation_id, new_status)

            self.status = new_status
            self.message_post(body=_('Status alterado para %s') % new_status)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Status atualizado!'),
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.error(f"Erro ao alterar status: {str(e)}")
            raise UserError(_('Erro ao alterar status: %s') % str(e))

    def action_assign_agent(self, agent_id):
        """Atribui agente à conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)

            agent = self.env['chatwoot.agent'].browse(agent_id)
            api.assign_agent(self.conversation_id, agent.agent_id)

            self.assignee_id = agent_id
            self.message_post(body=_('Atribuído a %s') % agent.name)

            return True

        except Exception as e:
            _logger.error(f"Erro ao atribuir agente: {str(e)}")
            raise UserError(_('Erro ao atribuir: %s') % str(e))

    def action_assign_team(self, team_id):
        """Atribui time à conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)

            team = self.env['chatwoot.team'].browse(team_id)
            api.assign_team(self.conversation_id, team.team_id)

            self.team_id = team_id
            self.message_post(body=_('Atribuído ao time %s') % team.name)

            return True

        except Exception as e:
            _logger.error(f"Erro ao atribuir time: {str(e)}")
            raise UserError(_('Erro ao atribuir time: %s') % str(e))

    def action_add_labels(self, label_ids):
        """Adiciona labels à conversa"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self.account_id)

            labels = self.env['chatwoot.label'].browse(label_ids)
            label_names = [label.title for label in labels]

            api.add_labels_to_conversation(self.conversation_id, label_names)

            self.label_ids = [(4, lid) for lid in label_ids]

            return True

        except Exception as e:
            _logger.error(f"Erro ao adicionar labels: {str(e)}")
            raise UserError(_('Erro ao adicionar labels: %s') % str(e))

    def action_create_lead(self):
        """Cria oportunidade manualmente"""
        self.ensure_one()
        if self.lead_id:
            raise UserError(_('Já existe uma oportunidade vinculada a esta conversa'))

        lead = self._create_lead()
        if lead:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'view_mode': 'form',
                'target': 'current',
            }
