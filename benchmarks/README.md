# Benchmarks

## Escopo atual

`benchmark_light.py` mede somente as partes que já podem ser executadas nesta
máquina sem instalar componentes pesados:

- decodificação de PNG pelo pipeline;
- Canny e transformada de Hough para segmentos;
- combinação das duas etapas.

Não inclui inferência YOLO, OCR Tesseract, entrada PDF ou renderização Graphviz.
Essas etapas estão indisponíveis no ambiente atual e devem ser medidas depois que
os pesos e executáveis forem fornecidos.

## Ambiente observado em 20 de agosto de 2026

- CPU: AMD Ryzen 5 5600G with Radeon Graphics, 12 processadores lógicos;
- RAM instalada: 16.423.751.680 bytes (aproximadamente 15,30 GiB);
- RAM livre na captura: 3.508.652 KiB (aproximadamente 3,35 GiB);
- GPU dedicada: NVIDIA GeForce GTX 750 Ti, 2 GiB;
- GPU integrada: AMD Radeon Graphics;
- sistema: Windows 11 Pro 64 bits, versão 10.0.26200;
- Python: 3.13.7.

Por causa da pouca memória livre e da GPU antiga, os benchmarks devem usar uma
thread e lotes unitários. Treinamento não faz parte desta medição.

## Protocolo

1. Fechar aplicações pesadas antes da medição final do artigo.
2. Registrar temperatura/energia do sistema quando possível.
3. Fazer duas iterações de aquecimento.
4. Fazer dez repetições por imagem.
5. Reportar mediana e percentil 95, não apenas a média.
6. Fixar versões, resolução, `imgsz`, dispositivo e número de threads.
7. Separar tempo de carregamento, YOLO, OCR, topologia e renderização.

Resultados em `results/light_benchmark.csv` são preliminares enquanto as etapas
de ML e OCR permanecerem indisponíveis.
