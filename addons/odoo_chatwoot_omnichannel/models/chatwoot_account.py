# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChatwootAccount(models.Model):
    _name = 'chatwoot.account'
    _description = 'Chatwoot Account Configuration'
    _order = 'name'

    name = fields.Char(string='Name', required=True, help='Nome da conta Chatwoot')
    account_id = fields.Integer(string='Account ID', required=True, help='ID da conta no Chatwoot')

    # Configurações de conexão
    base_url = fields.Char(
        string='Chatwoot URL',
        required=True,
        default='http://chatwoot:3000',
        help='URL base do Chatwoot (ex: https://app.chatwoot.com ou http://chatwoot:3000)'
    )
    api_access_token = fields.Char(
        string='API Access Token',
        required=True,
        help='Token de acesso da API do Chatwoot'
    )

    # Configurações de sincronização
    active = fields.Boolean(string='Active', default=True)
    auto_sync = fields.Boolean(
        string='Auto Sync',
        default=True,
        help='Sincronizar automaticamente com Chatwoot'
    )
    sync_interval = fields.Integer(
        string='Sync Interval (minutes)',
        default=5,
        help='Intervalo de sincronização em minutos'
    )
    last_sync_date = fields.Datetime(string='Last Sync Date', readonly=True)

    # Configurações de webhook
    webhook_enabled = fields.Boolean(string='Webhook Enabled', default=True)
    webhook_secret = fields.Char(string='Webhook Secret')
    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
        store=False
    )

    # Configurações de integração
    auto_create_partner = fields.Boolean(
        string='Auto Create Partner',
        default=True,
        help='Criar automaticamente parceiro no Odoo para novos contatos'
    )
    auto_create_lead = fields.Boolean(
        string='Auto Create Lead',
        default=True,
        help='Criar automaticamente oportunidade no CRM'
    )
    auto_assign_agent = fields.Boolean(
        string='Auto Assign Agent',
        default=True,
        help='Atribuir automaticamente agente às conversas'
    )

    # Estatísticas
    inbox_count = fields.Integer(string='Inboxes', compute='_compute_counts')
    agent_count = fields.Integer(string='Agents', compute='_compute_counts')
    conversation_count = fields.Integer(string='Conversations', compute='_compute_counts')
    contact_count = fields.Integer(string='Contacts', compute='_compute_counts')

    # Relacionamentos
    inbox_ids = fields.One2many('chatwoot.inbox', 'account_id', string='Inboxes')
    agent_ids = fields.One2many('chatwoot.agent', 'account_id', string='Agents')
    conversation_ids = fields.One2many('chatwoot.conversation', 'account_id', string='Conversations')
    contact_ids = fields.One2many('chatwoot.contact', 'account_id', string='Contacts')
    team_ids = fields.One2many('chatwoot.team', 'account_id', string='Teams')
    label_ids = fields.One2many('chatwoot.label', 'account_id', string='Labels')

    # Configurações avançadas
    enable_csat = fields.Boolean(string='Enable CSAT', default=True, help='Customer Satisfaction Score')
    enable_continuity = fields.Boolean(string='Enable Continuity', default=True)
    domain = fields.Char(string='Domain')
    locale = fields.Selection([
        ('pt_BR', 'Português (Brasil)'),
        ('en', 'English'),
        ('es', 'Español'),
        ('fr', 'Français'),
    ], string='Locale', default='pt_BR')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('account_id_unique', 'unique(account_id)', 'Account ID must be unique!'),
    ]

    @api.depends('base_url')
    def _compute_webhook_url(self):
        """Computa a URL do webhook"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if base_url and record.id:
                record.webhook_url = f"{base_url}/chatwoot/webhook/{record.id}"
            else:
                record.webhook_url = False

    @api.depends('inbox_ids', 'agent_ids', 'conversation_ids', 'contact_ids')
    def _compute_counts(self):
        """Computa contadores"""
        for record in self:
            record.inbox_count = len(record.inbox_ids)
            record.agent_count = len(record.agent_ids)
            record.conversation_count = len(record.conversation_ids)
            record.contact_count = len(record.contact_ids)

    @api.constrains('base_url')
    def _check_base_url(self):
        """Valida URL base"""
        for record in self:
            if record.base_url:
                if not record.base_url.startswith(('http://', 'https://')):
                    raise ValidationError(_('URL base deve começar com http:// ou https://'))

    def action_test_connection(self):
        """Testa conexão com Chatwoot"""
        self.ensure_one()
        try:
            api = self.env['chatwoot.api'].get_api_client(self)
            result = api.test_connection()

            if result.get('success'):
                self.last_sync_date = fields.Datetime.now()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Conexão com Chatwoot estabelecida com sucesso!'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Falha ao conectar: %s') % result.get('error'))

        except Exception as e:
            _logger.error(f"Erro ao testar conexão com Chatwoot: {str(e)}")
            raise UserError(_('Erro ao conectar com Chatwoot: %s') % str(e))

    def action_sync_all(self):
        """Sincroniza todos os dados do Chatwoot"""
        self.ensure_one()
        try:
            _logger.info(f"Iniciando sincronização completa da conta {self.name}")

            # Sincroniza em ordem
            self.action_sync_inboxes()
            self.action_sync_agents()
            self.action_sync_teams()
            self.action_sync_labels()
            self.action_sync_contacts()
            self.action_sync_conversations()

            self.last_sync_date = fields.Datetime.now()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Sincronização completa realizada com sucesso!'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"Erro durante sincronização: {str(e)}")
            raise UserError(_('Erro durante sincronização: %s') % str(e))

    def action_sync_inboxes(self):
        """Sincroniza inboxes"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        inboxes = api.get_inboxes()

        for inbox_data in inboxes:
            self.env['chatwoot.inbox'].create_or_update_from_chatwoot(self, inbox_data)

        _logger.info(f"Sincronizados {len(inboxes)} inboxes")

    def action_sync_agents(self):
        """Sincroniza agentes"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        agents = api.get_agents()

        for agent_data in agents:
            self.env['chatwoot.agent'].create_or_update_from_chatwoot(self, agent_data)

        _logger.info(f"Sincronizados {len(agents)} agentes")

    def action_sync_teams(self):
        """Sincroniza times"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        teams = api.get_teams()

        for team_data in teams:
            self.env['chatwoot.team'].create_or_update_from_chatwoot(self, team_data)

        _logger.info(f"Sincronizados {len(teams)} times")

    def action_sync_labels(self):
        """Sincroniza labels"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        labels = api.get_labels()

        for label_data in labels:
            self.env['chatwoot.label'].create_or_update_from_chatwoot(self, label_data)

        _logger.info(f"Sincronizadas {len(labels)} labels")

    def action_sync_contacts(self):
        """Sincroniza contatos"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        contacts = api.get_contacts()

        for contact_data in contacts:
            self.env['chatwoot.contact'].create_or_update_from_chatwoot(self, contact_data)

        _logger.info(f"Sincronizados {len(contacts)} contatos")

    def action_sync_conversations(self):
        """Sincroniza conversas"""
        self.ensure_one()
        api = self.env['chatwoot.api'].get_api_client(self)
        conversations = api.get_conversations()

        for conv_data in conversations:
            self.env['chatwoot.conversation'].create_or_update_from_chatwoot(self, conv_data)

        _logger.info(f"Sincronizadas {len(conversations)} conversas")

    def cron_sync_all_accounts(self):
        """Cron job para sincronizar todas as contas ativas"""
        accounts = self.search([('active', '=', True), ('auto_sync', '=', True)])
        for account in accounts:
            try:
                account.action_sync_all()
            except Exception as e:
                _logger.error(f"Erro ao sincronizar conta {account.name}: {str(e)}")
