from ultralytics import YOLO
import cv2

# Carrega o modelo que você treinou
model = YOLO('caminho/para/seu_modelo_treinado.pt')

# Faz a inferência na imagem do fluxograma médico
results = model('imagem_sincope.jpg')

# Extraindo as coordenadas das caixas detectadas
nodes_detectados = []
setas_detectadas = []

for r in results:
    for box in r.boxes:
        classe = int(box.cls[0]) # Identifica se é nó ou seta
        coordenadas = box.xyxy[0].tolist() # Pega o [x_min, y_min, x_max, y_max]
        
        if classe == 0: # Supondo que 0 seja 'node'
            nodes_detectados.append(coordenadas)
        elif classe == 1: # Supondo que 1 seja 'arrow_head'
            setas_detectadas.append(coordenadas)