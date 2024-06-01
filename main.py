from fastapi import File, UploadFile, Request, FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import base64
from test import *
from io import BytesIO
from process import *

CLOTH_PATH = "./model/cloth_segm.pth"
HAIR_PATH = "./model/hairmattenet_v2.pth"
device = 'cpu'

cloth_net = load_seg_model(CLOTH_PATH, device=device)
hair_net = build_model(HAIR_PATH, device)

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
    img = np.array(img)

    mask = get_mask(img, hair_net)
    combined_image = alpha_image(img, mask)
    
    combined_image = Image.fromarray(combined_image)
    img_byte_arr = BytesIO()
    combined_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    base64_encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

    # return templates.TemplateResponse("display.html", {"request": request, "myImage": base64_encoded_image})
    return JSONResponse(content={"segmented_image": base64_encoded_image})
