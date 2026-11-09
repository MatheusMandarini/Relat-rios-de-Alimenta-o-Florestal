# Relatório de alimentação florestal

Automação para acessar o Checklist Fácil, filtrar os registros do mês atual, exportar os dados em XLSX e salvar o relatório no destino configurado.

## Requisitos

- Python 3.10 ou superior
- Google Chrome
- Acesso ao Checklist Fácil
- Credenciais válidas para o sistema

## Instalação

No terminal, dentro da pasta do projeto:

```powershell
python -m pip install selenium python-dotenv
```

## Configuração

Crie um arquivo `.env` na raiz do projeto. Esse arquivo é local e não deve ser enviado ao GitHub:

```env
LOGIN_NAME=seu.usuario@empresa.com
LOGIN_PASSWORD=sua_senha

DOWNLOAD_DIR=downloads
EXPORT_DESTINATION_DIR=exports
HEADLESS=1
QUEUE_POLL_INTERVAL=10
QUEUE_POLL_TIMEOUT=600
DOWNLOAD_TIMEOUT=120
```

`EXPORT_DESTINATION_DIR` pode ser uma pasta local ou um caminho de rede ao qual você tenha acesso.

## Execução

```powershell
python "relatório.py"
```

O script busca os registros do primeiro dia do mês até a data atual. Quando encontra registros, ele gera o arquivo XLSX e substitui o relatório correspondente no destino configurado.

## Segurança

- Nunca publique o arquivo `.env`.
- Não coloque senhas, tokens ou caminhos corporativos diretamente no código.
- O arquivo `.env.example` local está ignorado pelo Git para evitar envios acidentais.
- Se uma senha for exposta, troque-a imediatamente.
