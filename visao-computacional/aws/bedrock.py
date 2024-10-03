import cv2
import numpy as np

def detect_edges(image_path, output_path):
    # Carrega a imagem
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"Erro ao carregar a imagem: {image_path}")
        return

    # Converte a imagem para escala de cinza
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aplica o filtro de Canny para detectar bordas
    edges = cv2.Canny(gray_image, 100, 200)

    # Salva a imagem resultante
    cv2.imwrite(output_path, edges)
    print(f"Bordas detectadas salvas em: {output_path}")

if __name__ == "__main__":
    input_image_path = 'caminho/para/sua/imagem.jpg'
    output_image_path = 'caminho/para/salvar/bordas.jpg'
    detect_edges(input_image_path, output_image_path)