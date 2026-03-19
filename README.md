````md
# Eye of Thundera

Eye of Thundera é um laboratório prático de observabilidade e monitoramento criado para estudar conceitos de DevOps e SRE de forma aplicada.

O projeto simula uma aplicação que pode apresentar falhas controladas, lentidão e degradação de saúde, enquanto um serviço separado monitora esse comportamento, detecta incidentes automaticamente e envia alertas em tempo real para o Telegram.

## Objetivo

A proposta deste projeto é demonstrar, na prática, como funciona um fluxo básico de monitoramento operacional, cobrindo pontos importantes como:

- health checks automáticos
- detecção de incidentes
- classificação de severidade
- alertas externos
- exposição de métricas para Prometheus
- visualização com Grafana
- execução de múltiplos serviços com Docker Compose

## Arquitetura do projeto

O projeto foi dividido em serviços com responsabilidades separadas:

- `app`: aplicação monitorada
- `ops-api`: serviço responsável pelo monitoramento, detecção de incidentes e alertas
- `prometheus`: coleta métricas da aplicação
- `grafana`: visualiza métricas coletadas pelo Prometheus

### Fluxo simplificado

1. A aplicação principal expõe endpoints como `/health` e `/metrics`
2. O `ops-api` verifica periodicamente a saúde da aplicação
3. Quando detecta falha, abre um incidente automaticamente
4. O incidente é classificado por severidade
5. Um alerta é enviado para o Telegram
6. Quando o serviço volta ao normal, o incidente é resolvido e uma nova mensagem é enviada
7. O Prometheus coleta métricas da aplicação e o Grafana pode exibi-las em dashboards

## Estrutura do projeto

```bash
eye-of-thundera/
├── app/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── ops-api/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── ops-web/
├── prometheus/
│   └── prometheus.yml
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
````

## Tecnologias utilizadas

* Python
* FastAPI
* Uvicorn
* Docker
* Docker Compose
* Prometheus
* Grafana
* Telegram Bot API

## Funcionalidades implementadas

### Aplicação monitorada

A aplicação principal foi construída para servir como alvo do monitoramento. Ela permite simular comportamentos comuns em ambientes reais.

#### Endpoints principais da aplicação

* `GET /` → resposta simples indicando que a aplicação está no ar
* `GET /health` → health check principal
* `GET /ready` → readiness check
* `GET /status` → estado interno atual da aplicação
* `GET /slow` → simula resposta lenta
* `GET /fail` → simula erro HTTP 500
* `GET /random-fail` → simula falhas aleatórias
* `GET /load` → simula carga artificial
* `POST /toggle-health` → alterna entre saudável e não saudável
* `POST /toggle-slow` → ativa/desativa modo lento
* `POST /toggle-error` → ativa/desativa modo de erro global
* `POST /reset` → restaura o estado inicial
* `GET /metrics` → expõe métricas no formato Prometheus

### Monitoramento automático

O `ops-api` faz verificações periódicas no endpoint `/health` da aplicação monitorada.

Com base na resposta, o serviço classifica o estado em:

* `healthy`
* `unhealthy`
* `down`

### Gestão de incidentes

Quando ocorre uma transição de estado saudável para estado degradado, o monitor abre automaticamente um incidente.

Quando o serviço volta ao normal, esse incidente é resolvido automaticamente.

### Severidade

Os incidentes também recebem severidade para diferenciar o impacto operacional:

* `warning` para estados `unhealthy`
* `critical` para estados `down`
* `resolved` quando ocorre recuperação

### Alertas no Telegram

Ao abrir ou resolver um incidente, o sistema envia uma notificação para o Telegram usando um bot configurado por variáveis de ambiente.

### Métricas com Prometheus

A aplicação expõe métricas de requisição, erros e latência por meio do endpoint `/metrics`.

### Visualização com Grafana

O Grafana foi incluído para possibilitar a visualização das métricas coletadas pelo Prometheus.

## Como executar o projeto

### Pré-requisitos

Antes de rodar o projeto, você precisa ter instalado:

* Docker
* Docker Compose

Também é necessário ter um bot do Telegram criado no `@BotFather` caso queira testar os alertas.

## Configuração do Telegram

No serviço `ops-api`, o envio de alertas depende de duas variáveis de ambiente:

* `TELEGRAM_BOT_TOKEN`
* `TELEGRAM_CHAT_ID`

### Exemplo de configuração no `docker-compose.yml`

```yaml
ops-api:
  build: ./ops-api
  ports:
    - "8001:8001"
  depends_on:
    - app
  environment:
    TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
    TELEGRAM_CHAT_ID: "${TELEGRAM_CHAT_ID}"
