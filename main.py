from fastapi import File, UploadFile, Request, FastAPI, Form
from fastapi.templating import Jinja2Templates
import base64
from test import *
from io import BytesIO
from process import *

PATH = "./model/cloth_segm.pth"
device = 'cpu'
net = load_seg_model(PATH, device=device)
net.eval() # 필요한가?

app = FastAPI()
templates = Jinja2Templates(directory="templates")
palette = get_palette(4)

@app.get("/")
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(request: Request, image_data: str = Form(...)):
    image_data = image_data.split(",")[1]  # Remove the 'data:image/png;base64,' part
    contents = base64.b64decode(image_data)
    
    img = Image.open(BytesIO(contents))
    img = img.convert('RGB')
    
    combined_image_data = generate_mask(img, net=net, palette=palette, device=device)
    base64_encoded_image = base64.b64encode(combined_image_data).decode("utf-8")

    return templates.TemplateResponse("display.html", {"request": request, "myImage": base64_encoded_image})
