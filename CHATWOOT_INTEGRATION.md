# Integração Odoo Chatwoot Omnichannel

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação](#instalação)
5. [Configuração](#configuração)
6. [Funcionalidades](#funcionalidades)
7. [Uso](#uso)
8. [API e Webhooks](#api-e-webhooks)
9. [Solução de Problemas](#solução-de-problemas)
10. [Desenvolvimento e Personalização](#desenvolvimento-e-personalização)

---

## 🎯 Visão Geral

Esta é uma solução completa de **omnichannel** que integra o **Odoo** com o **Chatwoot** (plataforma open source de atendimento ao cliente), proporcionando:

### Principais Benefícios

- ✅ **Gerenciamento Unificado**: Todas as conversas de múltiplos canais em um só lugar
- ✅ **Sincronização em Tempo Real**: Webhooks e API REST para atualização instantânea
- ✅ **Integração Nativa com CRM**: Criação automática de leads e contatos
- ✅ **Multi-canal**: Suporte a WhatsApp, Facebook, Email, Chat Web, Twitter, Telegram, etc.
- ✅ **Atribuição Automática**: Distribuição inteligente de conversas para agentes
- ✅ **Escalável**: Arquitetura Docker pronta para produção
- ✅ **Open Source**: Totalmente personalizável e extensível

### Funcionalidades Implementadas

#### Módulo Odoo (`odoo_chatwoot_omnichannel`)

- **Modelos de Dados Completos**:
  - `chatwoot.account` - Configuração de contas Chatwoot
  - `chatwoot.inbox` - Caixas de entrada (canais)
  - `chatwoot.agent` - Agentes de atendimento
  - `chatwoot.conversation` - Conversas omnichannel
  - `chatwoot.message` - Mensagens e anexos
  - `chatwoot.contact` - Contatos integrados
  - `chatwoot.team` - Times de atendimento
  - `chatwoot.label` - Tags e categorização
  - `chatwoot.webhook` - Log de webhooks

- **Cliente API REST Completo**: Comunicação bidirecional com Chatwoot
- **Sincronização Automática**: Cron job configurável
- **Webhooks**: Recebe eventos em tempo real
- **Interface Web**: Dashboard e visualizações integradas
- **Segurança**: Grupos de usuários e permissões granulares
- **Integração CRM**: Criação automática de leads e parceiros

#### Infraestrutura Docker

- **Chatwoot Web**: Interface principal
- **Chatwoot Sidekiq**: Processamento de background jobs
- **PostgreSQL**: Banco de dados dedicado
- **Redis**: Cache e filas
- **Nginx**: Proxy reverso (já existente)
- **Odoo**: ERP/CRM (já existente)

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX (Proxy)                        │
│                     (Port 80/443)                           │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
             │                              │
    ┌────────▼────────┐          ┌─────────▼──────────┐
    │   ODOO (8069)   │◄────────►│  CHATWOOT (3000)   │
    │                 │   API    │                     │
    │  + Módulo       │          │  - Web UI          │
    │    Omnichannel  │          │  - API REST        │
    └────────┬────────┘          └─────────┬──────────┘
             │                              │
             │                              │
    ┌────────▼────────┐          ┌─────────▼──────────┐
    │  PostgreSQL     │          │  PostgreSQL        │
    │  (Odoo DB)      │          │  (Chatwoot DB)     │
    └─────────────────┘          └─────────┬──────────┘
                                           │
                                  ┌────────▼──────────┐
                                  │   Redis Cache     │
                                  │   + Queues        │
                                  └───────────────────┘
                                           │
                                  ┌────────▼──────────┐
                                  │  Sidekiq Worker   │
                                  │  (Background)     │
                                  └───────────────────┘

Canais Externos:
- WhatsApp Business API
- Facebook Messenger
- Twitter DM
- Email (SMTP/IMAP)
- Website Chat Widget
- Telegram
- Line, SMS, etc.
```

### Fluxo de Dados

1. **Cliente → Canal → Chatwoot**: Mensagem recebida
2. **Chatwoot → Webhook → Odoo**: Notificação em tempo real
3. **Odoo**: Processa e armazena conversa/mensagem
4. **Odoo → API → Chatwoot**: Envio de resposta
5. **Chatwoot → Canal → Cliente**: Entrega da resposta

---

## 📦 Pré-requisitos

### Software Necessário

- **Docker** >= 20.10
- **Docker Compose** >= 1.29
- **Git**
- **OpenSSL** (para gerar chaves)

### Hardware Recomendado

#### Desenvolvimento
- CPU: 4 cores
- RAM: 8GB
- Disco: 20GB

#### Produção
- CPU: 8+ cores
- RAM: 16GB+
- Disco: 50GB+ SSD
- Rede: 100Mbps+

### Portas Utilizadas

- `80` - HTTP (Nginx)
- `443` - HTTPS (Nginx)
- `8069` - Odoo
- `3000` - Chatwoot
- `5432` - PostgreSQL (Odoo)
- `6379` - Redis (Chatwoot)
- `9432` - PostgreSQL (exposta localmente para backup)

---

## 🚀 Instalação

### Passo 1: Clone o Repositório

```bash
git clone <repository-url>
cd odoo-docker-compose-nginx-postgresql
```

### Passo 2: Configuração Inicial

```bash
# Cria diretórios necessários
sudo mkdir -p ./odoo-web-data ./addons ./chatwoot-storage ./chatwoot-public
sudo mkdir -p ./chatwoot-db-data ./chatwoot-redis-data

# Define permissões
sudo chmod -R 777 ./odoo-web-data ./addons
sudo chmod -R 777 ./chatwoot-storage ./chatwoot-public
```

### Passo 3: Configurar Variáveis de Ambiente

```bash
# Copia e edita configuração do Chatwoot
cp .env.chatwoot.example .env.chatwoot

# Gera SECRET_KEY_BASE
openssl rand -hex 64
# Cole o resultado em .env.chatwoot na variável SECRET_KEY_BASE
```

**Edite `.env.chatwoot` com suas configurações:**

```bash
# Configuração SMTP (obrigatório para funcionar)
SMTP_ADDRESS=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app

# URL Frontend (ajuste para seu domínio)
FRONTEND_URL=http://seu-dominio.com:3000
```

### Passo 4: Executar Setup Automatizado

```bash
# Torna script executável
chmod +x setup-chatwoot.sh

# Executa instalação
./setup-chatwoot.sh
```

### Passo 5: Instalação Manual (Alternativa)

Se preferir instalar manualmente:

```bash
# 1. Cria rede Docker
docker network create odoo_network

# 2. Inicia Odoo
docker-compose up -d

# 3. Aguarda Odoo iniciar (30-60 segundos)
sleep 30

# 4. Inicia Chatwoot
docker-compose -f docker-compose.chatwoot.yml up -d

# 5. Aguarda serviços (30 segundos)
sleep 30

# 6. Prepara banco de dados Chatwoot
docker-compose -f docker-compose.chatwoot.yml exec chatwoot bundle exec rails db:chatwoot_prepare
```

### Passo 6: Verificar Instalação

```bash
# Verifica containers rodando
docker-compose ps
docker-compose -f docker-compose.chatwoot.yml ps

# Deve mostrar todos os containers como "Up"

# Verifica logs
docker-compose logs -f odoo
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot
```

---

## ⚙️ Configuração

### Configuração do Chatwoot

#### 1. Acesso Inicial

Acesse: `http://localhost:3000` ou `http://seu-dominio.com:3000`

1. Clique em **"Create your account"**
2. Preencha:
   - **Company Name**: Nome da sua empresa
   - **Your Name**: Seu nome
   - **Email**: seu-email@empresa.com
   - **Password**: Senha segura
3. Clique em **"Create Account"**

#### 2. Configurar Inbox (Canal)

1. No Chatwoot, vá em **Settings** → **Inboxes**
2. Clique em **"Add Inbox"**
3. Escolha o tipo de canal:

**Website (Chat Widget):**
- Nome: "Website Chat"
- Website URL: http://seu-site.com
- Copie o código do widget

**Facebook:**
- Conecte sua página do Facebook
- Autorize as permissões

**WhatsApp Business API:**
- Configure com provedor (Twilio, 360Dialog, etc.)

**Email:**
- IMAP/SMTP para receber/enviar emails

#### 3. Criar API Access Token

1. No Chatwoot, vá em **Settings** → **Applications**
2. Clique em **"New Access Token"**
3. Nome: "Odoo Integration"
4. **Copie o token gerado** (você vai precisar!)

### Configuração do Módulo Odoo

#### 1. Instalar o Módulo

1. Acesse Odoo: `http://localhost:8069`
2. Login com suas credenciais
3. Vá em **Apps** (modo desenvolvedor ativado)
4. Remova filtro "Apps"
5. Busque por **"Chatwoot"**
6. Clique em **Instalar**

#### 2. Configurar Conta Chatwoot

1. No Odoo, vá em **Chatwoot** → **Configuration** → **Accounts**
2. Clique em **Criar**
3. Preencha:

```
Name: My Chatwoot Account
Account ID: 1 (ou o ID da sua conta no Chatwoot)
Chatwoot URL: http://chatwoot:3000
API Access Token: <cole o token copiado>
Active: ✓
Auto Sync: ✓
Sync Interval (minutes): 5
Webhook Enabled: ✓
Auto Create Partner: ✓
Auto Create Lead: ✓
Auto Assign Agent: ✓
```

4. Clique em **"Test Connection"**
   - Deve aparecer mensagem de sucesso
5. Clique em **"Sync All"**
   - Sincroniza inboxes, agents, conversations, etc.
6. **Salvar**

#### 3. Configurar Webhook no Chatwoot

1. No Chatwoot, vá em **Settings** → **Webhooks**
2. Clique em **"Add Webhook"**
3. Preencha:

```
URL: http://odoo:8069/chatwoot/webhook/1
(onde "1" é o ID da conta no Odoo)

Events (selecione todos):
✓ conversation_created
✓ conversation_updated
✓ conversation_status_changed
✓ message_created
✓ message_updated
✓ contact_created
✓ contact_updated
```

4. **Salvar**

---

## 🎨 Funcionalidades

### 1. Dashboard Omnichannel

**Acesso**: Chatwoot → Dashboard

Visualize em tempo real:
- Conversas abertas
- Conversas pendentes
- Total de contatos
- Conversas resolvidas hoje
- Tempo médio de resposta
- Taxa de resolução

### 2. Gerenciamento de Conversas

**Acesso**: Chatwoot → Conversations

Funcionalidades:
- Visualizar todas as conversas
- Filtrar por status (Open, Pending, Resolved)
- Filtrar por agente, time, inbox
- Buscar por contato ou conteúdo
- Atribuir para agente/time
- Adicionar labels
- Enviar mensagens
- Anexar arquivos
- Marcar como resolvida

**No Odoo:**
- Sincronização automática
- Histórico completo
- Integração com CRM (leads)
- Criação automática de parceiros

### 3. Gestão de Contatos

**Sincronização Bidirecional:**
- Contato criado no Chatwoot → Automaticamente no Odoo
- Parceiro no Odoo pode ser vinculado a contato Chatwoot

**Informações Sincronizadas:**
- Nome
- Email
- Telefone
- Atributos customizados
- Histórico de conversas

### 4. Atribuição Automática

Configure regras de atribuição:
- Round-robin entre agentes
- Por time
- Por tipo de inbox
- Por labels

### 5. Múltiplos Canais (Omnichannel)

Suportados:
- ✅ Website Chat Widget
- ✅ Facebook Messenger
- ✅ WhatsApp Business API
- ✅ Twitter DM
- ✅ Email
- ✅ Telegram
- ✅ Line
- ✅ SMS (Twilio)
- ✅ API Channel (custom)

### 6. Reports e Métricas

**Disponíveis:**
- Conversas por período
- Tempo médio de resposta
- Taxa de resolução
- Performance por agente
- Performance por inbox
- CSAT (Customer Satisfaction Score)

---

## 📖 Uso

### Cenário 1: Atendimento ao Cliente

1. **Cliente envia mensagem** via WhatsApp
2. **Chatwoot recebe** e cria conversa
3. **Webhook notifica Odoo** em tempo real
4. **Odoo sincroniza**:
   - Cria/atualiza contato
   - Vincula a parceiro existente
   - Cria lead no CRM (se configurado)
5. **Agente responde** pelo Chatwoot
6. **Sistema registra** no histórico do parceiro

### Cenário 2: Vendas via Chat

1. Visitor acessa site e abre chat
2. Agente atende e qualifica lead
3. Sistema cria automaticamente:
   - Contato no Chatwoot/Odoo
   - Parceiro no Odoo
   - Oportunidade no CRM
4. Vendedor acompanha no pipeline
5. Histórico completo de conversas anexado

### Cenário 3: Suporte Multi-canal

Cliente pode:
1. Iniciar conversa no Facebook
2. Continuar por Email
3. Finalizar por WhatsApp

**Sistema mantém contexto unificado!**

### Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot

# Reiniciar serviços
docker-compose restart
docker-compose -f docker-compose.chatwoot.yml restart

# Parar tudo
docker-compose down
docker-compose -f docker-compose.chatwoot.yml down

# Backup de banco de dados
docker exec postgresql pg_dump -U odoo your_database > backup.sql
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production > backup_chatwoot.sql

# Atualizar Chatwoot
docker-compose -f docker-compose.chatwoot.yml pull
docker-compose -f docker-compose.chatwoot.yml up -d
docker-compose -f docker-compose.chatwoot.yml exec chatwoot bundle exec rails db:migrate
```

---

## 🔌 API e Webhooks

### API REST do Chatwoot

**Base URL**: `http://chatwoot:3000/api/v1/accounts/{account_id}`

**Headers obrigatórios:**
```
api_access_token: YOUR_TOKEN_HERE
Content-Type: application/json
```

#### Endpoints Principais

**Conversas:**
```bash
GET  /conversations - Lista conversas
GET  /conversations/{id} - Detalhes
POST /conversations - Cria conversa
POST /conversations/{id}/messages - Envia mensagem
POST /conversations/{id}/toggle_status - Altera status
POST /conversations/{id}/assignments - Atribui agente
```

**Contatos:**
```bash
GET  /contacts - Lista contatos
POST /contacts - Cria contato
GET  /contacts/{id} - Detalhes
PUT  /contacts/{id} - Atualiza
GET  /contacts/search?q={query} - Busca
```

**Mensagens:**
```bash
GET  /conversations/{id}/messages - Lista mensagens
POST /conversations/{id}/messages - Envia mensagem
DELETE /conversations/{id}/messages/{msg_id} - Deleta
```

### Webhooks Recebidos

**Endpoint Odoo**: `http://odoo:8069/chatwoot/webhook/{account_id}`

**Eventos suportados:**
- `conversation_created` - Nova conversa
- `conversation_updated` - Conversa atualizada
- `conversation_status_changed` - Status alterado
- `conversation_resolved` - Conversa resolvida
- `conversation_opened` - Conversa reaberta
- `message_created` - Nova mensagem
- `message_updated` - Mensagem atualizada
- `contact_created` - Novo contato
- `contact_updated` - Contato atualizado

**Formato do Payload:**
```json
{
  "event": "message_created",
  "id": 123,
  "message": {
    "id": 456,
    "content": "Hello!",
    "message_type": 0,
    "created_at": 1234567890,
    "conversation_id": 789,
    "sender": {
      "id": 1,
      "name": "Customer"
    }
  }
}
```

---

## 🔧 Solução de Problemas

### Problema: Chatwoot não inicia

**Sintomas**: Container `chatwoot` reiniciando constantemente

**Soluções:**
1. Verifique SECRET_KEY_BASE está configurado
2. Verifique conexão com PostgreSQL:
   ```bash
   docker-compose -f docker-compose.chatwoot.yml logs chatwoot_postgres
   ```
3. Execute migrations:
   ```bash
   docker-compose -f docker-compose.chatwoot.yml exec chatwoot bundle exec rails db:chatwoot_prepare
   ```

### Problema: Webhook não funciona

**Sintomas**: Mensagens não aparecem no Odoo

**Soluções:**
1. Verifique URL do webhook está correta
2. Teste endpoint manualmente:
   ```bash
   curl -X POST http://localhost:8069/chatwoot/webhook/1 \
     -H "Content-Type: application/json" \
     -d '{"event": "message_created"}'
   ```
3. Verifique logs:
   ```bash
   docker-compose logs odoo | grep webhook
   ```

### Problema: Sincronização falha

**Sintomas**: Erro ao clicar "Sync All"

**Soluções:**
1. Teste conexão primeiro
2. Verifique token API está correto
3. Verifique URL: deve ser `http://chatwoot:3000` (interno Docker)
4. Verifique logs:
   ```bash
   docker-compose logs odoo | grep chatwoot
   ```

### Problema: Porta já em uso

**Sintomas**: Erro "port is already allocated"

**Soluções:**
```bash
# Verifica processo usando porta 3000
sudo lsof -i :3000

# Para Apache2 se necessário
sudo service apache2 stop

# Ou altere porta em docker-compose.chatwoot.yml
# "3001:3000" ao invés de "3000:3000"
```

### Problema: Permissões de arquivo

**Sintomas**: Erro ao salvar uploads/storage

**Soluções:**
```bash
sudo chmod -R 777 ./chatwoot-storage
sudo chmod -R 777 ./chatwoot-public
sudo chmod -R 777 ./odoo-web-data
```

### Logs Importantes

```bash
# Odoo
docker-compose logs -f odoo

# Chatwoot Web
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot

# Chatwoot Sidekiq (background jobs)
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot_sidekiq

# PostgreSQL
docker-compose logs -f db
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot_postgres

# Redis
docker-compose -f docker-compose.chatwoot.yml logs -f chatwoot_redis
```

---

## 🛠️ Desenvolvimento e Personalização

### Estrutura do Módulo

```
addons/odoo_chatwoot_omnichannel/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── chatwoot_account.py      # Configuração conta
│   ├── chatwoot_api.py          # Cliente API REST
│   ├── chatwoot_inbox.py        # Canais
│   ├── chatwoot_agent.py        # Agentes
│   ├── chatwoot_conversation.py # Conversas
│   ├── chatwoot_message.py      # Mensagens
│   ├── chatwoot_contact.py      # Contatos
│   ├── chatwoot_team.py         # Times
│   ├── chatwoot_label.py        # Labels
│   ├── chatwoot_webhook.py      # Webhooks
│   ├── res_partner.py           # Extensão Partner
│   └── crm_lead.py              # Extensão Lead
├── controllers/
│   ├── __init__.py
│   ├── main.py                  # Controllers principais
│   └── webhook.py               # Webhook receiver
├── wizard/
│   ├── __init__.py
│   ├── chatwoot_sync_wizard.py
│   └── chatwoot_assign_conversation.py
├── views/
│   ├── menu_views.xml
│   ├── chatwoot_account_views.xml
│   ├── chatwoot_conversation_views.xml
│   └── ...
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
└── data/
    ├── chatwoot_channel_data.xml
    └── ir_cron_data.xml
```

### Adicionar Novo Canal

1. Configure no Chatwoot (Settings → Inboxes)
2. Sincronize no Odoo (automático ou manual)
3. Configure regras de atribuição se necessário

### Personalizar Webhook

Edite `models/chatwoot_webhook.py`:

```python
def _process_message_event(self, account, payload):
    # Adicione lógica customizada aqui
    # Exemplo: notificar via email
    if payload.get('message', {}).get('message_type') == 0:  # incoming
        # Enviar notificação
        pass
```

### Adicionar Campos Customizados

```python
# Em models/chatwoot_conversation.py
class ChatwootConversation(models.Model):
    _inherit = 'chatwoot.conversation'

    custom_field = fields.Char('Custom Field')
```

### Integrar com Outros Módulos

```python
# Exemplo: Integração com helpdesk
def _create_ticket(self):
    ticket_vals = {
        'name': self.name,
        'partner_id': self.partner_id.id,
        'description': self.message_ids[0].content,
    }
    ticket = self.env['helpdesk.ticket'].create(ticket_vals)
    self.ticket_id = ticket.id
```

---

## 📊 Performance e Escalabilidade

### Recomendações de Produção

#### 1. Otimização de Recursos

**docker-compose.chatwoot.yml:**
```yaml
chatwoot:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

#### 2. Aumentar Workers Sidekiq

```yaml
chatwoot_sidekiq:
  environment:
    - SIDEKIQ_CONCURRENCY=25
```

#### 3. Configurar Redis Persistence

```yaml
chatwoot_redis:
  command: redis-server --appendonly yes --appendfsync everysec
```

#### 4. Backup Automático

Crie cron job:
```bash
# /etc/cron.daily/backup-chatwoot.sh
#!/bin/bash
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production | gzip > /backups/chatwoot_$(date +%Y%m%d).sql.gz
```

#### 5. Monitoramento

Use Prometheus + Grafana ou similar para monitorar:
- Uso de CPU/RAM
- Latência de API
- Tamanho de filas Redis
- Taxa de processamento de webhooks

---

## 📝 Checklist de Deploy em Produção

- [ ] Configurar domínio e SSL (Let's Encrypt)
- [ ] Configurar SMTP real (não usar Gmail)
- [ ] Configurar S3 para storage (opcional)
- [ ] Aumentar recursos Docker
- [ ] Configurar backup automático
- [ ] Configurar monitoramento
- [ ] Testar failover
- [ ] Documentar credenciais em local seguro
- [ ] Configurar firewall
- [ ] Habilitar logs centralizados
- [ ] Testar recuperação de desastre

---

## 🤝 Suporte e Contribuição

### Obter Suporte

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Este arquivo + README.md
- **Logs**: Sempre inclua logs ao reportar problemas

### Contribuir

1. Fork o projeto
2. Crie feature branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Add: nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

---

## 📄 Licença

Este módulo é licenciado sob LGPL-3.

---

## 🎉 Conclusão

Você agora tem uma solução completa de omnichannel rodando!

**Próximos passos sugeridos:**
1. Configure seus canais (WhatsApp, Facebook, etc.)
2. Crie agentes e times
3. Personalize labels e regras de atribuição
4. Integre com seu fluxo de vendas/suporte
5. Configure relatórios e métricas

**Dúvidas?** Consulte a documentação ou abra uma issue.

Bom atendimento! 🚀
