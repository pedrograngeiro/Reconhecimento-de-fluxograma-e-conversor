from ultralytics import YOLO

# 1. Em vez de baixar o modelo zerado, apontamos para o último "checkpoint" salvo antes de travar
# (Certifique-se de que o caminho da pasta runs está correto de acordo com o seu projeto)
modelo = YOLO('yolov8n.pt') 

# 2. Continua o treinamento com limitadores rígidos de memória
resultados = modelo.train(
    data='flow-chart/data.yaml', 
    epochs=100,      # Como você já fez 33, faltam apenas 17 para completar a meta de 50
    imgsz=640,      
    device='cpu',
    
    # --- NOVAS TRAVAS ANTI-KILLED ---
    batch=16,        # Reduz a quantidade de imagens carregadas na RAM por vez (o padrão é 16).
    workers=0       # Desativa o multiprocessamento de leitura. No WSL, processos paralelos duplicam o uso da RAM. Isso força a usar apenas 1 núcleo para leitura, economizando muita memória.
)