```

### Exemplo de `.env.example`

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

## Subindo os serviços

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Se quiser rodar em background:

```bash
docker compose up --build -d
```

## Acessos

Depois de subir os containers, os serviços ficam disponíveis em:

* aplicação monitorada: `http://localhost:8000`
* monitor (`ops-api`): `http://localhost:8001`
* Prometheus: `http://localhost:9090`
* Grafana: `http://localhost:3000`

## Como testar

### 1. Verificar se a aplicação está saudável

```bash
curl http://localhost:8000/health
```

### 2. Consultar o status atual no monitor

```bash
curl http://localhost:8001/status
```

### 3. Simular uma falha de health check

```bash
curl -X POST http://localhost:8000/toggle-health
```

Aguarde alguns segundos e consulte novamente:

```bash
curl http://localhost:8001/status
```

### 4. Consultar incidente ativo

```bash
curl http://localhost:8001/incident
```

### 5. Consultar histórico de incidentes

```bash
curl http://localhost:8001/incidents
```

### 6. Restaurar o serviço

```bash
curl -X POST http://localhost:8000/reset
```

Após alguns segundos, o incidente deve ser resolvido automaticamente e uma nova mensagem deve ser enviada ao Telegram.

## Observação para Windows PowerShell

No PowerShell, o comando `curl` pode se comportar de forma diferente. Nesse caso, você pode usar:

```powershell
irm -Method POST -Uri http://localhost:8000/toggle-health
```

e para consultar status:

```powershell
irm http://localhost:8001/status
```

## Exemplos de uso

Alguns cenários que podem ser simulados com o projeto:

* aplicação saudável e estável
* health check falhando
* resposta lenta
* erro HTTP 500
* falhas aleatórias
* recuperação automática após reset

Esses cenários ajudam a visualizar como um sistema de monitoramento reage a eventos reais de forma simples e prática.

## Estado atual do projeto

Atualmente o projeto já possui:

* aplicação monitorada com falhas controladas
* monitoramento automático
* abertura e resolução automática de incidentes
* classificação de severidade
* alertas no Telegram
* métricas expostas para Prometheus
* integração com Grafana
* orquestração com Docker Compose

## Limitações atuais

Este projeto foi construído como laboratório de estudo e MVP técnico. Por isso, algumas limitações ainda existem:

* os incidentes são armazenados apenas em memória
* não há banco de dados persistente
* apenas um serviço é monitorado por vez
* ainda não há autenticação
* o frontend `ops-web` ainda não foi implementado

## Próximos passos

Algumas evoluções planejadas para o projeto:

* persistência de incidentes em banco de dados
* suporte a múltiplos serviços monitorados
* dashboard web próprio
* autenticação e autorização
* mais métricas e regras de incidentes
* monitoramento de recursos do host
* execução de ações automatizadas com segurança

## Motivação do projeto

Este projeto foi desenvolvido com foco em estudo prático e portfólio, buscando consolidar conhecimentos em:

* observabilidade
* monitoramento de serviços
* incident management
* integração entre sistemas
* automação operacional
* fundamentos de DevOps e SRE

## Autor

Desenvolvido por João Artur como projeto prático de estudos em DevOps/SRE.

```
