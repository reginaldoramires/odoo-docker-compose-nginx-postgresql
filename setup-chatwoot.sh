#!/bin/bash
# Script para configurar e iniciar Chatwoot com Odoo

set -e

echo "=========================================="
echo "Chatwoot + Odoo Omnichannel Setup"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para printar com cor
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

print_info "Docker e Docker Compose encontrados!"

# Cria diretórios necessários
print_info "Criando diretórios necessários..."
mkdir -p ./chatwoot-db-data
mkdir -p ./chatwoot-redis-data
mkdir -p ./chatwoot-storage
mkdir -p ./chatwoot-public
mkdir -p ./addons

# Define permissões
print_info "Configurando permissões..."
sudo chmod -R 777 ./chatwoot-storage
sudo chmod -R 777 ./chatwoot-public
sudo chmod -R 777 ./addons

# Verifica se .env.chatwoot existe
if [ ! -f .env.chatwoot ]; then
    print_warning "Arquivo .env.chatwoot não encontrado. Copiando do exemplo..."
    cp .env.chatwoot.example .env.chatwoot

    # Gera SECRET_KEY_BASE
    print_info "Gerando SECRET_KEY_BASE..."
    SECRET_KEY=$(openssl rand -hex 64)
    sed -i "s/replace_with_your_secret_key_base/$SECRET_KEY/" .env.chatwoot

    print_warning "Por favor, edite o arquivo .env.chatwoot com suas configurações antes de continuar."
    print_warning "Especialmente: SMTP settings, FRONTEND_URL, etc."
    read -p "Pressione Enter para continuar após editar .env.chatwoot..."
fi

# Cria rede Docker se não existir
print_info "Criando rede Docker..."
docker network inspect odoo_network >/dev/null 2>&1 || docker network create odoo_network

# Inicia serviços Odoo (se não estiverem rodando)
print_info "Verificando serviços Odoo..."
if ! docker ps | grep -q odoo; then
    print_info "Iniciando serviços Odoo..."
    docker-compose up -d
    print_info "Aguardando Odoo iniciar (30 segundos)..."
    sleep 30
else
    print_info "Serviços Odoo já estão rodando."
fi

# Inicia serviços Chatwoot
print_info "Iniciando serviços Chatwoot..."
docker-compose -f docker-compose.chatwoot.yml up -d

# Aguarda serviços iniciarem
print_info "Aguardando serviços Chatwoot iniciarem (30 segundos)..."
sleep 30

# Verifica se containers estão rodando
print_info "Verificando status dos containers..."
docker-compose ps
docker-compose -f docker-compose.chatwoot.yml ps

# Executa migrations do Chatwoot
print_info "Executando migrations do Chatwoot..."
docker-compose -f docker-compose.chatwoot.yml exec -T chatwoot bundle exec rails db:chatwoot_prepare

# Cria usuário admin do Chatwoot (se necessário)
print_info "Configurando usuário admin do Chatwoot..."
echo ""
print_warning "Para criar um usuário admin, acesse:"
echo "  http://localhost:3000"
echo ""
print_warning "Ou execute manualmente:"
echo "  docker-compose -f docker-compose.chatwoot.yml exec chatwoot bundle exec rails console"
echo "  > Account.create!(name: 'Acme')"
echo "  > User.create!(name: 'Admin', email: 'admin@example.com', password: 'password', account_id: 1, role: :administrator)"
echo ""

# Informações de acesso
print_info "Setup completo!"
echo ""
echo "=========================================="
echo "INFORMAÇÕES DE ACESSO"
echo "=========================================="
echo ""
print_info "Odoo:"
echo "  URL: http://localhost:8069"
echo "  ou através do Nginx configurado"
echo ""
print_info "Chatwoot:"
echo "  URL: http://localhost:3000"
echo "  Criar conta admin no primeiro acesso"
echo ""
print_info "Próximos passos:"
echo "  1. Acesse o Chatwoot e crie uma conta"
echo "  2. Configure as inboxes (canais) desejadas"
echo "  3. Obtenha o API Access Token em Settings > Applications"
echo "  4. No Odoo, vá em Chatwoot > Configuration > Accounts"
echo "  5. Configure a conta com URL http://chatwoot:3000 e o token"
echo "  6. Teste a conexão e sincronize os dados"
echo ""
print_info "Para verificar logs:"
echo "  docker-compose logs -f"
echo "  docker-compose -f docker-compose.chatwoot.yml logs -f"
echo ""
print_info "Para parar os serviços:"
echo "  docker-compose down"
echo "  docker-compose -f docker-compose.chatwoot.yml down"
echo ""
echo "=========================================="
