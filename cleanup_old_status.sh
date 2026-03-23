#!/bin/bash

# Script para limpar arquivos de status antigos
# Mantém apenas os 10 arquivos mais recentes de cada tipo

echo "=== LIMPEZA DE ARQUIVOS DE STATUS ANTIGOS ==="
echo "Data: $(date)"
echo ""

# Função para limpar arquivos por padrão
cleanup_files() {
    local pattern="$1"
    local keep_count="${2:-10}"
    
    echo "Processando: $pattern"
    echo "Mantendo os $keep_count arquivos mais recentes"
    
    # Conta arquivos
    file_count=$(ls -1 $pattern 2>/dev/null | wc -l)
    echo "Total de arquivos encontrados: $file_count"
    
    if [ $file_count -gt $keep_count ]; then
        # Lista arquivos para remover (todos exceto os $keep_count mais recentes)
        files_to_remove=$(ls -1t $pattern | tail -n +$((keep_count + 1)))
        
        if [ -n "$files_to_remove" ]; then
            echo "Arquivos para remover:"
            echo "$files_to_remove"
            echo ""
            
            # Remove arquivos
            echo "$files_to_remove" | xargs rm -f
            echo "Removidos $(echo "$files_to_remove" | wc -l) arquivos antigos"
        else
            echo "Nenhum arquivo para remover"
        fi
    else
        echo "Nenhum arquivo para remover (mantendo todos $file_count arquivos)"
    fi
    
    echo ""
}

# Limpar arquivos de status
cleanup_files "STATUS_NEXUS_*.md" 10
cleanup_files "RESUMO_STATUS_NEXUS_*.md" 10
cleanup_files "COORDENACAO_EQUIPES_*.md" 10
cleanup_files "MONITORAMENTO_NEXUS_RESUMO_*.md" 10
cleanup_files "HEARTBEAT_REPORT_*.md" 10

echo "=== LIMPEZA CONCLUÍDA ==="
echo "Arquivos restantes:"
echo "STATUS_NEXUS: $(ls -1 STATUS_NEXUS_*.md 2>/dev/null | wc -l)"
echo "RESUMO_STATUS_NEXUS: $(ls -1 RESUMO_STATUS_NEXUS_*.md 2>/dev/null | wc -l)"
echo "COORDENACAO_EQUIPES: $(ls -1 COORDENACAO_EQUIPES_*.md 2>/dev/null | wc -l)"
echo "MONITORAMENTO_NEXUS_RESUMO: $(ls -1 MONITORAMENTO_NEXUS_RESUMO_*.md 2>/dev/null | wc -l)"
echo "HEARTBEAT_REPORT: $(ls -1 HEARTBEAT_REPORT_*.md 2>/dev/null | wc -l)"