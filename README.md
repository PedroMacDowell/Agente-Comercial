# Agente IA Local

Agente nativo para Windows para:

- buscar arquivos e documentos
- gerar proposta comercial com IA local ou API externa
- revisar antes de enviar
- enviar por email
- enviar no WhatsApp Web
- criar pasta modelo por cliente
- selecionar produtos da FutureMedia por checkbox

## O que ele faz

- Busca arquivos por nome e conteudo
- Extrai texto de `.txt`, `.md`, `.csv`, `.json`, `.html` e `.pdf`
- Gera proposta comercial mais executiva e pronta para envio
- Salva a proposta em disco
- Envia email via SMTP, se configurado
- Automatiza o WhatsApp Web via Playwright
- Valida o fluxo antes do envio

## Instalacao

1. Python 3.11+
2. Dependencias do projeto:
   ```powershell
   pip install -r requirements.txt
   ```
3. Browser do Playwright:
   ```powershell
   python -m playwright install
   ```

Se quiser usar o Edge instalado no computador, deixe `BROWSER_CHANNEL=msedge`.

Se quiser habilitar o comando `agente-ia` no terminal, rode uma vez:

```powershell
pip install -e .
```

## Configuracao

1. Copie `.env.example` para `.env`.
2. Ajuste:
   - `FILES_ROOT`: pasta onde os documentos ficam
   - `LLM_PROVIDER`: `ollama` para modelo local, `openai` para API externa
   - `OPENAI_API_KEY`: chave para gerar a proposta, se usar API externa
   - `OLLAMA_BASE_URL`: normalmente `http://localhost:11434`
   - `OLLAMA_MODEL`: modelo local, por exemplo `llama3.1`
   - `SMTP_*`: dados do servidor de email, se quiser envio automatico
   - `BROWSER_PROFILE_DIR`: pasta para manter o login do WhatsApp Web

## Estrutura recomendada por cliente

Para uso da empresa, recomendo criar uma pasta por cliente e apontar a interface para ela:

```text
clientes/
  C6 Bank/
    briefing.txt
    dados.txt
    anexos/
  Outro Cliente/
```

Quando voce cria a pasta modelo, o agente gera:

- `01_briefing`
- `02_anexos`
- `03_proposta`
- `04_envios`
- `05_referencias`
- `06_produtos`
- arquivos iniciais para orientar o time

## Como rodar

Buscar arquivos:

```powershell
python -m agente_ia.cli scan --query "cliente"
```

Gerar proposta:

```powershell
python -m agente_ia.cli proposal --recipient-name "Maria Silva" --recipient-email "maria@empresa.com" --company "C6 Bank" --product "robo-spark-venda"
```

Enviar email:

```powershell
python -m agente_ia.cli email --recipient-name "Maria Silva" --recipient-email "maria@empresa.com" --company "C6 Bank" --product "robo-spark-venda" --send
```

Enviar WhatsApp:

```powershell
python -m agente_ia.cli whatsapp --recipient-name "Maria Silva" --phone "11999999999" --company "C6 Bank" --product "robo-spark-venda" --send
```

Fluxo completo:

```powershell
python -m agente_ia.cli run --recipient-name "Maria Silva" --recipient-email "maria@empresa.com" --phone "11999999999" --company "C6 Bank" --product "robo-spark-venda" --send-email --send-whatsapp
```

Abrir a interface grafica:

```powershell
python -m agente_ia.cli gui
```

Se preferir, execute o arquivo [abrir_agente_gui.bat](abrir_agente_gui.bat) com duplo clique.

Validar o fluxo sem enviar nada:

```powershell
python -m agente_ia.cli validate --recipient-name "C6 Bank" --query "corporativo" --company "C6 Bank" --product "robo-spark-venda" --root "C:\caminho\da\pasta\do\cliente"
```

Criar a pasta modelo por cliente no terminal:

```powershell
python -m agente_ia.cli init-client --company "C6 Bank" --contact "Maria Silva" --root "C:\caminho\da\pasta\clientes" --product "robo-spark-venda"
```

## Como validar o fluxo corretamente

1. Separe a pasta do cliente dos arquivos de evento e materiais gerais.
2. Confirme que a pasta do cliente tem briefing ou documento comercial.
3. Abra a GUI e selecione a pasta correta em `Pasta do cliente`.
4. Preencha o nome da empresa.
5. Marque os produtos desejados.
6. Clique em `Criar pasta modelo` se for começar um novo cliente.
7. Clique em `Validar fluxo`.
8. Corrija qualquer aviso antes de gerar ou enviar.
9. Clique em `Buscar arquivo`.
10. Clique em `Gerar proposta`.
11. Revise o texto gerado na direita.
12. Use `Revisar` para salvar a versao final.
13. So entao envie por email ou WhatsApp.

## Ollama local

Minha recomendacao para o seu caso e usar um modelo local com Ollama se voce quer rodar tudo no computador sem depender de API.

- Fica rodando localmente no seu PC.
- Nao depende de chave externa.
- Evita custo por chamada.

Se voce ainda quiser usar API externa depois, o projeto continua pronto para isso.

### Como usar Ollama

1. Instale o Ollama no Windows.
2. Baixe um modelo, por exemplo:
   ```powershell
   ollama pull llama3.1
   ```
3. Verifique se o servidor local esta rodando em `http://localhost:11434`.
4. Defina `LLM_PROVIDER=ollama` no `.env`.

Se o Ollama nao estiver respondendo, o app cai no modo de fallback e ainda gera uma proposta simples para nao travar seu fluxo.

## Como gerar o EXE

1. Instale as dependencias de build:
   ```powershell
   pip install -r requirements-build.txt
   ```
2. Rode o arquivo [build_exe.bat](build_exe.bat).
3. O executavel vai sair em `dist\AgenteIA.exe`.

Se quiser abrir sem build, o atalho [abrir_agente_gui.bat](abrir_agente_gui.bat) continua funcionando.

## Observacoes importantes

- Para WhatsApp Web, o navegador precisa estar logado na sua conta.
- Por seguranca, o envio fica sob seu controle.
- O agente nao tenta adivinhar dados comerciais nao presentes nos documentos.

