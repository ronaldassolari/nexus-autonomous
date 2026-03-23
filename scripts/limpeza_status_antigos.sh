#!/bin/bash

# Script de Limpeza de Arquivos de Status Antigos
# Data: 2026-03-21
# Autor: Nexus Documentation Team

echo "=========================================="
echo "LIMPEZA DE ARQUIVOS DE STATUS ANTIGOS"
echo "=========================================="
echo "Data: $(date)"
echo ""

# Diretório de arquivamento
ARQUIVADOS_DIR="./arquivados"
mkdir -p "$ARQUIVADOS_DIR"

# 1. IDENTIFICAÇÃO DE ARQUIVOS ANTIGOS
echo "1. IDENTIFICANDO ARQUIVOS ANTIGOS"
echo "----------------------------------"

# Arquivos com mais de 24 horas
find . -name "STATUS_NEXUS_*.md" -mtime +1 -type f | head -10 > /tmp/arquivos_antigos.txt
find . -name "COORDENACAO_EQUIPES_*.md" -mtime +1 -type f | head -10 >> /tmp/arquivos_antigos.txt
find . -name "HEARTBEAT_REPORT_*.md" -mtime +1 -type f | head -10 >> /tmp/arquivos_antigos.txt
find . -name "MONITORAMENTO_NEXUS_RESUMO_*.md" -mtime +1 -type f | head -10 >> /tmp/arquivos_antigos.txt
find . -name "RESUMO_STATUS_NEXUS_*.md" -mtime +1 -type f | head -10 >> /tmp/arquivos_antigos.txt

TOTAL_ARQUIVOS=$(wc -l < /tmp/arquivos_antigos.txt)
echo "Arquivos antigos identificados: $TOTAL_ARQUIVOS"
echo ""

# 2. PRÉ-VISUALIZAÇÃO
echo "2. PRÉ-VISUALIZAÇÃO DOS ARQUIVOS"
echo "---------------------------------"
if [ $TOTAL_ARQUIVOS -gt 0 ]; then
    echo "Arquivos a serem movidos para $ARQUIVADOS_DIR/:"
    cat /tmp/arquivos_antigos.txt | head -5
    if [ $TOTAL_ARQUIVOS -gt 5 ]; then
        echo "... e mais $((TOTAL_ARQUIVOS - 5)) arquivos"
    fi
else
    echo "Nenhum arquivo antigo encontrado."
fi
echo ""

# 3. CONFIRMAÇÃO
echo "3. CONFIRMAÇÃO DA AÇÃO"
echo "-----------------------"
read -p "Deseja mover estes arquivos para $ARQUIVADOS_DIR/? (s/n): " CONFIRMACAO

if [[ $CONFIRMACAO != "s" && $CONFIRMACAO != "S" ]]; then
    echo "Operação cancelada."
    exit 0
fi

# 4. EXECUÇÃO DA LIMPEZA
echo ""
echo "4. EXECUTANDO LIMPEZA"
echo "---------------------"

MOVED_COUNT=0
while IFS= read -r arquivo; do
    if [ -f "$arquivo" ]; then
        # Extrair apenas o nome do arquivo (sem caminho)
        nome_arquivo=$(basename "$arquivo")
        
        # Mover para arquivados mantendo estrutura de data
        data_arquivo=$(stat -f "%Sm" -t "%Y-%m" "$arquivo" 2>/dev/null || date +"%Y-%m")
        destino_dir="$ARQUIVADOS_DIR/$data_arquivo"
        mkdir -p "$destino_dir"
        
        if mv "$arquivo" "$destino_dir/"; then
            echo "✓ Movido: $nome_arquivo → $destino_dir/"
            MOVED_COUNT=$((MOVED_COUNT + 1))
        else
            echo "✗ Falha ao mover: $nome_arquivo"
        fi
    fi
done < /tmp/arquivos_antigos.txt

# 5. RELATÓRIO FINAL
echo ""
echo "5. RELATÓRIO FINAL"
echo "------------------"
echo "Arquivos movidos: $MOVED_COUNT de $TOTAL_ARQUIVOS"
echo ""
echo "📊 ESTATÍSTICAS DO DIRETÓRIO ATUAL:"
echo "Arquivos STATUS_NEXUS_*.md: $(find . -name "STATUS_NEXUS_*.md" -type f | wc -l)"
echo "Arquivos COORDENACAO_EQUIPES_*.md: $(find . -name "COORDENACAO_EQUIPES_*.md" -type f | wc -l)"
echo "Arquivos HEARTBEAT_REPORT_*.md: $(find . -name "HEARTBEAT_REPORT_*.md" -type f | wc -l)"
echo ""
echo "📁 CONTEÚDO DO DIRETÓRIO ARQUIVADOS:"
find "$ARQUIVADOS_DIR" -type f | wc -l | xargs echo "Total de arquivos arquivados:"
echo ""

# 6. RECOMENDAÇÕES
echo "6. RECOMENDAÇÕES"
echo "----------------"
echo "🟢 BOAS PRÁTICAS:"
echo "   1. Executar esta limpeza diariamente"
echo "   2. Manter apenas os últimos 7 dias no diretório principal"
echo "   3. Backup mensal do diretório arquivados"
echo "   4. Documentar política de retenção"
echo ""
echo "⚙️  CONFIGURAÇÃO SUGERIDA:"
echo "   Adicionar ao crontab:"
echo "   0 2 * * * /bin/bash /caminho/para/scripts/limpeza_status_antigos.sh"
echo ""

echo "=========================================="
echo "LIMPEZA CONCLUÍDA - $(date)"
echo "=========================================="

# Limpar arquivo temporário
rm -f /tmp/arquivos_antigos.txt