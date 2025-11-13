# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging
import json
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class ChatwootWebhookController(http.Controller):

    @http.route('/chatwoot/webhook/<int:account_id>', type='json', auth='public', methods=['POST'], csrf=False)
    def chatwoot_webhook(self, account_id, **kwargs):
        """Endpoint para receber webhooks do Chatwoot"""
        try:
            # Busca conta
            account = request.env['chatwoot.account'].sudo().browse(account_id)

            if not account.exists():
                _logger.warning(f"Conta {account_id} não encontrada")
                return {'success': False, 'error': 'Account not found'}

            # Valida webhook secret se configurado
            if account.webhook_secret:
                if not self._validate_webhook_signature(account):
                    _logger.warning(f"Assinatura de webhook inválida para conta {account_id}")
                    return {'success': False, 'error': 'Invalid signature'}

            # Processa payload
            payload = request.jsonrequest
            event_type = payload.get('event')

            if not event_type:
                _logger.warning("Tipo de evento não especificado no webhook")
                return {'success': False, 'error': 'Event type not specified'}

            _logger.info(f"Webhook recebido: {event_type} para conta {account_id}")

            # Processa webhook
            request.env['chatwoot.webhook'].sudo().process_webhook(
                account, event_type, payload
            )

            return {'success': True, 'message': 'Webhook processed'}

        except Exception as e:
            _logger.error(f"Erro ao processar webhook: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _validate_webhook_signature(self, account):
        """Valida assinatura HMAC do webhook"""
        try:
            # Pega assinatura do header
            signature = request.httprequest.headers.get('X-Chatwoot-Signature')

            if not signature:
                return False

            # Calcula assinatura esperada
            payload = json.dumps(request.jsonrequest).encode('utf-8')
            expected_signature = hmac.new(
                account.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compara assinaturas
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            _logger.error(f"Erro ao validar assinatura: {str(e)}")
            return False

    @http.route('/chatwoot/webhook/test/<int:account_id>', type='http', auth='user', methods=['GET'])
    def test_webhook(self, account_id, **kwargs):
        """Endpoint de teste para webhook"""
        account = request.env['chatwoot.account'].browse(account_id)

        if not account.exists():
            return "Account not found"

        return f"""
        <html>
            <head><title>Chatwoot Webhook Test</title></head>
            <body>
                <h1>Chatwoot Webhook Endpoint</h1>
                <p>Account: {account.name}</p>
                <p>Webhook URL: {account.webhook_url}</p>
                <p>Status: Active</p>
                <p>Configure this URL in your Chatwoot account to receive webhooks.</p>
            </body>
        </html>
        """
