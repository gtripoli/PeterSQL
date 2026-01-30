from PIL import Image
import os


WORKDIR = "."
FILENAME = "../petersql_hat.png"
OUTPUT = "petersql.ico"


in_path = os.path.join(WORKDIR, FILENAME)
out_path = os.path.join(WORKDIR, OUTPUT)

# Apri immagine
img = Image.open(in_path).convert("RGBA")

# Crea un quadrato con lato = lato maggiore
size = max(img.size)
square = Image.new("RGBA", (size, size), (0, 0, 0, 0))

# Centra l’immagine nel quadrato
offset = ((size - img.width) // 2, (size - img.height) // 2)
square.paste(img, offset)

# Salva in più risoluzioni per compatibilità Windows / wxWidgets
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
square.save(out_path, format="ICO", sizes=sizes)