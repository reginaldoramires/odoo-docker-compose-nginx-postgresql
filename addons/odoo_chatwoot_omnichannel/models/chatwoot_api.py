# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError
import requests
import logging
import json

_logger = logging.getLogger(__name__)


class ChatwootAPI(models.AbstractModel):
    _name = 'chatwoot.api'
    _description = 'Chatwoot API Client'

    @api.model
    def get_api_client(self, account):
        """Retorna um cliente API para a conta"""
        return ChatwootAPIClient(account)


class ChatwootAPIClient:
    """Cliente para API do Chatwoot"""

    def __init__(self, account):
        self.account = account
        self.base_url = account.base_url.rstrip('/')
        self.api_token = account.api_access_token
        self.account_id = account.account_id
        self.session = requests.Session()
        self.session.headers.update({
            'api_access_token': self.api_token,
            'Content-Type': 'application/json',
        })

    def _make_request(self, method, endpoint, data=None, params=None):
        """Faz uma requisição à API do Chatwoot"""
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/{endpoint}"

        try:
            _logger.debug(f"Chatwoot API Request: {method} {url}")

            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            _logger.error(f"Erro na requisição Chatwoot API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                _logger.error(f"Response: {e.response.text}")
            raise UserError(_('Erro na API do Chatwoot: %s') % str(e))

    def test_connection(self):
        """Testa a conexão com a API"""
        try:
            result = self._make_request('GET', 'profile')
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== Inbox Endpoints ==========

    def get_inboxes(self):
        """Retorna todas as inboxes"""
        return self._make_request('GET', 'inboxes')

    def get_inbox(self, inbox_id):
        """Retorna uma inbox específica"""
        return self._make_request('GET', f'inboxes/{inbox_id}')

    def create_inbox(self, data):
        """Cria uma nova inbox"""
        return self._make_request('POST', 'inboxes', data=data)

    def update_inbox(self, inbox_id, data):
        """Atualiza uma inbox"""
        return self._make_request('PATCH', f'inboxes/{inbox_id}', data=data)

    # ========== Agent Endpoints ==========

    def get_agents(self):
        """Retorna todos os agentes"""
        return self._make_request('GET', 'agents')

    def get_agent(self, agent_id):
        """Retorna um agente específico"""
        return self._make_request('GET', f'agents/{agent_id}')

    def create_agent(self, data):
        """Cria um novo agente"""
        return self._make_request('POST', 'agents', data=data)

    def update_agent(self, agent_id, data):
        """Atualiza um agente"""
        return self._make_request('PATCH', f'agents/{agent_id}', data=data)

    def delete_agent(self, agent_id):
        """Remove um agente"""
        return self._make_request('DELETE', f'agents/{agent_id}')

    # ========== Team Endpoints ==========

    def get_teams(self):
        """Retorna todos os times"""
        return self._make_request('GET', 'teams')

    def get_team(self, team_id):
        """Retorna um time específico"""
        return self._make_request('GET', f'teams/{team_id}')

    def create_team(self, data):
        """Cria um novo time"""
        return self._make_request('POST', 'teams', data=data)

    def update_team(self, team_id, data):
        """Atualiza um time"""
        return self._make_request('PATCH', f'teams/{team_id}', data=data)

    # ========== Contact Endpoints ==========

    def get_contacts(self, page=1):
        """Retorna todos os contatos"""
        return self._make_request('GET', 'contacts', params={'page': page})

    def get_contact(self, contact_id):
        """Retorna um contato específico"""
        return self._make_request('GET', f'contacts/{contact_id}')

    def create_contact(self, data):
        """Cria um novo contato"""
        return self._make_request('POST', 'contacts', data=data)

    def update_contact(self, contact_id, data):
        """Atualiza um contato"""
        return self._make_request('PATCH', f'contacts/{contact_id}', data=data)

    def search_contacts(self, query):
        """Busca contatos"""
        return self._make_request('GET', 'contacts/search', params={'q': query})

    # ========== Conversation Endpoints ==========

    def get_conversations(self, status='open', page=1):
        """Retorna conversas"""
        return self._make_request('GET', 'conversations', params={
            'status': status,
            'page': page
        })

    def get_conversation(self, conversation_id):
        """Retorna uma conversa específica"""
        return self._make_request('GET', f'conversations/{conversation_id}')

    def create_conversation(self, data):
        """Cria uma nova conversa"""
        return self._make_request('POST', 'conversations', data=data)

    def toggle_status(self, conversation_id, status):
        """Altera status da conversa"""
        return self._make_request('POST', f'conversations/{conversation_id}/toggle_status',
                                 data={'status': status})

    def assign_agent(self, conversation_id, agent_id):
        """Atribui um agente à conversa"""
        return self._make_request('POST', f'conversations/{conversation_id}/assignments',
                                 data={'assignee_id': agent_id})

    def assign_team(self, conversation_id, team_id):
        """Atribui um time à conversa"""
        return self._make_request('POST', f'conversations/{conversation_id}/assignments',
                                 data={'team_id': team_id})

    # ========== Message Endpoints ==========

    def get_messages(self, conversation_id):
        """Retorna mensagens de uma conversa"""
        return self._make_request('GET', f'conversations/{conversation_id}/messages')

    def create_message(self, conversation_id, data):
        """Cria uma nova mensagem"""
        return self._make_request('POST', f'conversations/{conversation_id}/messages',
                                 data=data)

    def delete_message(self, conversation_id, message_id):
        """Deleta uma mensagem"""
        return self._make_request('DELETE',
                                 f'conversations/{conversation_id}/messages/{message_id}')

    # ========== Label Endpoints ==========

    def get_labels(self):
        """Retorna todas as labels"""
        return self._make_request('GET', 'labels')

    def create_label(self, data):
        """Cria uma nova label"""
        return self._make_request('POST', 'labels', data=data)

    def update_label(self, label_id, data):
        """Atualiza uma label"""
        return self._make_request('PATCH', f'labels/{label_id}', data=data)

    def add_labels_to_conversation(self, conversation_id, labels):
        """Adiciona labels a uma conversa"""
        return self._make_request('POST', f'conversations/{conversation_id}/labels',
                                 data={'labels': labels})

    # ========== Report Endpoints ==========

    def get_account_summary(self, since=None, until=None):
        """Retorna resumo da conta"""
        params = {}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        return self._make_request('GET', 'reports/summary', params=params)

    def get_agent_summary(self, agent_id=None, since=None, until=None):
        """Retorna resumo de agente"""
        params = {}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        endpoint = f'reports/agents/{agent_id}' if agent_id else 'reports/agents'
        return self._make_request('GET', endpoint, params=params)

    def get_conversation_metrics(self, type='account'):
        """Retorna métricas de conversas"""
        return self._make_request('GET', f'reports/conversations/{type}')

    # ========== Webhook Endpoints ==========

    def get_webhooks(self):
        """Retorna webhooks configurados"""
        return self._make_request('GET', 'webhooks')

    def create_webhook(self, data):
        """Cria um novo webhook"""
        return self._make_request('POST', 'webhooks', data=data)

    def update_webhook(self, webhook_id, data):
        """Atualiza um webhook"""
        return self._make_request('PATCH', f'webhooks/{webhook_id}', data=data)

    def delete_webhook(self, webhook_id):
        """Remove um webhook"""
        return self._make_request('DELETE', f'webhooks/{webhook_id}')

    # ========== CSAT Endpoints ==========

    def get_csat_responses(self, page=1):
        """Retorna respostas CSAT"""
        return self._make_request('GET', 'csat_survey_responses', params={'page': page})
