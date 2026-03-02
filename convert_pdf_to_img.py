#converter pdf para imagem
from pdf2image import convert_from_path
# Caminho para o arquivo PDF
pdf_path = 'pdf teste/pdf teste.pdf'
# Converter o PDF para uma lista de imagens (uma imagem por página)
images = convert_from_path(pdf_path)
# Salvar cada imagem em um arquivo separado
for i, image in enumerate(images):
    image.save(f'pagina_{i + 1}.png', 'PNG')
print("PDF convertido para imagens com sucesso!")
