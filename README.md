# YOLO Counter

Contagem de objetos em vídeo por **cruzamento de linha**, com detecção **YOLO** (Ultralytics) e rastreamento multiobjeto (**ByteTrack** ou **BoT-SORT**). Funciona com arquivos de vídeo, câmeras RTSP/HTTP e webcam, pela linha de comando ou por uma interface web.

![Testes](https://github.com/ka-lucas/YOLO-counter/actions/workflows/tests.yml/badge.svg)

## Como funciona

```
quadro ──► YOLO (detecção) ──► rastreador (ID estável por objeto) ──► contador de linha ──► eventos + totais
```

1. **Detecção:** o YOLO encontra os objetos das classes escolhidas em cada quadro.
2. **Rastreamento:** o ByteTrack associa as detecções entre quadros e dá a cada objeto um identificador estável.
3. **Contagem:** para cada objeto, o contador guarda a posição anterior de um ponto de referência (o centro da base da caixa, por padrão) e verifica se o deslocamento até a posição atual **cruza o segmento da linha** (teste de interseção de segmentos com produto vetorial). O sentido do cruzamento define entrada ou saída.
4. **Robustez:** cada objeto conta no máximo uma vez por sentido, então um objeto parado sobre a linha, oscilando por causa do ruído da caixa, não gera contagens repetidas. Pontos exatamente sobre a linha não substituem a posição anterior, para o cruzamento não se perder.

**Sentido:** com a linha desenhada da esquerda para a direita, quem **sobe** na imagem conta como **entrada** e quem **desce**, como **saída**. Para inverter, troque a ordem dos pontos.

## Instalação

Requer Python 3.10 ou mais recente.

```bash
git clone https://github.com/ka-lucas/YOLO-counter.git
cd YOLO-counter
pip install -e ".[web]"
```

Os pesos oficiais `yolo11n.pt` são baixados automaticamente na primeira execução. Para usar GPU, instale antes a versão do PyTorch com CUDA.

## Uso

### Linha de comando

```bash
# Contar pessoas e carros num vídeo, gravando o vídeo anotado e um relatório JSON
yolo-counter count video.mp4 --classes person car --line 0,360,1280,360 \
    --output anotado.mp4 --report relatorio.json

# Câmera RTSP, mostrando a janela ao vivo
yolo-counter count "rtsp://usuario:senha@host:554/stream" --classes person --show

# Webcam
yolo-counter count 0 --show
```

| Opção | Descrição |
|---|---|
| `--line x1,y1,x2,y2` | linha de contagem em pixels (padrão: horizontal no meio do quadro) |
| `--classes` | classes do modelo a contar (padrão: todas) |
| `--model` | pesos YOLO (padrão: `yolo11n.pt`; aceita outros modelos, inclusive treinados por você) |
| `--tracker` | `bytetrack.yaml` (padrão) ou `botsort.yaml` |
| `--anchor` | ponto da caixa usado na contagem: `bottom` (padrão) ou `center` |
| `--conf` | confiança mínima da detecção (padrão: 0,35) |

O relatório JSON traz os totais por sentido e por classe e a lista de eventos: quadro, tempo no vídeo, identificador do objeto, classe e sentido.

### Interface web

```bash
yolo-counter serve        # http://127.0.0.1:8000
```

Envie um vídeo ou informe a URL de uma câmera, defina a linha e as classes e acompanhe o vídeo anotado ao vivo, com o placar e os últimos eventos.

API:

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/jobs/upload` | inicia a contagem a partir de um arquivo enviado |
| POST | `/api/jobs/stream` | inicia a contagem a partir de uma URL ou webcam |
| GET | `/api/jobs/current` | status, totais e eventos |
| GET | `/api/jobs/current/video` | vídeo anotado ao vivo (MJPEG) |
| POST | `/api/jobs/current/stop` | interrompe a contagem |

### Docker

```bash
docker build -t yolo-counter .
docker run --rm -p 8000:8000 yolo-counter
```

## Avaliação da contagem

Para medir a qualidade em vídeos reais, anote a contagem correta de cada vídeo e compare com a prevista:

```bash
yolo-counter evaluate previsto.json anotado.json
```

Os dois arquivos têm o formato `{"nome_do_video": {"in": 12, "out": 9}}`. O comando calcula o erro absoluto médio das entradas e das saídas e o erro relativo médio do total.

`scripts/make_synthetic_video.py` gera um vídeo de teste com duas pessoas (recortadas da imagem de exemplo da Ultralytics) cruzando a linha em sentidos opostos. Nele, o pipeline conta 1 entrada e 1 saída, como esperado, a cerca de 10 quadros por segundo em CPU com o `yolo11n`.

## Testes

```bash
pip install -e ".[dev]"
pytest
```

Os testes cobrem a geometria do cruzamento, o contador (sentidos, oscilação sobre a linha, ponto sobre a linha, contagem por classe), a linha de comando, a avaliação e a API web. Eles rodam sem PyTorch, porque o pipeline é substituído por um falso nos testes da API. O GitHub Actions roda os testes a cada push.

## Estrutura

```
src/yolocounter/
├── geometry.py   # linha e teste de cruzamento de segmentos
├── counter.py    # contador por linha a partir de objetos rastreados
├── pipeline.py   # vídeo → YOLO + rastreador → contador → quadro anotado
├── draw.py       # desenho da linha, das caixas e do placar
├── evaluate.py   # erro das contagens contra anotações
├── cli.py        # yolo-counter count | evaluate | serve
├── web.py        # API FastAPI + vídeo ao vivo
└── static/index.html
tests/            # pytest
scripts/          # vídeo sintético de teste
```

## Licença

O código deste repositório está sob a licença MIT — veja [LICENSE](LICENSE). Ele depende do pacote `ultralytics` e dos seus pesos oficiais, que são distribuídos sob a licença AGPL-3.0: ao redistribuir o projeto junto com eles, os termos da AGPL-3.0 também se aplicam.
