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

As configurações são lidas diretamente das variáveis de ambiente do sistema. Assim, nenhuma credencial fica salva em arquivo ou no código.

No PowerShell, defina as variáveis antes de executar:

```powershell
$env:LOGIN_NAME = "seu.usuario@empresa.com"
$env:LOGIN_PASSWORD = "sua_senha"
$env:DOWNLOAD_DIR = "downloads"
$env:EXPORT_DESTINATION_DIR = "exports"
$env:HEADLESS = "1"
$env:QUEUE_POLL_INTERVAL = "10"
$env:QUEUE_POLL_TIMEOUT = "600"
$env:DOWNLOAD_TIMEOUT = "120"
```

`EXPORT_DESTINATION_DIR` pode ser uma pasta local ou um caminho de rede ao qual você tenha acesso.

## Execução

```powershell
python "relatório.py"
```

O script busca os registros do primeiro dia do mês até a data atual. Quando encontra registros, ele gera o arquivo XLSX e substitui o relatório correspondente no destino configurado.

## Segurança

- Não coloque senhas, tokens ou caminhos corporativos diretamente no código.
- Prefira variáveis de ambiente configuradas na sessão ou no gerenciador de credenciais do sistema.
- Se uma senha for exposta, troque-a imediatamente.
