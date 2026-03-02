from ultralytics import YOLO
import cv2

# 1. Carrega o seu modelo treinado (o troféu do seu treinamento!)
modelo = YOLO('modelo treinado/best.pt')

# 2. Coloque aqui o nome do arquivo da imagem que você quer testar
# (Certifique-se de que a imagem está na mesma pasta que este script)
caminho_da_imagem = 'pagina_1.png' 

# 3. A IA faz a leitura da imagem
resultados = modelo(caminho_da_imagem)

# 4. Gera a imagem final com as caixas delimitadoras e os nomes das classes desenhados
imagem_resultado = resultados[0].plot()

# 5. Salva o resultado em um novo arquivo para você poder visualizar no Windows
cv2.imwrite('resultado_fluxograma.png', imagem_resultado)

print("Teste concluído! Abra o arquivo 'resultado_fluxograma.png' para ver o resultado.")