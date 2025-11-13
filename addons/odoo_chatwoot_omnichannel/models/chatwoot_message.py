# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ChatwootMessage(models.Model):
    _name = 'chatwoot.message'
    _description = 'Chatwoot Message'
    _order = 'created_at desc'

    message_id = fields.Integer(string='Message ID', required=True)
    conversation_id = fields.Many2one('chatwoot.conversation', string='Conversation',
                                      required=True, ondelete='cascade', index=True)
    account_id = fields.Many2one('chatwoot.account', string='Account',
                                  related='conversation_id.account_id', store=True)

    # Conteúdo da mensagem
    content = fields.Text(string='Content', required=True)
    content_type = fields.Selection([
        ('text', 'Text'),
        ('input_text', 'Input Text'),
        ('input_textarea', 'Input Textarea'),
        ('input_email', 'Input Email'),
        ('input_select', 'Input Select'),
        ('cards', 'Cards'),
        ('form', 'Form'),
        ('article', 'Article'),
    ], string='Content Type', default='text')

    # Tipo e origem
    message_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
        ('activity', 'Activity'),
        ('template', 'Template'),
    ], string='Message Type', required=True, default='incoming')

    private = fields.Boolean(string='Private', default=False,
                            help='Mensagem privada (nota interna)')
    status = fields.Selection([
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], string='Status', default='sent')

    # Remetente
    sender_type = fields.Selection([
        ('contact', 'Contact'),
        ('agent_bot', 'Agent/Bot'),
    ], string='Sender Type')
    sender_id = fields.Integer(string='Sender ID')
    sender_name = fields.Char(string='Sender Name')

    # Timestamps
    created_at = fields.Datetime(string='Created At', required=True)
    external_source_id = fields.Char(string='External Source ID')

    # Anexos
    attachment_count = fields.Integer(string='Attachments', compute='_compute_attachment_count')
    attachment_ids = fields.One2many('chatwoot.message.attachment', 'message_id',
                                     string='Attachments')

    # Metadata
    source_id = fields.Char(string='Source ID')
    content_attributes = fields.Text(string='Content Attributes')

    _sql_constraints = [
        ('message_id_conversation_unique', 'unique(message_id, conversation_id)',
         'Message ID must be unique per conversation!'),
    ]

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Computa número de anexos"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.model
    def create_or_update_from_chatwoot(self, account, conversation, data):
        """Cria ou atualiza mensagem a partir de dados do Chatwoot"""
        message_id = data.get('id')
        existing = self.search([
            ('message_id', '=', message_id),
            ('conversation_id', '=', conversation.id)
        ], limit=1)

        # Processa sender
        sender_name = None
        sender_type = data.get('sender_type')
        if data.get('sender'):
            sender_name = data['sender'].get('name') or data['sender'].get('email')

        values = {
            'message_id': message_id,
            'conversation_id': conversation.id,
            'content': data.get('content', ''),
            'content_type': data.get('content_type', 'text'),
            'message_type': self._map_message_type(data.get('message_type', 0)),
            'private': data.get('private', False),
            'status': data.get('status', 'sent'),
            'sender_type': sender_type,
            'sender_id': data.get('sender', {}).get('id'),
            'sender_name': sender_name,
            'created_at': data.get('created_at') or fields.Datetime.now(),
            'external_source_id': data.get('external_source_id'),
            'source_id': data.get('source_id'),
            'content_attributes': str(data.get('content_attributes', {})),
        }

        if existing:
            existing.write(values)
            message = existing
        else:
            message = self.create(values)

        # Processa anexos
        if data.get('attachments'):
            for att_data in data['attachments']:
                message._create_attachment(att_data)

        return message

    @api.model
    def _map_message_type(self, message_type_value):
        """Mapeia tipo de mensagem do Chatwoot"""
        # Chatwoot usa: 0=incoming, 1=outgoing, 2=activity, 3=template
        mapping = {
            0: 'incoming',
            1: 'outgoing',
            2: 'activity',
            3: 'template',
        }
        if isinstance(message_type_value, int):
            return mapping.get(message_type_value, 'incoming')
        return message_type_value

    def _create_attachment(self, data):
        """Cria anexo da mensagem"""
        self.ensure_one()

        values = {
            'message_id': self.id,
            'file_type': data.get('file_type'),
            'file_url': data.get('data_url'),
            'thumb_url': data.get('thumb_url'),
            'file_size': data.get('file_size'),
        }

        existing = self.env['chatwoot.message.attachment'].search([
            ('message_id', '=', self.id),
            ('file_url', '=', data.get('data_url'))
        ], limit=1)

        if not existing:
            self.env['chatwoot.message.attachment'].create(values)


class ChatwootMessageAttachment(models.Model):
    _name = 'chatwoot.message.attachment'
    _description = 'Chatwoot Message Attachment'

    message_id = fields.Many2one('chatwoot.message', string='Message',
                                  required=True, ondelete='cascade')

    file_type = fields.Selection([
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
    ], string='File Type', default='file')

    file_url = fields.Char(string='File URL', required=True)
    thumb_url = fields.Char(string='Thumbnail URL')
    file_size = fields.Integer(string='File Size (bytes)')
